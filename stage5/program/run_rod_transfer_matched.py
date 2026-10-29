"""Matched fixed-current regression of Kirchhoff ROM versus full Cosserat rods.

This separate conservative diagnostic disables environmental loads in BOTH
models. The main rod-transfer experiment retains flow/contact. Zero straight
position/velocity, total currents and material parameters are common.
"""
from pathlib import Path
import argparse
import json
import time
import sys
import hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'stage5/results/rod_transfer/matched'
OUT.mkdir(parents=True, exist_ok=True)


def rom_reference(duration):
    import torch
    from scipy.integrate import solve_ivp
    from coil_rom import CoilROM
    model = CoilROM()
    current = model.bias_currents.copy()
    z0 = np.zeros(24)
    t = np.linspace(0., duration, 21)
    tau = t*model.rom.omega0
    records, solutions = [], []
    start = time.perf_counter()
    for rtol, atol, sub in [(2e-10, 2e-12, 10), (5e-12, 5e-14, 20)]:
        result = solve_ivp(lambda tt, z: model.field(z, current), [0., tau[-1]], z0,
                           method='DOP853', rtol=rtol, atol=atol,
                           max_step=tau[-1]/sub, t_eval=tau)
        if not result.success:
            raise RuntimeError(result.message)
        records.append(dict(rtol=rtol, atol=atol, max_step_tau=tau[-1]/sub,
                            evaluations=result.nfev, success=result.success))
        solutions.append(result.y.T)
    positions = []
    for z in solutions[-1]:
        q = model.rom.Sq@torch.tensor(z[:12])
        geometry = model.rom.mechanics(q[None, :], field=torch.zeros(8), return_geometry=True)[2]
        positions.append(geometry[0].detach().numpy())
    np.savez_compressed(OUT/'rom_reference.npz', time_s=t, z=solutions[-1], r=np.asarray(positions),
                        reference_s_m=np.linspace(0., model.rom.L, model.rom.elements+1),
                        total_currents_A=current, initial_z=z0)
    result = dict(status='independently_executed', references=records,
                  reference_refinement_max_state_norm=float(np.max(np.linalg.norm(solutions[0]-solutions[1], axis=1))),
                  elapsed_s=time.perf_counter()-start, python=sys.version,
                  total_currents_A=current.tolist(), omega0=model.rom.omega0, E0_J=model.rom.E0,
                  initial_state='straight untwisted rod, zero all configuration coefficients and momenta',
                  boundary='ROM fixes continuum base frame; Cosserat fixes first element frame, causing finite-spatial-step boundary discrepancy',
                  field='Full 256-source-point circular coils; total bias currents, no extra ideal bias',
                  source_sha256=hashlib.sha256((ROOT/'stage5/program/coil_rom.py').read_bytes()).hexdigest(),
                  scope='Conservative same-input model comparison only; not the flow/contact tracking case or a proven ROM error bound.')
    (OUT/'rom_reference.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


def rod_comparison():
    import rod_transfer_control as transfer
    from scipy.interpolate import interp1d
    with np.load(OUT/'rom_reference.npz') as data:
        current = data['total_currents_A'].copy()
        times = data['time_s'].copy()
        rr, sr = data['r'].copy(), data['reference_s_m'].copy()
    duration = float(times[-1])
    class FixedCurrentEnvironment(transfer.bs.FullCoilEnvironment):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.currents = current.copy()
            self.held_u = self.allocator.A@current
            self.coil_log = [np.r_[tt, self.held_u, self.held_u, current] for tt in [0., duration]]
        def apply_forces(self, system, time=0.):
            self.last = self.evaluate(system, time)
            self.before_v = system.velocity_collection.copy()
            self.before_w = system.omega_collection.copy()
            system.external_forces += self.last[0].sum(axis=0)
            system.external_torques += self.last[1].sum(axis=0)
    transfer.base.Environment = FixedCurrentEnvironment
    transfer.base.metrics_snapshot = transfer.bs.full_snapshot
    cfg = transfer.base.load_config(transfer.SOURCE/'config_position_feedback.json')
    cfg['rod']['mass_proportional_damping_rate_s_inv'] = 0.
    for key in ['flow','lumen','microgravity']:
        cfg[key]['enabled'] = False
    cfg['controller']['target_base_xy_m'] = [0.,0.]
    cfg['controller']['target_amplitude_xy_m'] = [0.,0.]
    cfg['controller']['matched_fixed_current_note'] = 'Pre-energized total currents from actual ROM; no current jumps or supplementary ideal bias.'
    grid = np.linspace(0., .1, 129)
    rom = np.stack([[np.interp(grid, sr, r[:, j]) for j in range(3)] for r in rr])
    records = []
    for n in [16, 32, 64]:
        name = f'fixed_n{n}_h2p5us'
        summary = transfer.base.run_case(name, OUT, cfg, n, 2.5e-6, duration,
                                         duration/20, 'coil_allocated')
        diagnostics = np.genfromtxt(OUT/name/'diagnostics.csv', delimiter=',', names=True)
        true_gradient_max = float(diagnostics['true_G_at_nodes_frobenius_max_T_per_m'].max())
        summary['true_full_coil_gradient_max_T_per_m'] = true_gradient_max
        summary['fixed_bias_satisfies_node_gradient_limit'] = bool(true_gradient_max<=.03)
        summary['constraint_scope'] = 'Unconstrained fixed-bias model-comparison diagnostic. Bias fitted at distal origin violates the gradient limit at unmagnetized upstream rod nodes; not an admissible navigation controller.'
        (OUT/name/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        with np.load(OUT/name/'trajectory.npz') as data:
            assert np.allclose(times, data['time_s'], rtol=0, atol=1e-14)
            sr_rod, r_rod = data['reference_s_m'], data['r']
            physical = np.stack([[np.interp(grid, sr_rod, r[:, j]) for j in range(3)] for r in r_rod])
            delta = physical-rom
            tip_delta = r_rod[:, -1]-rr[:, -1]
            records.append(dict(n_elements=n, physical_duration_s=duration,
                                centerline_time_space_rms_m=float(np.sqrt(np.mean(np.sum(delta*delta,axis=1)))),
                                tip_time_rms_m=float(np.sqrt(np.mean(np.sum(tip_delta*tip_delta,axis=1)))),
                                final_tip_difference_m=float(np.linalg.norm(tip_delta[-1])),
                                final_rod_tip_displacement_m=float(np.linalg.norm(r_rod[-1,-1]-r_rod[0,-1])),
                                final_ROM_tip_displacement_m=float(np.linalg.norm(rr[-1,-1]-rr[0,-1])),
                                true_node_gradient_max_T_per_m=true_gradient_max,
                                gradient_limit_T_per_m=.03,
                                node_gradient_limit_satisfied=bool(true_gradient_max<=.03),
                                mechanical_work_residual_J=summary['energy_work_residual_J']))
    output = dict(status='independently_executed', records=records,
                  matching='same straight static initial state, same constant full coil currents/material/magnet, no fluid/contact/gravity/damping in either model',
                  differences='Kirchhoff ROM constrains shear/stretch, truncates 12 Ritz coordinates, uses20-cell midpoint mass/field; rods retain shear/stretch and N-dependent boundary and magnetic quadrature.',
                  constraint_scope='The local bias fit is held fixed for model comparison, not projected. It violates full-rod gradient limits, explicitly retained as a diagnostic limitation. Main transfer uses tube-constrained actual currents.',
                  interpretation='These observed model differences are not monotone convergence to ROM or a rigorous PDE error estimate. The separate main experiment retains flow/contact.')
    (OUT/'model_difference.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['rom','rod'])
    parser.add_argument('--duration', type=float, default=.002)
    args = parser.parse_args()
    if args.mode == 'rom':
        rom_reference(args.duration)
    else:
        rod_comparison()
