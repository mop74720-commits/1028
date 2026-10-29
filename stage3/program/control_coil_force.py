"""Independently differentiate full Biot-Savart magnetic energy on the ROM.

This measures the approximation made by the 8-field affine magnetic interface.
It does not reuse the affine G to construct the full coil-force reference.
"""
from pathlib import Path
import json
import sys
import time
import hashlib
import numpy as np
import torch
from control_experiments import ROMBridge, MagneticControl, basis, make_array, field_limits, unpack

ROOT=Path(__file__).resolve().parents[1]


def coil_potential(bridge,Q,currents,config):
    with torch.no_grad():
        rawq=bridge.rom.Sq@torch.tensor(Q)
        _,_,_,frames,centers=bridge.rom.mechanics(rawq[None,:],return_geometry=True)
    centers=centers[0].numpy();directions=frames[0].numpy()[:,:,2]
    moments=bridge.rom.segment_moment.numpy()
    active=moments>0
    field=np.einsum('pij,j->pi',basis(centers[active],config),currents)
    return -float(np.sum(moments[active,None]*directions[active]*field))/bridge.rom.E0


def numerical_force(bridge,Q,currents,config,eps):
    columns=[]
    for j in range(bridge.n):
        dq=eps*np.eye(bridge.n)[j]
        columns.append(-(coil_potential(bridge,Q+dq,currents,config)-coil_potential(bridge,Q-dq,currents,config))/(2*eps))
    return np.array(columns)


def virtual_work_audit(bridge,Q,currents,config,local_input,full_fd):
    active=bridge.rom.segment_moment.numpy()>0
    active_idx=torch.tensor(np.flatnonzero(active))
    def geometry(x):
        rawq=bridge.rom.Sq@x
        _,_,_,frames,centers=bridge.rom.mechanics(rawq[None,:],return_geometry=True)
        return torch.stack((centers[0,active_idx],frames[0,active_idx,:,2]*bridge.rom.segment_moment[active_idx,None]))
    x=torch.tensor(Q);geo=geometry(x).detach().numpy()
    dg=torch.autograd.functional.jacobian(geometry,x,vectorize=True).detach().numpy()
    centers,mu=geo;dc,dm=dg
    def b_at(points):return np.einsum('pij,j->pi',basis(points,config),currents)
    bfull=b_at(centers);derivatives=[]
    for eps in (1e-5,5e-6):
        derivatives.append(np.stack([(b_at(centers+eps*np.eye(3)[j])-b_at(centers-eps*np.eye(3)[j]))/(2*eps) for j in range(3)],axis=2))
    gradfull=derivatives[-1]
    b0,grad=unpack(local_input);baffine=b0+(centers-np.array(config['origin_m']))@grad.T
    torque_difference=np.einsum('pak,pa->k',dm,bfull-baffine)/bridge.rom.E0
    force_difference=np.einsum('pa,pab,pbk->k',mu,gradfull-grad[None,:,:],dc)/bridge.rom.E0
    forcefull=(np.einsum('pak,pa->k',dm,bfull)+np.einsum('pa,pab,pbk->k',mu,gradfull,dc))/bridge.rom.E0
    forceaffine=(np.einsum('pak,pa->k',dm,baffine)+np.einsum('pa,ab,pbk->k',mu,grad,dc))/bridge.rom.E0
    origin=np.array(config['origin_m'])[None,:];eps=5e-6
    origin_grad=np.stack([(b_at(origin+eps*np.eye(3)[j])-b_at(origin-eps*np.eye(3)[j]))/(2*eps) for j in range(3)],axis=2)[0]
    return dict(total_vs_increment='actual_local_input includes bias; both energies and G@actual_local_input here use total fields',
       origin_center_field_reconstruction_error_T=float(np.linalg.norm(b_at(origin)[0]-b0)),
       origin_gradient_reconstruction_error_T_per_m=float(np.linalg.norm(origin_grad-grad)),
       full_gradient_refinement_difference_T_per_m=float(np.linalg.norm(derivatives[0]-derivatives[1])),
       distal_gradient_minus_origin_affine_T_per_m=float(np.linalg.norm(gradfull-grad[None,:,:])),
       full_force_virtual_work_vs_energy_gradient_difference=float(np.linalg.norm(forcefull-full_fd)),
       affine_virtual_work_vs_Gm_difference=float(np.linalg.norm(forceaffine-bridge.magnetic_map(Q)@local_input)),
       field_torque_contribution_difference_norm=float(np.linalg.norm(torque_difference)),
       gradient_force_contribution_difference_norm=float(np.linalg.norm(force_difference)),
       additive_difference_closure=float(np.linalg.norm(forcefull-forceaffine-torque_difference-force_difference)))

def main():
    start=time.perf_counter();out=ROOT/'results/control'
    results=json.loads((out/'control_results.json').read_text())
    trajectories=np.load(out/'trajectories.npz')
    bridge=ROMBridge();config=results['coil_allocation']['config'];records=[]
    for index in (0,len(results['coil_allocation']['records'])-1):
        record=results['coil_allocation']['records'][index]
        z=trajectories['bounded_compensation_state'][index+1];Q=z[:bridge.n]
        currents=np.array(record['currents_A']);u=np.array(record['actual_local_input'])
        full=[numerical_force(bridge,Q,currents,config,eps) for eps in (2e-6,1e-6)]
        affine=bridge.magnetic_map(Q)@u
        records.append(dict(time_s=record['time_s'],steps=[2e-6,1e-6],
           independent_virtual_work=virtual_work_audit(bridge,Q,currents,config,u,full[-1]),
           full_coil_generalized_force=full[-1].tolist(),affine_generalized_force=affine.tolist(),
           finite_difference_refinement_difference=float(np.linalg.norm(full[0]-full[1])),
           full_minus_affine_norm=float(np.linalg.norm(full[-1]-affine)),
           full_minus_affine_relative=float(np.linalg.norm(full[-1]-affine)/max(np.linalg.norm(full[-1]),1e-30))))
    control=MagneticControl(bridge);stress=[]
    for scale in (1.,10.,100.):
        z=bridge.initial_state();z[bridge.n:]*=scale
        g=bridge.magnetic_map(z[:bridge.n]);desired=control.gamma*z[bridge.n:]
        raw,_=control.command(z,'projected_damping_compensation',g=g)
        limited,details=control.command(z,'bounded_compensation',g=g)
        stress.append(dict(momentum_scale=scale,radial_scale=details['radial_scale'],
           unbounded_limits=field_limits(bridge,raw),bounded_limits=field_limits(bridge,limited),
           desired_force_norm=float(np.linalg.norm(desired)),
           bounded_force_residual=float(np.linalg.norm(g@limited-desired))))
    report=dict(status='executed',constraint_stress=stress,method='centered finite differences of -sum_i mu_i (R_i e3) dot B_BiotSavart(r_i,I) / E0; full actual 20-cell 12-DOF geometry, currents fixed during differentiation',
      records=records,elapsed_seconds=time.perf_counter()-start,
      source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      limitation='Pointwise force audit only; full coil-force trajectories and bounds over continuous space remain unrun.')
    (out/'full_coil_force_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
