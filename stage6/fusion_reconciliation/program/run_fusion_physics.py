"""Reproduce full-coil power/clearance reconciliation; writes only stage6."""
from __future__ import annotations
from pathlib import Path
import csv
import json
import platform
import sys
import time
import numpy as np
import torch
from fusion_physics import (CoilROM, CurrentAllocator, PowerCurrentAllocator,
                           clearance_coefficient, mechanical_energy, power_port, ramp_rk4)


OUT = Path(__file__).resolve().parents[1]/'results/physics'


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    model = CoilROM()
    initial = model.initial_state(.01)
    y0, _ = power_port(model, initial)
    request = .3*y0/np.linalg.norm(y0)
    energy0 = mechanical_energy(model, initial)
    cap = energy0+1e-8
    h, steps, gamma, kappa = .001, 4, .02, 20.
    coefficient = clearance_coefficient(model.rom.L, float(model.rom.bending.min()))
    results = dict(status='independently executed', command='python stage6/fusion_reconciliation/program/run_fusion_physics.py',
        python=sys.version, numpy=np.__version__, torch=torch.__version__, platform=platform.platform(),
        metadata=model.metadata(), initial_state=initial.tolist(),
        protocol=dict(h_tau=h, steps=steps, T_tau=h*steps, T_s=h*steps/model.rom.omega0,
                      gamma=gamma, kappa_tau_inverse=kappa, energy_cap_E0=cap,
                      initial_mechanical_energy_E0=energy0, initial_current_A=[0.]*12,
                      requested_current_A=request.tolist(), field_limit_T=.005,
                      gradient_limit_T_per_m=.03, current_limit_A=model.coil_config['current_bound_A'],
                      slew_limit_A_s=model.coil_config['slew_bound_A_s'],
                      model='20-cell actual 12-coordinate 24-phase-space ROM; full variable mass and full 256-point coil quadrature'),
        clearance=dict(coefficient_m2_per_J=coefficient,
                       implied_straight_reference_centerline_radius_m=float(np.sqrt(coefficient*cap*model.rom.E0)),
                       scope='straight stress-free reference and clamped root; sufficient theorem, not vascular clearance'),
        negative_counterexamples=dict(signed_fullcoil_H_E0=model.hamiltonian(initial, model.bias_currents),
                                      positive_mechanical_energy_E0=energy0), runs=[])
    states = {}
    csv_rows = []
    for subdivisions in (1, 2, 4):
        for governed in (False, True):
            name = f'{"governed" if governed else "baseline"}_rk4sub{subdivisions}'
            allocator = PowerCurrentAllocator(model) if governed else CurrentAllocator(model)
            z = initial.copy()
            previous = np.zeros(12)
            work = energy0
            dissipation = 0.
            history = [z.copy()]
            currents = [previous.copy()]
            records = []
            start = time.perf_counter()
            failure = None
            for k in range(steps):
                upper = kappa*(cap-work)
                try:
                    if governed:
                        target, allocation = allocator.allocate_power(z, request, previous, h/model.rom.omega0, upper)
                    else:
                        target, allocation = allocator.allocate(z[:12], request, previous, h/model.rom.omega0)
                    y, _ = power_port(model, z)
                    endpoint, increment, loss, residual, stages = ramp_rk4(model, z, previous, target, h, gamma, subdivisions)
                except RuntimeError as exc:
                    failure = dict(step=k, reason=str(exc), status='failure saved; no substituted control')
                    break
                work += increment
                dissipation += loss
                sample = model.physical_samples(endpoint[:12], target)
                energy = mechanical_energy(model, endpoint)
                data = dict(name=name, step=k+1, tau=(k+1)*h, time_s=(k+1)*h/model.rom.omega0,
                            mechanical_energy_E0=energy, work_ledger_E0=work,
                            cumulative_dissipation_E0=dissipation,
                            independent_energy_ledger_residual_E0=energy-work+dissipation,
                            step_power_residual_E0=residual,
                            decision_target_power_dE0_dtau=float(y@target),
                            decision_power_upper_dE0_dtau=upper,
                            maximum_RK_stage_power_dE0_dtau=max(s['power'] for s in stages),
                            maximum_current_A=float(abs(target).max()),
                            maximum_slew_A_s=float(abs(target-previous).max()*model.rom.omega0/h),
                            maximum_B_T=sample['maximum_B_T'],
                            maximum_G_T_per_m=sample['maximum_G_T_per_m'],
                            current_allocation_residual_A=allocation['current_request_distance_A'],
                            generalized_force_allocation_residual=allocation['generalized_force_allocation_residual'],
                            constraint_violation=allocation['constraint_violation'])
                csv_rows.append(data)
                records.append(dict(**data, allocation=allocation, RK_stages=stages))
                z = endpoint
                previous = target
                history.append(z.copy())
                currents.append(previous.copy())
            states[name] = np.asarray(history)
            states[name+'_currents_A'] = np.asarray(currents)
            results['runs'].append(dict(name=name, completed_steps=len(records), failure=failure,
                                       elapsed_s=time.perf_counter()-start, records=records,
                                       final_state=z.tolist()))
    for governed in ('baseline', 'governed'):
        a, b, c = (states[f'{governed}_rk4sub{n}'][-1] for n in (1, 2, 4))
        results[f'{governed}_time_refinement'] = dict(
            endpoint_difference_1_vs_2=float(np.linalg.norm(a-b)),
            endpoint_difference_2_vs_4=float(np.linalg.norm(b-c)),
            note='fixed control decision interval; trajectory plus independently recomputed allocation; finite differences do not certify asymptotic order')
    results['limitations'] = [
        'Only 0.897 ms local experiment; no long-time tracking/clearance certification.',
        'Power constraint is imposed at decision state; RK-stage powers are observations, not interval envelopes.',
        'Slew-restricted feasible sets need not include zero; infeasible governor is explicitly tested and rejected.',
        'Moving-point fields sampled at step endpoints; no continuous workspace field bound.',
        'Smooth proportional drag only; unknown blood-flow work, contact, wall motion and microgravity physiology are not activated.',
        'A power governor changes the requested Hamiltonian dynamics and does not imply symplecticity or KAM.']
    (OUT/'experiment.json').write_text(json.dumps(results, indent=2, ensure_ascii=False)+'\n')
    np.savez_compressed(OUT/'trajectories.npz', **states, initial_state=initial)
    with (OUT/'trajectory_summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(json.dumps(dict(runs=[dict(name=r['name'], completed=r['completed_steps'], failure=r['failure'],
                                       elapsed_s=r['elapsed_s']) for r in results['runs']],
                          signed_H_E0=results['negative_counterexamples']['signed_fullcoil_H_E0'],
                          clearance_radius_m=results['clearance']['implied_straight_reference_centerline_radius_m'],
                          baseline_refinement=results['baseline_time_refinement'],
                          governed_refinement=results['governed_time_refinement']), indent=2))


if __name__ == '__main__':
    run()
