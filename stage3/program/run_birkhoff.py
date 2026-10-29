"""Execute local Birkhoff vs original dynamics with separate error budgets."""
from pathlib import Path
import argparse
import csv
import json
import time
import numpy as np
import torch
from scipy.integrate import solve_ivp
from birkhoff_rom import LocalBirkhoffROM
from rom_integrators import solve_chord, TOLERANCE

OUT=Path(__file__).resolve().parents[1]/'results/birkhoff'

def chart_jacobian(model,t,y):
    w=torch.tensor(np.r_[np.ones(model.n),model.weights(t)])
    x=torch.tensor(y,requires_grad=True)
    hess=torch.autograd.functional.hessian(lambda v:model.gauge_hamiltonian(v/w,t),x,vectorize=True)
    return model.J@hess.detach().numpy()

def integrate(model,z0,T,h,chart=True):
    state=model.chart(z0,0.) if chart else z0.copy()
    times=np.arange(round(T/h)+1)*h; trajectory=[z0.copy()]; records=[]
    started=time.perf_counter()
    for k,t in enumerate(times[:-1]):
        field=(lambda y:model.chart_field(t+h/2,y)) if chart else model.original_field
        jac=chart_jacobian(model,t+h/2,state) if chart else model.original_jacobian(state)
        eye=np.eye(len(state));old=state.copy()
        new,stats=solve_chord(lambda y:y-old-h*field((y+old)/2),old+h*field(old),eye-h*jac/2)
        if k==0:
            midjac=chart_jacobian(model,t+h/2,(old+new)/2) if chart else model.original_jacobian((old+new)/2)
            tangent=np.linalg.solve(eye-h*midjac/2,eye+h*midjac/2)
            if chart:
                tangent=np.linalg.solve(model.chart_jacobian(t+h),tangent@model.chart_jacobian(t))
            stats['first_step_Ka_defect_2']=float(np.linalg.norm(tangent.T@model.K(t+h)@tangent-model.K(t),2))
            stats['first_step_implicit_min_singular']=float(np.linalg.svd(eye-h*midjac/2,compute_uv=False)[-1])
        state=new
        trajectory.append(model.inverse_chart(new,t+h) if chart else new.copy());records.append(stats)
    return np.asarray(trajectory), dict(seconds=time.perf_counter()-started,steps=len(records),
        residual_inf=max(r['increment_residual_inf'] for r in records),
        max_solver_condition=max(r['solver_matrix_condition'] for r in records),
        first_step=records[0],structure_sampling='first step; ideal implicit tangent')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--duration',type=float,default=.0005)
    args=parser.parse_args();T=args.duration
    OUT.mkdir(parents=True,exist_ok=True); started=time.perf_counter()
    m=LocalBirkhoffROM();z0=m.bridge.initial_state();steps=[T/4,T/8,T/16]
    report=dict(status='running',duration_tau=T,duration_seconds=T/m.bridge.rom.omega0,
        initial_state=z0.tolist(),rates=m.rates.tolist(),model=m.bridge.metadata(),
        solver_tolerance=TOLERANCE,diagnostics=[],rows=[],references=[],
        scope='First-order one-form from one fixed origin on the full nonlinear 12-DOF ROM; synthetic nonproportional canonical drag. No blood/contact closure or exact flow oracle.')
    destination=OUT/f'results_T{T:g}.json'
    save=lambda:destination.write_text(json.dumps(report,indent=2)+'\n')
    for t in [T/8,T/4,T/2,T]:
        d=m.diagnostics(z0,t,differentiate_oneform=t==T/2);report['diagnostics'].append(d);save()
        print('diagnostic',json.dumps(d),flush=True)
    refs={}
    for name,field in [('original',lambda t,z:m.original_field(z)),('represented',m.approximate_field)]:
        sols=[]
        for rtol,atol,max_step in [(2e-10,2e-12,T/8),(5e-12,5e-14,T/16)]:
            before=time.perf_counter()
            sol=solve_ivp(field,(0,T),z0,method='DOP853',rtol=rtol,atol=atol,max_step=max_step,dense_output=True)
            if not sol.success: raise RuntimeError(sol.message)
            row=dict(field=name,rtol=rtol,atol=atol,max_step=max_step,nfev=sol.nfev,seconds=time.perf_counter()-before)
            report['references'].append(row);sols.append(sol);save();print('reference',row,flush=True)
        grid=np.linspace(0,T,129)
        report[name+'_reference_refinement_max']=float(np.max(np.linalg.norm(sols[0].sol(grid)-sols[1].sol(grid),axis=0)))
        refs[name]=sols[1]
    grid=np.linspace(0,T,129)
    report['represented_vs_original_reference_gap']=float(np.max(np.linalg.norm(refs['represented'].sol(grid)-refs['original'].sol(grid),axis=0)))
    traces={'reference_times':grid,'original_reference':refs['original'].sol(grid).T,'represented_reference':refs['represented'].sol(grid).T}
    for method,chart in [('original_midpoint',False),('birkhoff_chart_midpoint',True)]:
        previous=None
        for h in steps:
            states,stats=integrate(m,z0,T,h,chart);times=np.arange(len(states))*h
            eo=float(np.max(np.linalg.norm(states-refs['original'].sol(times).T,axis=1)))
            ea=float(np.max(np.linalg.norm(states-refs['represented'].sol(times).T,axis=1)))
            target_error=ea if chart else eo
            row=dict(method=method,h=h,error_to_original_max=eo,error_to_represented_max=ea,
                observed_order_to_integrated_field=None if previous is None else float(np.log2(previous/target_error)),**stats)
            # This power balance is for the ORIGINAL field, even for f_a. It
            # intentionally exposes model discrepancy rather than renaming it.
            work=0.;power_defects=[]
            H0=m.bridge.hamiltonian(z0)
            for i in range(len(states)-1):
                mid=(states[i]+states[i+1])/2
                velocity=m.bridge.field(mid)[:m.n]
                work-=h*float(velocity@(m.rates*mid[m.n:]))
                power_defects.append(abs(m.bridge.hamiltonian(states[i+1])-H0-work))
            row['original_power_balance_residual_max']=max(power_defects)
            report['rows'].append(row);previous=target_error
            traces[f'{method}_h{h:g}']=states
            save();print('integration',json.dumps(row),flush=True)
    report['status']='completed';report['elapsed_seconds']=time.perf_counter()-started;save()
    np.savez_compressed(OUT/f'trajectories_T{T:g}.npz',**traces)
    with (OUT/f'metrics_T{T:g}.csv').open('w') as f:
        keys=['method','h','error_to_original_max','error_to_represented_max','observed_order_to_integrated_field','residual_inf','seconds','original_power_balance_residual_max']
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows(report['rows'])

if __name__=='__main__': main()
