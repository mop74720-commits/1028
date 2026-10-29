"""Independent energy/units/Maxwell/quadrature/reachability checks for CoilROM."""
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np
import torch
from coil_rom import CoilROM
from coil_control import CurrentAllocator
from coil_field import basis

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'stage4/audit/program'))
from physical_audit_checks import analytic_field_gradient


def main():
    start=time.perf_counter();out=ROOT/'stage5/results/coil';out.mkdir(parents=True,exist_ok=True)
    m=CoilROM();z=m.initial_state();Q=z[:m.n];current=m.bias_currents
    qt=m.tensor(Q);it=m.tensor(current)
    centers,moments=m.magnetic_geometry_tensor(qt)
    coords=centers.detach().numpy();mu=moments.detach().numpy()
    b,g=analytic_field_gradient(coords,current,m.coil_config)
    dgeo=torch.func.jacrev(lambda x:torch.stack(m.magnetic_geometry_tensor(x)))(qt).detach().numpy()
    dx,dmu=dgeo
    virtual=(np.einsum('pak,pa->k',dmu,b)+np.einsum('pa,pab,pbk->k',mu,g,dx))/m.rom.E0
    port=m.current_port(Q);trueforce=port@current
    fds=[]
    for eps in (2e-6,1e-6):
        values=[]
        for j in range(m.n):
            d=eps*np.eye(m.n)[j]
            vp=float(m.coil_potential_tensor(qt+m.tensor(d),it))
            vm=float(m.coil_potential_tensor(qt-m.tensor(d),it))
            values.append(-(vp-vm)/(2*eps))
        fds.append(np.array(values))
    # Absolute units, turns, orientation and radius tested against exact loop axis.
    cfg=m.coil_config;normal=np.asarray(cfg['normals'][0]);center=np.asarray(cfg['centers_m'][0]);a=cfg['radius_m']
    axial_z=np.array([0.,.02,.075]);points=center+axial_z[:,None]*normal
    axial=m.field_basis_tensor(m.tensor(points)).numpy()[:,:,0]
    expected=(2*np.pi*1e-7*cfg['turns']*a*a/(a*a+axial_z**2)**1.5)[:,None]*normal
    axiserror=float(np.linalg.norm(axial-expected)/np.linalg.norm(expected))
    btorch,gtorch=m.field_basis_tensor(centers,gradient=True)
    energy_port=dict(total_moment_A_m2=float(m.rom.segment_moment.sum()),
        full_force_Q=trueforce.tolist(),virtual_work_difference=float(np.linalg.norm(virtual-trueforce)),
        energy_central_differences=[dict(eps=eps,difference=float(np.linalg.norm(fd-trueforce))) for eps,fd in zip((2e-6,1e-6),fds)],
        full_vs_affine_force_relative=float(np.linalg.norm(trueforce-m.current_port(Q,model='affine')@current)/np.linalg.norm(trueforce)),
        analytic_B_difference_T=float(np.linalg.norm(btorch.numpy()@current-b)),
        analytic_G_difference_T_per_m=float(np.linalg.norm(gtorch.numpy()@current-g)),
        independent_stage2_basis_difference_T_per_A=float(np.linalg.norm(btorch.numpy()-basis(coords,m.coil_config))),
        maxwell_divergence_T_per_m=float(np.max(abs(np.trace(g,axis1=1,axis2=2)))),
        maxwell_curl_T_per_m=float(np.linalg.norm(g-g.transpose(0,2,1))),
        axial_closed_form_relative_error=axiserror)
    assert energy_port['virtual_work_difference']<1e-11
    assert max(e['difference'] for e in energy_port['energy_central_differences'])<2e-8
    assert axiserror<1e-12
    assert energy_port['maxwell_divergence_T_per_m']<1e-12
    assert energy_port['maxwell_curl_T_per_m']<1e-12
    arrays={'initial_state':z,'bias_currents_A':current,'full_force_Q':trueforce,'full_virtual_work_Q':virtual}
    wire=[]
    for n in (128,256,512):
        mm=m if n==256 else CoilROM(wire_points=n)
        bb,gg=mm.field_basis_tensor(centers,gradient=True)
        ff=mm.current_port(Q)@current
        wire.append(dict(wire_points=n,field_difference_T=float(np.linalg.norm(bb.numpy()@current-b)),
            gradient_difference_T_per_m=float(np.linalg.norm(gg.numpy()@current-g)),force_difference_Q=float(np.linalg.norm(ff-trueforce))))
    rawq=m.rom.Sq.numpy()@Q;spatial=[]
    for n in (20,40,80):
        mm=m if n==20 else CoilROM(elements=n)
        Qn=np.linalg.solve(mm.rom.Sq.numpy(),rawq)
        transform=m.rom.Sq.numpy().T@np.linalg.inv(mm.rom.Sq.numpy().T)
        full=transform@mm.current_port(Qn)@current
        affine=transform@mm.current_port(Qn,model='affine')@current
        singular=np.linalg.svd(transform@mm.current_port(Qn),compute_uv=False)
        arrays[f'force_common_Q_elements{n}']=full
        spatial.append(dict(elements=n,magnetic_points=len(mm.active),
            common_force_Q=full.tolist(),difference_from_20=float(np.linalg.norm(full-trueforce)),
            full_vs_affine_relative=float(np.linalg.norm(full-affine)/np.linalg.norm(full)),
            rank_rcond=1e-8,rank=int(np.sum(singular>1e-8*singular[0])),singular_values=singular.tolist()))
    spatial[-1]['difference_40_to_80']=float(np.linalg.norm(arrays['force_common_Q_elements80']-arrays['force_common_Q_elements40']))
    allocation=[];allocator=CurrentAllocator(m)
    for scale in (1.,10.,100.):
        desired=.2*scale*z[m.n:]
        allocated,audit=allocator.allocate_force(Q,desired,current,1e-4)
        samples=m.physical_samples(Q,allocated)
        audit.update(momentum_scale=scale,maximum_actual_B_T=samples['maximum_B_T'],maximum_actual_G_T_per_m=samples['maximum_G_T_per_m'])
        allocation.append(audit)
        assert audit['orthogonal_unreachable_residual']<=audit['constrained_force_residual']+1e-10
    direction=np.cos(np.arange(2*m.n)+.3);direction/=np.linalg.norm(direction)
    jac=m.feedback_jacobian(z);eps=2e-6
    fd=(m.feedback_field(z+eps*direction)-m.feedback_field(z-eps*direction))/(2*eps)
    x=m.tensor(z);i_feedback=m.collocated_current_tensor(x)
    wrong=m.J_tensor@torch.func.grad(lambda a:m.hamiltonian_tensor(a,m.collocated_current_tensor(a)))(x)
    actual=m.feedback_field_tensor(x)
    grad_bias=torch.func.grad(lambda a:m.hamiltonian_tensor(a,m.bias_currents_tensor))(x)
    y=m.current_port_tensor(x[:m.n]).T@grad_bias[m.n:]
    power=float(grad_bias@(actual-m.field_tensor(x,m.bias_currents_tensor)))
    feedback=dict(full_jacobian_direction_FD_difference=float(np.linalg.norm(jac@direction-fd)),
        incorrectly_differentiated_feedback_H_field_error=float(torch.linalg.vector_norm(wrong-actual)),
        magnetic_increment_power=power,power_identity_error=abs(power+m.collocated_gain*float(y@y)),
        unbounded_requested_currents_A=i_feedback.numpy().tolist(),
        fixed_input_vs_feedback_jacobian_difference=float(np.linalg.norm(jac-m.jacobian(z,i_feedback.numpy()),2)))
    assert feedback['full_jacobian_direction_FD_difference']<2e-6
    assert feedback['power_identity_error']<1e-12
    assert feedback['incorrectly_differentiated_feedback_H_field_error']>1e-6
    report=dict(status='actually_executed_pass',model=m.metadata(),energy_and_units=energy_port,
        wire_quadrature=wire,same_physical_q_spatial_quadrature=spatial,
        force_space_allocation=allocation,smooth_feedback=feedback,
        elapsed_seconds=time.perf_counter()-start,
        tolerances=dict(virtual_work_abs=1e-11,energy_FD_abs=2e-8,axis_relative=1e-12,maxwell_abs=1e-12,feedback_J_direction_abs=2e-6,power_abs=1e-12,allocation_feasibility=1e-9),
        environment=dict(python=sys.version,numpy=np.__version__,torch=torch.__version__),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('coil_rom.py'),Path(__file__).with_name('coil_control.py')]},
        limitation='Independent local energy/derivative tests and common-q spatial diagnostics; no global domain/ROM-to-PDE error/thermal or physiology certification.')
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(out/'validation_arrays.npz',**arrays)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
