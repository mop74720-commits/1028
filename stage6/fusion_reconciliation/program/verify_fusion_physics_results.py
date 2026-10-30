"""Independent geometry/ledger inspection of saved current-governor runs."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fusion_physics import CoilROM, PowerCurrentAllocator, clearance_coefficient, power_port


BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
OUT = BASE/'results/physics'


def run():
    model = CoilROM()
    data = json.loads((OUT/'experiment.json').read_text())
    saved = np.load(OUT/'trajectories.npz')
    C = clearance_coefficient(model.rom.L, float(model.rom.bending.min()))
    rest = np.zeros((model.rom.elements+1, 3))
    rest[:, 2] = np.linspace(0, model.rom.L, model.rom.elements+1)
    fields = {}
    diagnostics = dict(status='independently executed postprocessing of unchanged experiment NPZ',
                       command='python stage6/fusion_reconciliation/program/verify_fusion_physics_results.py',
                       source_sha256={}, geometry={})
    for rel in ['stage5/program/coil_rom.py','stage5/program/coil_control.py',
                'stage3/program/rom_bridge.py','stage3/source_inputs/starter/stage2/program/learning/rod_rom.py',
                'stage6/fusion_reconciliation/program/fusion_physics.py',
                'stage6/fusion_reconciliation/program/run_fusion_physics.py',
                'stage6/fusion_reconciliation/tests/test_fusion_physics.py']:
        diagnostics['source_sha256'][rel] = hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
    for name in ['baseline_rk4sub4', 'governed_rk4sub4']:
        z = saved[name]
        positions, energies, ratios, frame_defects = [], [], [], []
        for state in z:
            q = model.rom.Sq @ model.tensor(state[:12])
            _, elastic, pos, frame, _ = model.rom.mechanics(q[None, :], field=model.zero_field, return_geometry=True)
            pos = pos[0].numpy()
            displacement = np.linalg.norm(pos-rest, axis=1).max()
            energies.append(float(elastic[0]))
            ratios.append(displacement**2/(C*float(elastic[0])))
            positions.append(pos)
            frame_defects.append(float(torch.linalg.matrix_norm(frame.transpose(-1,-2)@frame-torch.eye(3), dim=(-2,-1)).max()))
        fields[name+'_centerlines_m'] = np.asarray(positions)
        diagnostics['geometry'][name] = dict(
            maximum_straight_reference_displacement_m=float(np.linalg.norm(np.asarray(positions)-rest, axis=2).max()),
            maximum_squared_displacement_over_bound=float(max(ratios)),
            maximum_SO3_orthogonality_defect=float(max(frame_defects)),
            initial_tip_m=positions[0][-1].tolist(), final_tip_m=positions[-1][-1].tolist(),
            centerline_nodes=model.rom.elements+1)
        assert max(ratios) <= 1+1e-12
        rec = next(r for r in data['runs'] if r['name'] == name)['records']
        t = np.r_[0, [r['time_s'] for r in rec]]*1e3
        energy = np.r_[data['protocol']['initial_mechanical_energy_E0'], [r['mechanical_energy_E0'] for r in rec]]
        work = np.r_[data['protocol']['initial_mechanical_energy_E0'], [r['work_ledger_E0'] for r in rec]]
        axes[0].plot(t, (energy-energy[0])*model.rom.E0*1e12, marker='o', label=name.split('_')[0])
        axes[1].plot(t, np.linalg.norm(np.asarray(positions)-rest, axis=2).max(axis=1)*1e3, marker='o', label=name.split('_')[0])
        assert max(r['maximum_slew_A_s'] for r in rec) <= 20.+1e-10
        if name.startswith('governed'):
            assert max(r['decision_target_power_dE0_dtau']-r['decision_power_upper_dE0_dtau'] for r in rec) <= 1e-12
        diagnostics['geometry'][name]['maximum_observed_work_minus_cap_E0'] = float(work.max()-data['protocol']['energy_cap_E0'])
    axes[0].set(xlabel='physical time (ms)', ylabel='mechanical energy change (pJ)', title='Actual full-coil integration')
    axes[1].set(xlabel='physical time (ms)', ylabel='max centerline displacement (mm)', title='Relative to the clamped straight reference')
    for ax in axes:
        ax.legend()
        ax.grid(alpha=.25)
    fig.savefig(OUT/'power_governor.svg')
    plt.close(fig)
    # Save a fully specified infeasible request, not just a passing assertRaises.
    initial = saved['initial_state']
    y, _ = power_port(model, initial)
    previous = .05*np.sign(y)
    allocator = PowerCurrentAllocator(model, field_bound_T=1., gradient_bound_T_per_m=100.)
    failure = dict(z=initial.tolist(), previous_current_A=previous.tolist(), physical_interval_s=1e-7,
                   allowed_power=0., previous_power=float(y@previous),
                   analytic_minimum_power_over_slew_box=float(y@previous-model.coil_config['slew_bound_A_s']*1e-7*np.sum(abs(y))),
                   physical_field_limits_deliberately_loose=True)
    assert failure['analytic_minimum_power_over_slew_box'] > failure['allowed_power']
    try:
        allocator.allocate_power(initial, previous, previous, 1e-7, 0.)
    except RuntimeError as exc:
        failure.update(status='expected physical feasibility failure recorded', message=str(exc))
    else:
        raise AssertionError('The independently constructed slew/power conflict was not rejected')
    diagnostics['slew_feasibility_counterexample'] = failure
    diagnostics['scope'] = 'Observed full-coil 24D trajectories and straight-reference sufficient geometric inequality; no sampled-data clearance certificate'
    np.savez_compressed(OUT/'centerlines.npz', **fields, reference_centerline_m=rest)
    (OUT/'independent_diagnostics.json').write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(diagnostics['geometry'], indent=2))
    print(failure['message'])


if __name__ == '__main__':
    run()
