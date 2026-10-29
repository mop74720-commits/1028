"""Actual magnetic-port control on the delivered 12-DOF variable-mass ROM.

All fields are increments above the inherited axial bias. The affine Maxwell
interface and engineered coil realization are distinguished explicitly. This is
smooth-ROM research, not a replacement for blood/contact Cosserat validation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import torch

from rom_bridge import ROMBridge
SOURCE = Path(__file__).resolve().parents[1] / 'source_inputs/starter/stage2/program'
sys.path.insert(0, str(SOURCE))
from coil_field import CoilAllocator, basis, local_mapping, make_array, unpack

ROOT = Path(__file__).resolve().parents[1]
POLICIES = ('uncontrolled', 'projected_damping_compensation',
            'constant_magnetic_potential', 'collocated_damping', 'bounded_compensation')


def field_limits(bridge, increment):
    total = bridge.bias.numpy() + np.asarray(increment)
    b, grad = unpack(total)
    config = bridge.rom.config['magnet']
    return dict(total_center_field_T=float(np.linalg.norm(b)),
                gradient_frobenius_T_per_m=float(np.linalg.norm(grad)),
                affine_workspace_upper_bound_T=float(np.linalg.norm(b)+config['workspace_radius_m']*np.linalg.norm(grad,2)),
                divergence=float(np.trace(grad)),curl_defect=float(np.linalg.norm(grad-grad.T)))


def bounded_increment(bridge, increment):
    """Radial projection along the bias-to-command segment onto convex bounds."""
    config=bridge.rom.config['magnet']
    def feasible(factor):
        v=field_limits(bridge, factor*increment)
        return (v['affine_workspace_upper_bound_T']<=config['B_workspace_bound_T'] and
                v['gradient_frobenius_T_per_m']<=config['gradient_frobenius_bound_T_per_m'])
    if feasible(1.): return np.asarray(increment).copy(),1.
    lo,hi=0.,1.
    for _ in range(60):
        mid=(lo+hi)/2
        if feasible(mid):lo=mid
        else:hi=mid
    return lo*np.asarray(increment),lo


class MagneticControl:
    def __init__(self, bridge, gamma=.2, rcond=1e-8):
        self.bridge=bridge;self.gamma=gamma;self.rcond=rcond
        self.port_scale=np.array([.001]*3+[.01]*5)
        g=bridge.magnetic_map(bridge.initial_state()[:bridge.n])
        self.collocated_gain=gamma/np.linalg.norm(g*self.port_scale,2)**2

    def command(self, z, policy, *, g=None, velocity=None):
        n=self.bridge.n
        if policy=='uncontrolled':return np.zeros(8),dict(radial_scale=1.)
        if policy=='constant_magnetic_potential':
            return np.array([.0001,-.00006,0.,0.,0.,0.,0.,0.]),dict(radial_scale=1.)
        if g is None:g=self.bridge.magnetic_map(z[:n])
        if policy in ('projected_damping_compensation','bounded_compensation'):
            u=self.port_scale*(np.linalg.pinv(g*self.port_scale,rcond=self.rcond)@(self.gamma*z[n:]))
        elif policy=='collocated_damping':
            if velocity is None:velocity=self.bridge.field(z)[:n]
            u=-self.collocated_gain*self.port_scale*((g*self.port_scale).T@velocity)
        else:raise ValueError(policy)
        factor=1.
        if policy=='bounded_compensation':u,factor=bounded_increment(self.bridge,u)
        return u,dict(radial_scale=factor)

    def evaluate(self,z,policy):
        base=self.bridge.field(z,gamma=self.gamma)
        if policy=='uncontrolled':return base,np.zeros(8),np.zeros(self.bridge.n)
        if policy=='constant_magnetic_potential':
            u,_=self.command(z,policy)
            controlled=self.bridge.field(z,gamma=self.gamma,u=u)
            return controlled,u,controlled[self.bridge.n:]-base[self.bridge.n:]
        g=self.bridge.magnetic_map(z[:self.bridge.n])
        u,_=self.command(z,policy,g=g,velocity=base[:self.bridge.n])
        force=g@u
        base[self.bridge.n:]+=force
        return base,u,force


def point_audit(bridge,control,z):
    start=time.perf_counter();n=bridge.n
    g=bridge.magnetic_map(z[:n]);scaled=g*control.port_scale
    s=np.linalg.svd(scaled,compute_uv=False)
    velocity=bridge.field(z)[:n];desired=control.gamma*z[n:]
    records=[]
    for policy in POLICIES:
        u,extra=control.command(z,policy,g=g,velocity=velocity)
        force=g@u
        records.append(dict(policy=policy,input_increment=u.tolist(),generalized_force=force.tolist(),
                    target_damping_force=desired.tolist(),damping_cancellation_residual=float(np.linalg.norm(force-desired)),
                    input_power_dimensionless=float(velocity@force),
                    input_power_W=float(bridge.rom.E0*bridge.rom.omega0*(velocity@force)),
                    total_Hdot_dimensionless=float(velocity@(force-desired)),
                    limits=field_limits(bridge,u),**extra))
    # Actual feedback derivatives, including G(Q) and u(Q,P), with a centered
    # step refinement. Do not replace these by fixed-input Hamiltonian tangents.
    jacobian_records=[]
    direction=np.cos(np.arange(2*n)+.1);direction/=np.linalg.norm(direction)
    # Full control Jacobian; derivative of constant magnetic force is a Hessian.
    for policy in POLICIES[1:]:
        derivatives=[]
        for eps in (2e-6,1e-6):
            cols=[]
            for j in range(2*n):
                d=np.eye(2*n)[j]*eps
                def force(zz):
                    gg=bridge.magnetic_map(zz[:n]);v=bridge.field(zz)[:n]
                    uu,_=control.command(zz,policy,g=gg,velocity=v)
                    return np.r_[np.zeros(n),gg@uu]
                cols.append((force(z+d)-force(z-d))/(2*eps))
            derivatives.append(np.column_stack(cols))
        dg=derivatives[-1]
        jacobian_records.append(dict(policy=policy,
             original_conformal_form_feedback_defect_spectral=float(np.linalg.norm(dg.T@bridge.K0+bridge.K0@dg,2)),
             feedback_jacobian_refinement_difference=float(np.linalg.norm(derivatives[0]-dg,2))))
    return dict(state=z.tolist(),scaled_port_singular_values=s.tolist(),
       input_scaling_SI=control.port_scale.tolist(),rank_at_rcond=int(np.sum(s>control.rcond*s[0])),
       rank_rcond=control.rcond,scaled_condition=float(s[0]/s[-1]),
       sensitivity=[dict(rcond=r,rank=int(np.sum(s>r*s[0])),
          unreachable_norm=float(np.linalg.norm(scaled@np.linalg.pinv(scaled,rcond=r)@desired-desired))) for r in (1e-6,1e-8,1e-10)],
       policies=records,feedback_jacobians=jacobian_records,elapsed_seconds=time.perf_counter()-start)


def integrate(bridge,control,policy,duration,steps):
    """Independent RK4 control comparison; no symplecticity claim for RK4."""
    dt=duration/steps;z=bridge.initial_state();states=[z.copy()];powers=[];inputs=[]
    start=time.perf_counter();work=0.
    for _ in range(steps):
        k1,u1,f1=control.evaluate(z,policy)
        k2,u2,f2=control.evaluate(z+dt*k1/2,policy)
        k3,u3,f3=control.evaluate(z+dt*k2/2,policy)
        k4,u4,f4=control.evaluate(z+dt*k3,policy)
        rates=[]
        for zz,kk,ff in ((z,k1,f1),(z+dt*k1/2,k2,f2),(z+dt*k2/2,k3,f3),(z+dt*k3,k4,f4)):
            rates.append(float(kk[:bridge.n]@(ff-control.gamma*zz[bridge.n:])))
        work+=dt*(rates[0]+2*rates[1]+2*rates[2]+rates[3])/6
        powers.append(rates[0]);inputs.append(u1)
        z=z+dt*(k1+2*k2+2*k3+k4)/6
        if not np.isfinite(z).all():raise FloatingPointError('nonfinite controlled trajectory')
        states.append(z.copy())
    elapsed=time.perf_counter()-start
    energy_change=bridge.hamiltonian(z)-bridge.hamiltonian(states[0])
    return dict(policy=policy,steps=steps,dt=dt,duration_tau=duration,
      duration_seconds=duration/bridge.rom.omega0,seconds=elapsed,
      final_state=z.tolist(),energy_change_dimensionless=energy_change,
      integrated_net_power_dimensionless=work,power_balance_residual=energy_change-work,
      maximum_requested_input_norm=float(np.max(np.linalg.norm(inputs,axis=1)))),np.asarray(states),np.asarray(inputs)


def coil_audit(bridge,control,states,times):
    cfg=make_array();a,defects=local_mapping(cfg);allocator=CoilAllocator(cfg)
    # Pre-energized axial-bias equilibrium at t=0; initialization is not a
    # zero-to-bias slew experiment. All subsequent increments obey slew bounds.
    allocator.allocate(bridge.bias.numpy(),time_s=0.)
    records=[];currents=[allocator.currents.copy()]
    for z,tau in zip(states[1:],times[1:]):
        g=bridge.magnetic_map(z[:bridge.n]);u,_=control.command(z,'bounded_compensation',g=g)
        requested=bridge.bias.numpy()+u
        actual,current=allocator.allocate(requested,time_s=float(tau/bridge.rom.omega0))
        rawq=bridge.rom.Sq@torch.tensor(z[:bridge.n])
        _,_,_,frames,centers=bridge.rom.mechanics(rawq[None,:],return_geometry=True)
        centers=centers[0].detach().numpy();frames=frames[0].detach().numpy()
        magnetic=bridge.rom.segment_moment.numpy()>0
        points=centers[magnetic]
        btrue=np.einsum('pij,j->pi',basis(points,cfg),current)
        b0,grad=unpack(actual);baffine=b0+(points-np.array(cfg['origin_m']))@grad.T
        records.append(dict(time_s=float(tau/bridge.rom.omega0),requested_input=requested.tolist(),actual_local_input=actual.tolist(),
            currents_A=current.tolist(),max_actual_field_at_magnetic_centers_T=float(np.max(np.linalg.norm(btrue,axis=1))),
            full_Biot_Savart_minus_affine_max_T=float(np.max(np.linalg.norm(btrue-baffine,axis=1))),
            affine_modal_force_target_residual=float(np.linalg.norm(g@(actual-bridge.bias.numpy())-control.gamma*z[bridge.n:])),
            affine_limits=field_limits(bridge,actual-bridge.bias.numpy())))
        currents.append(current.copy())
    currents=np.array(currents)
    return dict(config=cfg,local_mapping_singular_values=np.linalg.svd(a/allocator.scale[:,None],compute_uv=False).tolist(),
      local_mapping_rank=int(np.linalg.matrix_rank(a/allocator.scale[:,None])),maxwell_finite_difference=defects,
      initialization='Pre-energized bias allocation; recorded slew starts after t=0',
      maximum_current_A=float(np.abs(currents).max()),
      maximum_sample_difference_slew_A_s=float(np.max(np.abs(np.diff(currents,axis=0)/np.diff(times/bridge.rom.omega0)[:,None]))),
      records=records,
      limitation='Allocation replay on the bounded-field ROM trajectory; not a coil-driven rod trajectory. Affine modal forces differ from full spatial Biot-Savart forces. No continuous-current interpolation, thermal or hardware calibration claim.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'results/control')
    parser.add_argument('--duration',type=float,default=.004);parser.add_argument('--steps',type=int,default=8)
    parser.add_argument('--skip-jacobians',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(1);bridge=ROMBridge();control=MagneticControl(bridge)
    # Flag exists only to allow a quick independent test; full delivery uses all.
    if args.skip_jacobians: raise ValueError('Full control audit requires feedback Jacobians')
    audit=point_audit(bridge,control,bridge.initial_state())
    (args.output/'point_audit.json').write_text(json.dumps(audit,indent=2))
    summaries=[];arrays={}
    for policy in POLICIES:
        coarse,states,inputs=integrate(bridge,control,policy,args.duration,args.steps)
        fine,fs,fi=integrate(bridge,control,policy,args.duration,2*args.steps)
        fine['coarse_to_fine_maximum_state_difference']=float(np.max(np.linalg.norm(states-fs[::2],axis=1)))
        fine['coarse_run']=coarse
        summaries.append(fine);arrays[policy+'_state']=fs;arrays[policy+'_input']=fi
        print(json.dumps(fine),flush=True)
    times=np.linspace(0,args.duration,2*args.steps+1);arrays['time_tau']=times
    coils=coil_audit(bridge,control,arrays['bounded_compensation_state'],times)
    np.savez_compressed(args.output/'trajectories.npz',**arrays)
    result=dict(status='executed',model=bridge.metadata(),gamma_dimensionless=control.gamma,
       initial_state=bridge.initial_state().tolist(),controller_parameters=dict(pseudoinverse_rcond=control.rcond,
          SI_port_scale=control.port_scale.tolist(),collocated_gain=control.collocated_gain),
       trajectories=summaries,coil_allocation=coils,
       learning_residual_compensation=dict(status='missing_data',
          required_files=['stage2/results/learning/complex_seed1025.pt','stage2/results/learning/analytic_coefficients.npy','stage2/results/learning/learning_data.npz','stage2/results/learning/learning_summary.json'],
          statement='No delivered trained weights or NPZ learning datasets found. No frozen learned compensation was executed or fabricated.'),
       scope='Actual 12-coordinate variable-mass smooth Kirchhoff ROM; synthetic proportional damping. Blood, contact and microgravity forcing remain in existing full Cosserat model, not closed into this ROM.',
       source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output/'control_results.json').write_text(json.dumps(result,indent=2))
    with (args.output/'control_summary.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['policy','steps','dt','duration_tau','seconds','energy_change_dimensionless','power_balance_residual','coarse_to_fine_maximum_state_difference'])
        writer.writeheader()
        for row in summaries:writer.writerow({k:row[k] for k in writer.fieldnames})
    print('Control experiments and coil replay completed',flush=True)

if __name__=='__main__':main()
