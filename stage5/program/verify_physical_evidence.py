"""Independently recheck saved physical trajectories and source provenance.

This is numerical postprocessing, not a fresh dynamics integration. It reads
raw NPZ/CSV arrays rather than trusting the prose or summary values, and never
writes into a previous experiment directory.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
COIL = ROOT / 'stage5/results/coil'
ROD = ROOT / 'stage5/results/rod_transfer'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    started = time.perf_counter()
    source_checks = []
    snapshot = {
        'coil_rom.py': COIL/'source_before_higher_ad_fix.py',
        'coil_control.py': COIL/'source_before_force_warm_fix_coil_control.py',
        'run_coil_validation.py': COIL/'source_before_force_warm_fix_run_coil_validation.py',
        'run_coil_closed_loop.py': COIL/'source_before_force_warm_fix_run_coil_closed_loop.py',
    }
    for directory, old in ((COIL, True), (COIL/'force_warm_fix', False)):
        for name in ('validation.json', 'closed_loop_summary.json'):
            report = read(directory/name)
            for module, expected in report['source_sha256'].items():
                path = snapshot[module] if old else ROOT/'stage5/program'/module
                match = sha(path) == expected
                source_checks.append(dict(report=str((directory/name).relative_to(ROOT)),
                    source=str(path.relative_to(ROOT)), sha256=expected, matches=match))
                assert match, (directory/name, path)

    coil_checks = []
    for directory in (COIL, COIL/'force_warm_fix'):
        summary = read(directory/'closed_loop_summary.json')
        omega = summary['model']['omega0_rad_s']
        with np.load(directory/'closed_loop_trajectories.npz') as arrays:
            for run in summary['runs']:
                name = f"{run['plant']}_plant_{run['controller']}_control_substeps{run['substeps_per_control_interval']}"
                tau, z, current = (arrays[name+suffix] for suffix in ('_tau', '_state', '_current_A'))
                assert np.isfinite(z).all() and np.isfinite(current).all()
                assert np.array_equal(z[0], run['state_initial'])
                assert np.array_equal(z[-1], run['state_final'])
                current_max = float(np.abs(current).max())
                slew = float(np.max(np.abs(np.diff(current, axis=0))/np.diff(tau)[:, None])*omega)
                assert current_max <= 2+1e-10 and slew <= 20+1e-8
                details = read(directory/(name+'_details.json'))
                B = max(s['maximum_B_T'] for s in details['RK_stage_checks'])
                G = max(s['maximum_G_T_per_m'] for s in details['RK_stage_checks'])
                assert B <= .005 and G <= .03
                for energy, work, residual in (
                    ('total_energy_change', 'total_input_work', 'total_power_balance_residual'),
                    ('mechanical_energy_change', 'mechanical_net_work', 'mechanical_power_balance_residual')):
                    assert abs(run[energy]-run[work]-run[residual]) < 1e-18
                coil_checks.append(dict(directory=str(directory.relative_to(ROOT)),case=name,
                    trajectory_sha256=sha(directory/'closed_loop_trajectories.npz'),
                    maximum_current_A=current_max, ramp_slew_from_raw_nodes_A_s=slew,
                    maximum_RK_magnet_point_B_T=B, maximum_RK_magnet_point_gradient_T_per_m=G,
                    total_energy_work_residual=run['total_power_balance_residual'],
                    mechanical_energy_work_residual=run['mechanical_power_balance_residual']))

    rod_checks = []
    for summary in read(ROD/'execution.json')['summaries']:
        folder = ROD/summary['case']
        rows = np.genfromtxt(folder/'diagnostics.csv', delimiter=',', names=True)
        ramps = np.genfromtxt(folder/'current_ramps.csv', delimiter=',', names=True)
        begin = np.column_stack([ramps[f'I_start_{j}_A'] for j in range(12)])
        end = np.column_stack([ramps[f'I_end_{j}_A'] for j in range(12)])
        slew = float(np.max(np.abs(end-begin)/(ramps['end_s']-ramps['start_s'])[:, None]))
        continuity = float(np.max(np.abs(end[:-1]-begin[1:])))
        current_max = float(max(np.abs(begin).max(), np.abs(end).max()))
        assert current_max <= 2+1e-10 and slew <= 20+1e-8 and continuity < 1e-12
        with np.load(folder/'trajectory.npz') as raw:
            for key in raw.files:
                assert np.isfinite(raw[key]).all(), (folder, key)
            error = np.linalg.norm(raw['r'][:, -1]-raw['target'], axis=1)
            rmse = float(np.sqrt(np.mean(error**2)))
            penetration = float(raw['contact_penetration_m'].max())
            normal_force = float(raw['contact_normal_force_N'].sum(axis=1).max())
            gradient = float(np.linalg.norm(raw['field_gradient_at_nodes_T_per_m'], axis=(2,3)).max())
            flow_force = float(np.linalg.norm(raw['force_flow'].sum(axis=1), axis=1).max())
            assert abs(rmse-summary['tip_rmse_m']) < 1e-14
            # Summary extrema are accumulated at EVERY force evaluation in the
            # inherited integrator; NPZ snapshots are saved every 2 ms. They
            # cannot be required to agree. Check the snapshot values against
            # their matching CSV and retain the sampling distinction.
            assert abs(penetration-rows['max_quadrature_penetration_m'].max()) < 1e-14
            assert abs(normal_force-rows['contact_normal_total_N'].max()) < 1e-14
            assert penetration <= summary['max_contact_penetration_m']+1e-12
            assert normal_force <= summary['max_total_contact_normal_N']+1e-12
            assert gradient < .03 and flow_force > 0
        work = sum(rows['work_'+key+'_J'][-1] for key in (
            'magnetic', 'flow', 'contact_dissipative', 'residual_g', 'structural_damping'))
        residual = float(rows['mechanical_energy_J'][-1]-rows['mechanical_energy_J'][0]-work)
        assert abs(residual-summary['energy_work_residual_J']) < 1e-20
        audit = read(folder/'current_constraint_audit.json')
        gain = audit['collocated_gain_A2_per_W']
        if summary['case'].startswith('port_'):
            assert abs(gain-95590.3224538941) < 1e-8
        rod_checks.append(dict(case=summary['case'], trajectory_sha256=sha(folder/'trajectory.npz'),
            tip_rmse_from_raw_positions_m=rmse, maximum_saved_penetration_m=penetration,
            reported_allstep_penetration_m=summary['max_contact_penetration_m'],
            maximum_saved_normal_force_N=normal_force,
            reported_allstep_normal_force_N=summary['max_total_contact_normal_N'],
            maximum_saved_node_gradient_T_per_m=gradient,
            maximum_resultant_flow_force_N=flow_force, maximum_continuous_current_A=current_max,
            ramp_slew_from_raw_endpoints_A_s=slew, continuity_defect_A=continuity,
            mechanical_energy_work_residual_J=residual, gain_A2_per_W=gain,
            optimizer_nonconverged=audit['optimizer_nonconverged'], fallback_count=audit['fallback_count']))

    matched = read(ROD/'matched/model_difference.json')
    assert all(not x['node_gradient_limit_satisfied'] for x in matched['records'])
    assert all(x['true_node_gradient_max_T_per_m'] > .03 for x in matched['records'])
    assert (ROD/'initial_allocator_failure/execution.json').exists()
    assert (ROD/'smoke_failed_api_execution.json').exists()
    interface = read(COIL/'transport_interface_check.json')
    interface_sources = {name: sha(ROOT/name) == value
                         for name, value in interface['source_sha256_at_import'].items()}
    # A later transport-driver edit need not invalidate its recorded historical
    # result. Report identity here; the latest backend run has its own snapshots.
    report = dict(status='independently_executed_postprocessing_pass',
        command=' '.join(sys.argv), source_sha256=sha(Path(__file__)),
        python=sys.version, numpy=np.__version__, elapsed_seconds=time.perf_counter()-started,
        source_checks=source_checks, coil_trajectory_checks=coil_checks,
        rod_trajectory_checks=rod_checks, historical_transport_interface_current_source_matches=interface_sources,
        matched_diagnostic_gradient_limits='All three fixed-bias model-comparison branches exceed .03 T/m; excluded from admissible control evidence.',
        metadata_correction='CoilROM model.omega_rad_s, nu and repeated_frequency_pairs are inherited ideal-uniform-bias reference frequencies used for scaling. They are not the spectrum at a full-coil equilibrium; its existence, linear spectrum and KAM conditions are not certified.',
        scope='Recomputed source identity and constraints/power/trajectory observables from saved raw arrays. No new dynamics integration, no unsampled field bound or clinical validation.')
    destination = ROOT/'stage5/results/physical_evidence_recheck.json'
    destination.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(status=report['status'], source_records=len(source_checks),
        coil_cases=len(coil_checks), rod_cases=len(rod_checks), elapsed_seconds=report['elapsed_seconds']), indent=2))


if __name__ == '__main__':
    main()
