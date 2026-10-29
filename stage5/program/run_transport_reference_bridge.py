"""Recompute the current full-coil physical reference and quantify roundoff drift.

The mathematical coil model is unchanged by a differentiable norm rewrite,
but roundoff in the local bias least-squares fit changes currents slightly.
This run does not claim bit-identical input across old and new snapshots.
"""
from pathlib import Path
import importlib.util,json,hashlib,sys,time
import numpy as np
from scipy.integrate import solve_ivp
from coil_rom import CoilROM
from closed_loop import ClosedLoop
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'stage5/results/transport';dest=out/'inverse_verified_reference_bridge.json'
    if dest.exists():raise FileExistsError(dest)
    start=time.perf_counter();source=ROOT/'stage5/results/closed_loop/source_used/coil_rom.py'
    spec=importlib.util.spec_from_file_location('closed_loop_frozen_coil_kernel',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    old=module.CoilROM();current=CoilROM();old_loop=ClosedLoop(old,'collocated');loop=ClosedLoop(current,'collocated')
    prior=json.loads((ROOT/'stage5/results/closed_loop/results.json').read_text());shared=np.load(ROOT/'stage5/results/closed_loop/shared_collocated_reference.npz');times=shared['collocated_reference_times'];states=shared['collocated_reference_states'];z0=np.asarray(prior['initial_state']);T=float(times[-1])
    report=dict(status='running',command=sys.argv,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),source,ROOT/'stage5/program/coil_rom.py',ROOT/'stage5/program/closed_loop.py']},old_bias_current_A=old.bias_currents.tolist(),new_bias_current_A=current.bias_currents.tolist(),maximum_bias_change_A=float(np.max(abs(old.bias_currents-current.bias_currents))),old_gain=float(old.collocated_gain),new_gain=float(current.collocated_gain),old_metadata_bias_reconstruction_difference_A=float(np.max(abs(old.bias_currents-np.asarray(prior['model']['bias_currents_A'])))),reference=dict(method='DOP853',rtol=5e-13,atol=5e-15,max_step=T/8),interpretation='Shared mathematical full-coil and feedback definitions; no claim of bit-identical recalculated bias. Old numeric reference retained; current numeric field independently integrated.')
    save=lambda:dest.write_text(json.dumps(report,indent=2)+'\n');save()
    report['sampled_old_new_field_differences']=[dict(index=int(k),difference_2=float(np.linalg.norm(loop.field(times[k],states[k])-old_loop.field(times[k],states[k])))) for k in [0,16,32,48,64]]
    sol=solve_ivp(loop.field,(0,T),z0,method='DOP853',rtol=5e-13,atol=5e-15,max_step=T/8,dense_output=True)
    if not sol.success:raise RuntimeError(sol.message)
    newstates=sol.sol(times).T;report['reference'].update(nfev=sol.nfev,success=sol.success,message=sol.message)
    report['maximum_new_old_reference_state_difference_2']=float(np.max(np.linalg.norm(newstates-states,axis=1)))
    report['new_reference_errors']=[]
    main=json.loads((out/'fullcoil_collocated/inverse_verified.json').read_text());traces=np.load(out/'fullcoil_collocated/inverse_verified_traces.npz')
    for row in main['rows']:
        n=row['steps'];computed=traces[f"chart_r{row['order']}_steps{n}"];error=float(np.max(np.linalg.norm(computed-newstates[::64//n],axis=1)))
        report['new_reference_errors'].append(dict(order=row['order'],steps=n,error_to_new_current_reference=error,prior_shared_reference_error=row['error_to_original_max'],absolute_error_metric_change=abs(error-row['error_to_original_max'])))
    np.savez_compressed(out/'inverse_verified_reference_bridge.npz',times=times,new_current_field_reference=newstates,old_shared_reference=states)
    report.update(status='completed',seconds=time.perf_counter()-start);save()

if __name__=='__main__':main()
