"""Reproducible same-model full-coil implicit integration experiments."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import traceback
import numpy as np
from scipy.integrate import solve_ivp

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.dont_write_bytecode = True
from coil_rom import CoilROM
from closed_loop import ClosedLoop, TOLERANCE, integrate

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(duration=.0005, branches=('conservative', 'proportional', 'collocated')):
    out = ROOT/'stage5/results/closed_loop'
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    model = CoilROM()
    z0 = model.initial_state(.01)
    payload = dict(status='running', started_at=datetime.now(timezone.utc).isoformat(),
        command=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
        environment={'python': platform.python_version(), **{p:importlib.metadata.version(p) for p in ('numpy','scipy','torch')}},
        source_sha256={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),
            ROOT/'stage5/program/closed_loop.py', ROOT/'stage5/program/coil_rom.py', ROOT/'stage3/program/rom_integrators.py']},
        model=model.metadata(), duration_tau=duration, duration_seconds=duration/model.rom.omega0,
        initial_state=z0.tolist(), initial_state_amplitude=.01,
        step_counts=[4,8,16], solver_increment_tolerance=TOLERANCE,
        same_field_protocol='Each branch and all methods in it share one full-coil/variable-mass field. Each branch has its own DOP853 references.',
        branches={}, limitations=['Smooth collocated feedback is not automatically constrained.',
            'No blood/contact closure has been added to the Kirchhoff ROM.',
            'No KAM or uniform-domain invertibility certificate is inferred from numerical structure.'])
    traces = {}
    def save():
        (out/'results.json').write_text(json.dumps(payload, indent=2)+'\n')
        if traces:
            np.savez_compressed(out/'trajectories.npz', **traces)
    save()
    try:
        for kind in branches:
            loop = ClosedLoop(model, kind)
            data = dict(kind=kind, gamma=loop.gamma, collocated_gain=loop.gain,
                        initial_structure=loop.structure(z0), references=[], methods={}, reference_resolution={})
            payload['branches'][kind] = data
            references = []
            for rtol, atol, maxstep in ((2e-11,2e-13,duration/4), (5e-13,5e-15,duration/8)):
                t0 = time.perf_counter()
                sol = solve_ivp(loop.field, (0,duration), z0, method='DOP853',
                    rtol=rtol, atol=atol, max_step=maxstep, dense_output=True)
                record = dict(success=bool(sol.success), message=sol.message, nfev=sol.nfev,
                    rtol=rtol, atol=atol, max_step=maxstep, seconds=time.perf_counter()-t0)
                data['references'].append(record); references.append(sol)
                save(); print(kind, 'reference', record, flush=True)
                if not sol.success:
                    raise RuntimeError(sol.message)
            grid = np.linspace(0,duration,65)
            data['reference_refinement_max'] = float(np.max(np.linalg.norm(references[0].sol(grid)-references[1].sol(grid),axis=0)))
            traces[kind+'_reference_times'] = grid
            traces[kind+'_reference_states'] = references[-1].sol(grid).T
            methods = {'conservative':['midpoint','central4'], 'proportional':['midpoint','weighted_midpoint'],
                       'collocated':['midpoint']}[kind]
            for method in methods:
                rows = []; data['methods'][method] = rows
                previous = None
                for count in (4,8,16):
                    h = duration/count; before = time.perf_counter()
                    states, info = integrate(loop, z0, duration, h, method)
                    times = np.linspace(0,duration,count+1)
                    reference = references[-1].sol(times).T
                    error = float(np.max(np.linalg.norm(states-reference,axis=1)))
                    # Powers at actual endpoint averages are separate from
                    # generated-map structure, especially for weighted methods.
                    endpoint_power = [loop.energy_and_power(z) for z in states]
                    middle_power = [loop.energy_and_power((a+b)/2) for a,b in zip(states[:-1],states[1:])]
                    fixed_H = np.array([v['fixed_bias_energy'] for v in endpoint_power])
                    mechanical_H = np.array([v['mechanical_energy'] for v in endpoint_power])
                    fixed_work = np.r_[0., np.cumsum([h*v['fixed_bias_power'] for v in middle_power])]
                    mechanical_work = np.r_[0., np.cumsum([h*v['mechanical_power'] for v in middle_power])]
                    currents = np.array([v['current'] for v in endpoint_power])
                    physical = [model.physical_samples(z[:model.n], current) for z,current in zip(states,currents)]
                    structural = [v for v in info if 'canonical_two_form_defect_2' in v]
                    row = dict(step=h, steps=count, maximum_state_error=error,
                        observed_order=None if previous is None else float(np.log2(previous/error)),
                        maximum_fixed_bias_power_balance_residual=float(np.max(abs(fixed_H-fixed_H[0]-fixed_work))),
                        maximum_mechanical_power_balance_residual=float(np.max(abs(mechanical_H-mechanical_H[0]-mechanical_work))),
                        maximum_instantaneous_power_identity_residual=max(abs(v[key]) for v in endpoint_power+middle_power
                            for key in ('fixed_bias_power_identity_residual','mechanical_power_identity_residual')),
                        maximum_current_A=float(np.max(abs(currents))),
                        maximum_sample_difference_slew_A_per_s=float(np.max(abs(np.diff(currents,axis=0)))/(h/model.rom.omega0)),
                        maximum_sampled_field_T=max(v['maximum_B_T'] for v in physical),
                        maximum_sampled_gradient_T_per_m=max(v['maximum_G_T_per_m'] for v in physical),
                        minimum_sampled_wire_distance_m=min(v['minimum_distance_exact_wire_m'] for v in physical),
                        maximum_increment_residual_inf=max(v['increment_residual_inf'] for v in info),
                        maximum_solver_condition=max(v['final_matrix_condition'] for v in info),
                        minimum_solver_singular_value=min(v['final_matrix_min_singular'] for v in info),
                        maximum_sampled_canonical_defect_2=max(v['canonical_two_form_defect_2'] for v in structural),
                        maximum_sampled_weighted_defect_2=max(v['weighted_two_form_defect_2'] for v in structural),
                        structure_steps_sampled=len(structural),
                        structure_scope='Ideal implicit tangents; all midpoint/weighted steps, first Central4 step.',
                        seconds=time.perf_counter()-before, solver_steps=info)
                    rows.append(row); previous=error
                    tag=kind+'_'+method+'_'+str(count)
                    traces[tag+'_times']=times;traces[tag+'_states']=states;traces[tag+'_reference']=reference
                    traces[tag+'_currents_A']=currents;traces[tag+'_fixed_energy']=fixed_H
                    traces[tag+'_mechanical_energy']=mechanical_H
                    traces[tag+'_fixed_work']=fixed_work;traces[tag+'_mechanical_work']=mechanical_work
                    save();print(kind,method,count,'error',error,'order',row['observed_order'],flush=True)
                    assert row['maximum_increment_residual_inf'] <= TOLERANCE
                    assert row['minimum_solver_singular_value'] > 0
                    assert np.isfinite(states).all()
                    if kind == 'conservative' or method == 'weighted_midpoint':
                        assert row['maximum_sampled_weighted_defect_2'] < 1e-10
                data['reference_resolution'][method] = data['reference_refinement_max'] < rows[-1]['maximum_state_error']*.01
            save()
        payload['status']='completed'
    except Exception as exc:
        payload['status']='failed'
        payload['failure']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        raise
    finally:
        payload['elapsed_seconds']=time.perf_counter()-start
        payload['ended_at']=datetime.now(timezone.utc).isoformat()
        save()
    return payload


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--duration',type=float,default=.0005)
    parser.add_argument('--branches',nargs='+',choices=['conservative','proportional','collocated'],
                        default=['conservative','proportional','collocated'])
    args=parser.parse_args()
    run(args.duration, tuple(args.branches))
