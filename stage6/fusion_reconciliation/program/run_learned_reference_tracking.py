"""Small independently identified S6-T01 experiment; no old results overwritten."""
from pathlib import Path
import json
import argparse
import platform
import sys
import time
import numpy as np
import scipy
import torch
from scipy.integrate import solve_ivp
from learned_reference_tracking import (CoilROM, CurrentAllocator, LearnedReference,
    tracking_request, identity_diagnostics, velocity_tensor, ROOT)
from coil_control import ramp_current

OUT = ROOT/'stage6/fusion_reconciliation/results/history/S6_T01'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",default="S6_T01")
    args=parser.parse_args()
    OUT=ROOT/"stage6/fusion_reconciliation/results/history"/args.run_id
    if OUT.exists():
        raise FileExistsError('Use a new experiment ID before rerunning frozen S6_T01')
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    model = CoilROM()
    ref = LearnedReference(model)
    allocator = CurrentAllocator(model)
    n = model.n
    zr0 = model.initial_state(amplitude=.01)
    z0 = zr0.copy(); z0[:n] += .0005/np.sqrt(model.rom.nu.numpy())
    gamma = .05
    horizon = .002; dt = .0005
    grid = np.arange(5)*dt
    refsol = solve_ivp(lambda t,z:ref.field(z),(0,horizon),zr0,method='DOP853',rtol=2e-12,atol=2e-14,dense_output=True)
    if not refsol.success: raise RuntimeError(refsol.message)
    v0 = velocity_tensor(model,model.tensor(z0)).detach().numpy()
    vr0,_ = ref.kinematics(zr0)
    e0=z0[:n]-zr0[:n]; de0=v0-vr0
    states=[z0.copy()]; rows=[]; schedule=[]; current=model.bias_currents.copy(); z=z0.copy()
    for j,(begin,end) in enumerate(zip(grid[:-1],grid[1:])):
        zr = refsol.sol(begin)
        desired,kin = tracking_request(model,ref,z,zr,gamma=gamma)
        target,allocation = allocator.allocate_force(z[:n],desired,current,(end-begin)/model.rom.omega0)
        diag_start = identity_diagnostics(model,ref,z,zr,current,gamma=gamma)
        diag_target = identity_diagnostics(model,ref,z,zr,target,gamma=gamma)
        schedule.append((current.copy(),target.copy(),float(begin),float(end)))
        sol = solve_ivp(lambda t,y:model.field(y,ramp_current(current,target,t,begin,end),gamma),
                        (begin,end),z,method='DOP853',rtol=2e-10,atol=2e-12,dense_output=True)
        if not sol.success:raise RuntimeError(sol.message)
        checks=[]
        for t in np.linspace(begin,end,5):
            zz=sol.sol(t);ii=ramp_current(current,target,t,begin,end)
            physical=model.physical_samples(zz[:n],ii)
            grad = torch.func.grad(lambda a:model.hamiltonian_tensor(a,model.bias_currents_tensor))(model.tensor(zz)).detach().numpy()
            actual=model.field(zz,ii,gamma)
            vel=actual[:n]
            port=model.current_port(zz[:n]); power=vel@port@(ii-model.bias_currents)-gamma*vel@zz[n:]
            checks.append(dict(tau=float(t),B=physical['maximum_B_T'],G=physical['maximum_G_T_per_m'],
                power_balance_residual=float(grad@actual-power),power_J_s=float(model.rom.E0*model.rom.omega0*power)))
        z=sol.y[:,-1];states.append(z.copy());current=target
        rows.append(dict(step=j,begin_tau=float(begin),end_tau=float(end),allocation=allocation,
            desired_norm=float(np.linalg.norm(desired)),start_current_identity=diag_start,target_current_identity=diag_target,
            moving_point_checks=checks,nfev=int(sol.nfev)))
        print(f'S6-T01 actual full-coil step {j+1}/4 rank={allocation["rank"]} residual={allocation["constrained_force_residual"]:.6g}',flush=True)
    states=np.asarray(states);references=refsol.sol(grid).T
    # Same predetermined learned reference, ideal all-generalized-force oracle.
    # This is an exact error-equation benchmark, never an executable magnetic control.
    ideal_error=np.exp(-grid[:,None])*((1+grid[:,None])*e0+grid[:,None]*de0)
    oracle_q=references[:,:n]+ideal_error
    # Reintegrate the identical stored current ramps at tighter solver tolerances.
    zcheck=z0.copy(); checkstates=[zcheck.copy()]
    for old,target,begin,end in schedule:
        chk=solve_ivp(lambda t,y:model.field(y,ramp_current(old,target,t,begin,end),gamma),
            (begin,end),zcheck,method='DOP853',rtol=2e-12,atol=2e-14)
        if not chk.success:raise RuntimeError(chk.message)
        zcheck=chk.y[:,-1];checkstates.append(zcheck.copy())
    # Independently approximated reference demonstrates reference error separately.
    yr=zr0.copy();rk=[yr.copy()]
    for begin,end in zip(grid[:-1],grid[1:]):
        for unused in range(8):
            h=(end-begin)/8;k1=ref.field(yr);k2=ref.field(yr+h*k1/2);k3=ref.field(yr+h*k2/2);k4=ref.field(yr+h*k3)
            yr=yr+h*(k1+2*k2+2*k3+k4)/6
        rk.append(yr.copy())
    rk=np.asarray(rk);checks=[x for row in rows for x in row['moving_point_checks']]
    record=dict(experiment='S6-T01',status='independently actually run',reference=ref.metadata,
        plant=model.metadata(),gamma=gamma,initial_plant=z0.tolist(),initial_reference=zr0.tolist(),
        gains=dict(kp=1.,kd=2.),horizon_tau=horizon,horizon_seconds=horizon/model.rom.omega0,
        allocation_interval_tau=dt,solver=dict(method='DOP853',rtol=2e-10,atol=2e-12,check_rtol=2e-12,check_atol=2e-14),
        constraints=dict(current_A=model.coil_config['current_bound_A'],slew_A_s=model.coil_config['slew_bound_A_s'],field_T=.005,gradient_T_per_m=.03),
        summary=dict(max_identity_residual=max(r['target_current_identity']['identity_absolute_residual'] for r in rows),
            max_constraint_violation=max(r['allocation']['constraint_violation'] for r in rows),
            max_current_A=float(np.max(np.abs(np.asarray([s[:2] for s in schedule])))),
            max_planned_slew_A_s=max(r['allocation']['maximum_planned_slew_A_s'] for r in rows),
            max_sampled_field_T=max(x['B'] for x in checks),max_sampled_gradient_T_per_m=max(x['G'] for x in checks),
            max_sampled_power_residual=max(abs(x['power_balance_residual']) for x in checks),
            same_schedule_tolerance_difference=float(np.max(np.linalg.norm(states-np.asarray(checkstates),axis=1))),
            reference_RK4_vs_DOP853_difference=float(np.max(np.linalg.norm(rk-references,axis=1))),
            final_position_tracking_error=float(np.linalg.norm(states[-1,:n]-references[-1,:n])),
            final_same_reference_ideal_force_oracle_error=float(np.linalg.norm(ideal_error[-1])),
            final_actual_vs_ideal_force_oracle=float(np.linalg.norm(states[-1,:n]-oracle_q[-1])),
            max_reference_normalized_state=float(np.max(abs(references*ref.scale.numpy())))),
        limitations=['short-window proof-of-connection, not long-horizon stability or superiority',
            'sampled ramp allocation causes extra hold/lag error; decision-state identity is not a zero residual during a ramp',
            'ideal-force oracle is only an unattainable benchmark; all simulated plant inputs are allocated full coil currents',
            'learned reference targets Hideal while physical plant uses Hcoil; no shared learned-error bound is assumed',
            'smooth ROM excludes blood/contact closure; final 3D vascular Cosserat target is unchanged',
            'no symplectic/KAM claim for damping and sampled constrained control'],steps=rows,
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,torch=torch.__version__,platform=platform.platform(),torch_threads=torch.get_num_threads()),
        elapsed_seconds=time.perf_counter()-started)
    np.savez(OUT/'trajectories.npz',tau=grid,plant=states,reference=references,oracle_position=oracle_q,reference_rk4=rk,
        check_plant=np.asarray(checkstates),currents_start=np.asarray([s[0] for s in schedule]),currents_target=np.asarray([s[1] for s in schedule]))
    (OUT/'results.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record['summary'],indent=2),flush=True)

if __name__=='__main__':main()
