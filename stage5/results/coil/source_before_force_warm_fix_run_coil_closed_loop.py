"""Actually integrate full-coil closed loops, with constrained continuous currents.

Three cases share initial state, gain, time grid, total bias, material, limits,
and tolerance: full controller/full plant; affine/affine; affine/full. Current
targets are recomputed from each actual state. Every RK stage evaluates its
plant force at current geometry. No saved affine trajectory is replayed.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys
import time
import numpy as np
import torch
from coil_rom import CoilROM
from coil_control import CurrentAllocator,ramp_current

ROOT=Path(__file__).resolve().parents[2]


def integrate(model,plant,controller,duration,updates,substeps,gamma):
    start_clock=time.perf_counter()
    z=model.initial_state();current=model.bias_currents.copy()
    allocator=CurrentAllocator(model)
    interval=duration/updates;dt=interval/substeps
    states=[z.copy()];currents=[current.copy()];times=[0.]
    allocations=[];stages=[];node_rows=[]
    work=0.;magnetic_work=0.;mechanical_work=0.
    initial_h=model.hamiltonian(z,current,model=plant)
    initial_mech=model.hamiltonian(z,np.zeros_like(current),model=plant)
    for k in range(updates):
        begin=k*interval;end=(k+1)*interval
        if controller=='damping_compensation':
            target,report=allocator.allocate_force(z[:model.n],gamma*z[model.n:],current,interval/model.rom.omega0)
        else:
            requested=model.collocated_current_tensor(model.tensor(z),model=controller).detach().numpy()
            target,report=allocator.allocate(z[:model.n],requested,current,interval/model.rom.omega0)
        report.update(update=k,tau=begin,plant=plant,controller=controller)
        allocations.append(report)
        start_current=current.copy();slope=(target-start_current)/interval
        def rhs(state,tau):
            i=ramp_current(start_current,target,tau,begin,end)
            f=model.field(state,i,gamma=gamma,model=plant)
            with torch.no_grad():
                features=model.magnetic_features_tensor(model.tensor(state[:model.n]),model=plant).numpy()
            rate=float(features@slope-gamma*f[:model.n]@state[model.n:])
            # Magnetic mechanical work, independent of the parametric dV/di term.
            magnetic_force=-torch.func.grad(lambda Q:model.coil_potential_tensor(Q,model.tensor(i),model=plant))(model.tensor(state[:model.n])).detach().numpy()
            pmag=float(f[:model.n]@magnetic_force)
            pmech=pmag-gamma*float(f[:model.n]@state[model.n:])
            samples=model.physical_samples(state[:model.n],i)
            stages.append(dict(time_tau=tau,maximum_B_T=samples['maximum_B_T'],maximum_G_T_per_m=samples['maximum_G_T_per_m'],
                minimum_wire_distance_m=samples['minimum_distance_exact_wire_m'],maximum_current_A=float(np.max(abs(i))),
                mechanical_magnetic_power_W=pmag*model.rom.E0*model.rom.omega0))
            return f,rate,pmag,pmech
        for j in range(substeps):
            tau=begin+j*dt
            a=rhs(z,tau);b=rhs(z+dt*a[0]/2,tau+dt/2)
            c=rhs(z+dt*b[0]/2,tau+dt/2);d=rhs(z+dt*c[0],tau+dt)
            z=z+dt*(a[0]+2*b[0]+2*c[0]+d[0])/6
            weights=np.array([1,2,2,1])/6
            work+=dt*float(weights@np.array([a[1],b[1],c[1],d[1]]))
            magnetic_work+=dt*float(weights@np.array([a[2],b[2],c[2],d[2]]))
            mechanical_work+=dt*float(weights@np.array([a[3],b[3],c[3],d[3]]))
            current=ramp_current(start_current,target,tau+dt,begin,end)
            if not np.isfinite(z).all():
                raise FloatingPointError('Nonfinite full-coil closed-loop state')
            states.append(z.copy());currents.append(current.copy());times.append(tau+dt)
            node_rows.append(dict(time_tau=tau+dt,time_s=(tau+dt)/model.rom.omega0,
                H_total=model.hamiltonian(z,current,model=plant),H_mechanical=model.hamiltonian(z,np.zeros_like(current),model=plant),
                input_work=work,mechanical_work=mechanical_work,magnetic_work=magnetic_work,
                maximum_current_A=float(np.max(abs(current)))))
        print(f'{plant}/{controller} substeps={substeps}: update {k+1}/{updates}',flush=True)
    full_h=model.hamiltonian(z,current,model=plant)
    mech_h=model.hamiltonian(z,np.zeros_like(current),model=plant)
    maximum_B=max(v['maximum_B_T'] for v in stages)
    maximum_G=max(v['maximum_G_T_per_m'] for v in stages)
    summary=dict(plant=plant,controller=controller,actually_integrated=True,
        duration_tau=duration,duration_s=duration/model.rom.omega0,updates=updates,
        steps=updates*substeps,substeps_per_control_interval=substeps,dt_tau=dt,
        gamma_dimensionless=gamma,gain_dimensionless=model.collocated_gain,
        state_initial=states[0].tolist(),state_final=z.tolist(),
        total_energy_change=full_h-initial_h,total_input_work=work,
        total_power_balance_residual=full_h-initial_h-work,
        mechanical_energy_change=mech_h-initial_mech,mechanical_net_work=mechanical_work,
        mechanical_power_balance_residual=mech_h-initial_mech-mechanical_work,
        magnetic_mechanical_work=magnetic_work,
        max_current_A=max(v['maximum_current_A'] for v in stages),
        max_continuous_ramp_slew_A_s=max(v['maximum_planned_slew_A_s'] for v in allocations),
        max_actual_magnet_point_B_T=maximum_B,max_actual_magnet_point_G_T_per_m=maximum_G,
        max_normalized_sampled_field_violation=max(0.,maximum_B/.005-1,maximum_G/.03-1),
        min_actual_magnet_point_wire_distance_m=min(v['minimum_wire_distance_m'] for v in stages),
        max_allocation_current_residual_A=max(v['current_request_distance_A'] for v in allocations),
        max_allocation_force_residual=max(v['generalized_force_allocation_residual'] for v in allocations),
        elapsed_seconds=time.perf_counter()-start_clock,
        scope='Fields checked at every RK stage and actual magnetic quadrature point; no continuous-space or between-stage field bound. Currents are continuous piecewise linear, so their amplitude/rate bounds hold throughout every ramp.')
    if summary['max_current_A']>2.+1e-10 or summary['max_continuous_ramp_slew_A_s']>20.+1e-8:
        raise AssertionError('Continuous current bounds violated')
    return summary,np.asarray(times),np.asarray(states),np.asarray(currents),allocations,stages,node_rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--duration',type=float,default=.004)
    parser.add_argument('--updates',type=int,default=8)
    parser.add_argument('--gamma',type=float,default=.2)
    parser.add_argument('--output',type=Path,default=ROOT/'stage5/results/coil')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    model=CoilROM();arrays={};records=[]
    for plant,controller in [('full','full'),('affine','affine'),('full','affine'),('full','damping_compensation')]:
        pair=[]
        for substeps in (1,2):
            run,t,z,i,allocations,stages,node_rows=integrate(model,plant,controller,args.duration,args.updates,substeps,args.gamma)
            name=f'{plant}_plant_{controller}_control_substeps{substeps}'
            arrays[name+'_tau']=t;arrays[name+'_state']=z;arrays[name+'_current_A']=i
            (args.output/(name+'_details.json')).write_text(json.dumps(dict(allocations=allocations,RK_stage_checks=stages,nodes=node_rows),indent=2)+'\n')
            pair.append(run);records.append(run)
            print(json.dumps(run),flush=True)
        fine=arrays[f'{plant}_plant_{controller}_control_substeps2_state']
        coarse=arrays[f'{plant}_plant_{controller}_control_substeps1_state']
        pair[1]['coarse_fine_max_state_difference']=float(np.max(np.linalg.norm(fine[::2]-coarse,axis=1)))
    baseline=arrays['full_plant_full_control_substeps2_state']
    comparisons={}
    for key in ('affine_plant_affine_control_substeps2_state','full_plant_affine_control_substeps2_state'):
        comparisons[key]=float(np.max(np.linalg.norm(arrays[key]-baseline,axis=1)))
    np.savez_compressed(args.output/'closed_loop_trajectories.npz',**arrays)
    report=dict(status='actually_executed',model=model.metadata(),runs=records,
        max_state_difference_from_full_full=comparisons,
        fair_comparison='Identical material, initial z/current, gain, interval, controller updates, current limits and sampled full-field constraints. Each actual trajectory closes its own state feedback. Affine/full cross-case separates controller-model error from plant approximation.',
        power_convention='Total H=T+Ve+Vcoil, dH/dtau=(dVcoil/di)·di/dtau−gamma H_P·P. Mechanical H=T+Ve uses H_P·Gcoil i−gamma H_P·P. Both work balances are integrated with same RK stage weights.',
        structure='Continuous-ramp sampled constrained feedback is not declared exact symplectic or passive. Smooth unconstrained collocated law has a separate power identity.',
        limitation='Short smooth Kirchhoff ROM study, no fluid/contact/FSI, no full continuous workspace certificate, no long-time tracking or KAM claim.',
        environment=dict(python=sys.version,numpy=np.__version__,torch=torch.__version__),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('coil_rom.py'),Path(__file__).with_name('coil_control.py')]})
    (args.output/'closed_loop_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    columns=['plant','controller','steps','duration_tau','elapsed_seconds','total_power_balance_residual','mechanical_power_balance_residual','max_current_A','max_continuous_ramp_slew_A_s','max_actual_magnet_point_B_T','max_actual_magnet_point_G_T_per_m','coarse_fine_max_state_difference']
    with (args.output/'closed_loop_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows({key:r.get(key,'') for key in columns} for r in records)
    print('ACTUAL coil closed-loop runs complete',flush=True)


if __name__=='__main__':
    main()
