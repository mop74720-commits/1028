"""Execute new full-coil control transfer with explicit space/time refinement."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import time
import sys
import numpy as np
import rod_transfer_control as transfer

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'stage5/results/rod_transfer'


def run_case(name, n, dt, duration, gain, *, contact_stress=False):
    transfer.configure(gain)
    cfg = transfer.base.load_config(transfer.SOURCE/'config_position_feedback.json')
    cfg['controller']['stage5_current_port_gain_A2_per_W'] = gain
    cfg['controller']['stage5_nominal_law'] = 'inherited static compliance feedforward plus position feedback, mapped to nominal currents by weighted ridge least squares'
    cfg['controller']['stage5_executed_law'] = 'current-port correction, current-space constrained projection, continuous 2ms ramps; full Biot-Savart at every force evaluation'
    if contact_stress:
        cfg['lumen']['radius_m'] = .0016
        cfg['lumen']['stage5_stress_note'] = 'Separate narrower rigid lumen; initial quadrature penetration is zero, and contact activates during the trajectory. This tests active contact, not feasible navigation.'
    summary = transfer.base.run_case(name, OUT, cfg, n, dt, duration,
                                     min(.002, duration/20), 'coil_allocated')
    env = transfer.TransferredEnvironment.instances[-1]
    audit = transfer.constraint_summary(env)
    case = OUT/name
    (case/'current_constraint_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    (case/'feedback_updates.json').write_text(json.dumps(env.feedback_log, indent=2)+'\n')
    ramps = np.asarray(env.ramp_log)
    np.savetxt(case/'current_ramps.csv', ramps, delimiter=',',
               header='start_s,end_s,'+','.join(f'I_start_{j}_A' for j in range(12))+','+','.join(f'I_end_{j}_A' for j in range(12)), comments='')
    data = np.genfromtxt(case/'diagnostics.csv', delimiter=',', names=True)
    summary.update(status='independently_executed', gain_A2_per_W=gain,
                   actual_max_current_A=audit['actual_current_amplitude_max_A'],
                   actual_max_slew_A_per_s=audit['actual_current_slew_max_A_per_s'],
                   actual_snapshot_gradient_max_T_per_m=float(data['true_G_at_nodes_frobenius_max_T_per_m'].max()),
                   max_flow_force_power_W=float(data['power_flow_W'].max()),
                   min_flow_force_power_W=float(data['power_flow_W'].min()),
                   contact_active=bool(summary['max_contact_penetration_m']>0),
                   fullcoil_every_step=True,
                   source_path='stage3/source_inputs/starter/stage2/program/rod3d/model.py',
                   extension_sha256=hashlib.sha256((ROOT/'stage5/program/rod_transfer_control.py').read_bytes()).hexdigest(),
                   no_ROM_error_claim='No same-initial-state and matched-flow/contact ROM trajectory exists; these are high-dimensional transfer/refinement results, not a ROM-to-PDE error certificate.')
    (case/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


def pair_difference(first, second):
    """Centerlines compared at common saved time and reference arclength."""
    with np.load(OUT/first/'trajectory.npz') as a, np.load(OUT/second/'trajectory.npz') as b:
        assert np.allclose(a['time_s'], b['time_s'], atol=1e-14, rtol=0)
        grid = np.linspace(0., .1, 129)
        ra = np.stack([[np.interp(grid, a['reference_s_m'], r[:, j]) for j in range(3)] for r in a['r']])
        rb = np.stack([[np.interp(grid, b['reference_s_m'], r[:, j]) for j in range(3)] for r in b['r']])
        delta = ra-rb
        tip_delta = a['r'][:, -1]-b['r'][:, -1]
        return dict(first=first, second=second, common_reference_samples=129,
                    centerline_time_space_rms_m=float(np.sqrt(np.mean(np.sum(delta*delta, axis=1)))),
                    tip_time_rms_m=float(np.sqrt(np.mean(np.sum(tip_delta*tip_delta, axis=1)))),
                    max_centerline_difference_m=float(np.max(np.sqrt(np.sum(delta*delta, axis=1)))),
                    scope='Adjacent numerical solutions, not error against exact PDE.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gain', type=float, default=95590.3224538941)
    parser.add_argument('--duration', type=float, default=.2)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    start = time.perf_counter()
    cases = [('baseline_n32_h10us', 32, 1e-5, 0., False),
             ('port_n16_h5us', 16, 5e-6, args.gain, False),
             ('port_n32_h10us', 32, 1e-5, args.gain, False),
             ('port_n32_h5us', 32, 5e-6, args.gain, False),
             ('port_n32_h2p5us', 32, 2.5e-6, args.gain, False),
             ('port_n64_h5us', 64, 5e-6, args.gain, False),
             ('port_contact_n32_h5us', 32, 5e-6, args.gain, True)]
    if args.smoke:
        cases = [('smoke_n16_h10us', 16, 1e-5, args.gain, False)]
    summaries, failures = [], []
    for name, n, dt, gain, contact in cases:
        try:
            summaries.append(run_case(name, n, dt, args.duration, gain, contact_stress=contact))
        except Exception as error:
            failures.append(dict(case=name, exception=type(error).__name__, message=str(error)))
        (OUT/('smoke_execution.json' if args.smoke else 'execution.json')).write_text(json.dumps(
            dict(command=sys.argv, python=sys.version, elapsed_s=time.perf_counter()-start,
                 summaries=summaries, failures=failures, current_protocol='All physical rod parameters unchanged except explicit narrow-lumen stress case.'), indent=2)+'\n')
    if failures:
        raise SystemExit(1)
    if args.smoke:
        return
    pairs = [pair_difference('port_n16_h5us', 'port_n32_h5us'),
             pair_difference('port_n32_h5us', 'port_n64_h5us'),
             pair_difference('port_n32_h10us', 'port_n32_h5us'),
             pair_difference('port_n32_h5us', 'port_n32_h2p5us'),
             pair_difference('baseline_n32_h10us', 'port_n32_h10us')]
    result = dict(pairs=pairs,
                  observed_space_order=float(np.log2(pairs[0]['centerline_time_space_rms_m']/pairs[1]['centerline_time_space_rms_m'])),
                  observed_time_order=float(np.log2(pairs[2]['centerline_time_space_rms_m']/pairs[3]['centerline_time_space_rms_m'])),
                  numerical_order_scope='Observed adjacent differences only; no smoothness or formal order claim for the open constrained controller.')
    (OUT/'refinement.json').write_text(json.dumps(result, indent=2)+'\n')
    with (OUT/'comparison.csv').open('w', newline='') as f:
        fields = ['case','n_elements','dt_s','duration_s','gain_A2_per_W','tip_rmse_m','final_tip_error_m','max_contact_penetration_m','max_total_contact_normal_N','energy_work_residual_J','energy_work_residual_scaled','actual_max_current_A','actual_max_slew_A_per_s','wall_time_s']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(summaries)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
