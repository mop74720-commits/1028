"""Refine saved local references with half max_step; retain all integrator runs.

Used once after diagnosing identical adaptive grids in the initial two-tolerance
reference run. Fresh run_birkhoff.py already uses the corrected protocol.
"""
from pathlib import Path
import json
import time
import numpy as np
from scipy.integrate import solve_ivp
from birkhoff_rom import LocalBirkhoffROM

root=Path(__file__).resolve().parents[1]/'results/birkhoff'
path=root/'results_T0.0005.json';r=json.loads(path.read_text());T=r['duration_tau']
traces=dict(np.load(root/'trajectories_T0.0005.npz'));grid=traces['reference_times']
m=LocalBirkhoffROM();z0=np.array(r['initial_state']);references={}
for name,fun in [('original',lambda t,z:m.original_field(z)),('represented',m.approximate_field)]:
    start=time.perf_counter()
    sol=solve_ivp(fun,(0,T),z0,method='DOP853',rtol=5e-12,atol=5e-14,max_step=T/16,dense_output=True)
    assert sol.success
    difference=float(np.linalg.norm(sol.sol(grid).T-traces[name+'_reference'],axis=1).max())
    references[name]=sol
    r[name+'_reference_refinement_max']=difference
    entries=[v for v in r['references'] if v['field']==name]
    entries[0]['max_step']=T/8
    entries[1].update(max_step=T/16,nfev=sol.nfev,seconds=time.perf_counter()-start)
    print(name,entries[1],'refinement',difference,flush=True)
    traces[name+'_reference']=sol.sol(grid).T
for method in ('original_midpoint','birkhoff_chart_midpoint'):
    previous=None
    for row in [v for v in r['rows'] if v['method']==method]:
        states=traces[f"{method}_h{row['h']:g}"];times=np.arange(len(states))*row['h']
        row['error_to_original_max']=float(np.linalg.norm(states-references['original'].sol(times).T,axis=1).max())
        row['error_to_represented_max']=float(np.linalg.norm(states-references['represented'].sol(times).T,axis=1).max())
        error=row['error_to_original_max'] if method=='original_midpoint' else row['error_to_represented_max']
        row['observed_order_to_integrated_field']=None if previous is None else float(np.log2(previous/error))
        previous=error
r['represented_vs_original_reference_gap']=float(np.linalg.norm(traces['original_reference']-traces['represented_reference'],axis=1).max())
r['reference_refinement_note']='Initial stricter-tolerance run used identical step grids and gave zero difference. Recomputed stricter references with halved max_step, preserving actual integrator outputs. Fresh runner uses this protocol.'
path.write_text(json.dumps(r,indent=2)+'\n')
np.savez_compressed(root/'trajectories_T0.0005.npz',**traces)
import csv
with (root/'metrics_T0.0005.csv').open('w') as f:
    keys=['method','h','error_to_original_max','error_to_represented_max','observed_order_to_integrated_field','residual_inf','seconds','original_power_balance_residual_max']
    writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows(r['rows'])
