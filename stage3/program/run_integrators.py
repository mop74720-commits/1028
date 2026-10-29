"""Same-model 24-dimensional midpoint/weighted/Central4 experiments."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import time
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
import numpy as np
from scipy.integrate import solve_ivp
from rom_bridge import ROMBridge
from rom_integrators import integrate, TOLERANCE

ROOT = Path(__file__).resolve().parents[1]


def references(model, z0, duration, gamma):
    records = []
    solutions = []
    for rtol, atol, maximum in [(2e-11, 2e-13, duration/4), (5e-13, 5e-15, duration/8)]:
        start = time.perf_counter()
        sol = solve_ivp(lambda t, z: model.field(z, gamma=gamma), (0, duration), z0,
                        method='DOP853', rtol=rtol, atol=atol, max_step=maximum,
                        dense_output=True)
        if not sol.success:
            raise RuntimeError(sol.message)
        records.append(dict(rtol=rtol, atol=atol, max_step=maximum,
                            nfev=sol.nfev, seconds=time.perf_counter()-start))
        solutions.append(sol)
    return solutions, records


def run(output, duration=.004, steps=(.001,.0005,.00025), branches=('conservative','damped')):
    output.mkdir(parents=True, exist_ok=True)
    model = ROMBridge()
    z0 = model.initial_state()
    payload = dict(model=model.metadata(), initial_state=z0.tolist(), duration_tau=duration,
                   duration_seconds=duration/model.rom.omega0, steps=list(steps),
                   tolerance_increment_inf=TOLERANCE,
                   scope='Same 12-coordinate three-dimensional variable-mass Kirchhoff ROM; smooth conservative and declared proportional-drag branches, not full blood/contact dynamics.',
                   source_sha256={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                                  for name in ['rom_bridge.py','rom_integrators.py','run_integrators.py']},
                   error_norm='maximum Euclidean full 24-dimensional state error on each method grid',
                   reference_protocol='Independent full-state DOP853, two tolerance/max-step settings; no reference flow used by an integrator.', branches={})
    traces = {'initial':z0}
    for branch in branches:
        gamma = 0. if branch == 'conservative' else .2
        methods = ['midpoint','central4'] if gamma == 0 else ['midpoint','weighted_midpoint']
        print(f'references {branch}', flush=True)
        refs, protocol = references(model, z0, duration, gamma)
        fine_times = np.linspace(0,duration,round(duration/min(steps))+1)
        difference = float(np.max(np.linalg.norm(refs[0].sol(fine_times).T-refs[1].sol(fine_times).T,axis=1)))
        data = dict(gamma=gamma, reference=protocol, reference_refinement_maximum=difference, methods={})
        payload['branches'][branch] = data
        for method in methods:
            rows = []
            for h in steps:
                print(f'{branch} {method} h={h}', flush=True)
                states, stats = integrate(model,z0,duration,h,method,gamma,diagnose_first=True)
                times = np.arange(len(states))*h
                errors = np.linalg.norm(states-refs[1].sol(times).T,axis=1)
                energies = np.array([model.hamiltonian(z) for z in states])
                powers=[]
                for a,b in zip(states[:-1],states[1:]):
                    mid=(a+b)/2
                    velocity=model.field(mid)[:model.n]
                    powers.append(-gamma*float(mid[model.n:]@velocity))
                balance = energies-energies[0]-np.r_[0.,np.cumsum(powers)*h]
                row = dict(step=h, maximum_state_error=float(errors.max()), endpoint_error=float(errors[-1]),
                           observed_order=None if not rows else float(np.log(rows[-1]['maximum_state_error']/errors.max())/np.log(rows[-1]['step']/h)),
                           maximum_energy_drift=float(np.max(np.abs(energies-energies[0]))),
                           maximum_midpoint_power_balance_residual=float(np.max(np.abs(balance))),
                           power_balance_scope='Energy difference minus midpoint quadrature of -gamma P.H_P; quadrature defect is included, not an exact discrete-energy identity.',
                           **stats)
                rows.append(row)
                data['methods'][method] = rows
                tag=f'{branch}_{method}_{h:g}'
                traces[tag+'_time']=times
                traces[tag+'_state']=states
                traces[tag+'_reference']=refs[1].sol(times).T
                traces[tag+'_energy']=energies
                traces[tag+'_power_balance']=balance
                (output/'integrators.json').write_text(json.dumps(payload,indent=2)+'\n')
                np.savez_compressed(output/'integrators_traces.npz',**traces)
                print(json.dumps({k:row[k] for k in ['step','maximum_state_error','observed_order','seconds','max_increment_residual_inf']}),flush=True)
        for method, rows in data['methods'].items():
            assert difference < min(row['maximum_state_error'] for row in rows)*.01, (branch,method,'reference insufficiently resolved')
            expected=4 if method=='central4' else 2
            assert abs(rows[-1]['observed_order']-expected)<.15,(branch,method,rows[-1]['observed_order'])
            assert all(row['max_increment_residual_inf']<=TOLERANCE for row in rows)
            if method=='central4' or gamma==0 or method=='weighted_midpoint':
                assert max(row['first_step_diagnostics']['conformal_two_form_defect_spectral2'] for row in rows)<1e-10
    payload['status']='all convergence, residual, reference and applicable structure assertions passed'
    (output/'integrators.json').write_text(json.dumps(payload,indent=2)+'\n')
    fields=['branch','method','step','maximum_state_error','observed_order','maximum_energy_drift','maximum_midpoint_power_balance_residual','seconds','max_increment_residual_inf','max_solver_matrix_condition']
    with (output/'integrators.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for branch,data in payload['branches'].items():
            for method,rows in data['methods'].items():
                for row in rows:writer.writerow({k:branch if k=='branch' else method if k=='method' else row[k] for k in fields})
    print(payload['status'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'results/integrators')
    parser.add_argument('--branch',choices=['conservative','damped','all'],default='all')
    args=parser.parse_args()
    run(args.output,branches=('conservative','damped') if args.branch=='all' else (args.branch,))
