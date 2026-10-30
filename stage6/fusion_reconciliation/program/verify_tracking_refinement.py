"""Independent smaller maximum-step check of the saved S6-T01 actual currents."""
import json
import argparse
import time
import numpy as np
from scipy.integrate import solve_ivp
from learned_reference_tracking import CoilROM,ROOT
from coil_control import ramp_current


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='S6_T01');args=parser.parse_args()
    out=ROOT/'stage6/fusion_reconciliation/results/history'/args.run_id
    record=json.loads((out/'results.json').read_text());data=np.load(out/'trajectories.npz')
    model=CoilROM();z=data['plant'][0].copy();trajectory=[z.copy()];calls=0;started=time.perf_counter()
    for j,(begin,end) in enumerate(zip(data['tau'][:-1],data['tau'][1:])):
        old=data['currents_start'][j];target=data['currents_target'][j]
        sol=solve_ivp(lambda t,y:model.field(y,ramp_current(old,target,t,begin,end),record['gamma']),
            (begin,end),z,method='DOP853',rtol=2e-12,atol=2e-14,max_step=(end-begin)/4)
        if not sol.success:raise RuntimeError(sol.message)
        z=sol.y[:,-1];trajectory.append(z.copy());calls+=sol.nfev
    error=float(np.max(np.linalg.norm(np.asarray(trajectory)-data['plant'],axis=1)))
    result=dict(status='independently actually run',maximum_state_difference=error,nfev=calls,
        method='DOP853',rtol=2e-12,atol=2e-14,maximum_step_tau=.000125,
        original_tolerance_only_difference=record['summary']['same_schedule_tolerance_difference'],
        explanation='Original tolerance-only rerun used the same accepted steps and returned identical floating values; explicitly smaller maximum step adds an independent refinement check, not a rigorous enclosure.',
        seconds=time.perf_counter()-started)
    (out/'fixed_schedule_refinement.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez(out/'fixed_schedule_refinement.npz',tau=data['tau'],plant=np.asarray(trajectory))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
