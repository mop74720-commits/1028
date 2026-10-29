"""Compare actual old/new 36D sampled maps without overwriting either run."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'stage5/results/closed_loop'
NEW = BASE / 'sampled_warmfix'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--new-output', type=Path, default=NEW)
    args = parser.parse_args()
    destination = args.new_output.resolve()
    old = json.loads((BASE / 'sampled_jacobian.json').read_text())
    new = json.loads((destination / 'sampled_jacobian.json').read_text())
    assert old['status'] == new['status'] == 'completed'
    old_npz = np.load(BASE / 'sampled_jacobians.npz')
    new_npz = np.load(destination / 'sampled_jacobians.npz')
    retained_old_sources = {
        'stage5/program/run_closed_loop_sampled.py': BASE / 'source_before_sampled_output_option.py',
        'stage5/program/closed_loop_sampled.py': ROOT / 'stage5/program/closed_loop_sampled.py',
        'stage5/program/coil_control.py': ROOT / 'stage5/results/coil/source_before_force_warm_fix_coil_control.py',
        'stage5/program/coil_rom.py': ROOT / 'stage5/results/coil/source_before_higher_ad_fix.py'}
    for source, snapshot in retained_old_sources.items():
        assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == old['source_sha256'][source], source
    rows = []
    for old_row, new_row in zip(old['runs'], new['runs']):
        kind = old_row['kind']
        assert kind == new_row['kind']
        for key in ('interval_tau', 'RK4_substeps', 'gamma', 'finite_difference_epsilon'):
            assert old_row[key] == new_row[key], key
        assert np.array_equal(old_npz[kind + '_initial'], new_npz[kind + '_initial'])
        old_jac = old_npz[kind + '_jacobian']
        new_jac = new_npz[kind + '_jacobian']
        difference = new_jac - old_jac
        final_difference = new_npz[kind + '_final'] - old_npz[kind + '_final']
        rows.append(dict(
            kind=kind, original_initial_state_and_protocol_identical=True,
            actual_fixed_total_bias_current_A=new_npz[kind + '_initial'][24:].tolist(),
            bias_metadata='For the matched run both model.bias_currents and model.bias_currents_tensor were set to these exact saved currents before evaluating either map; this is the old fixed local-bias fit, not the newly refitted rounding variant.',
            Jacobian_change_spectral_norm=float(np.linalg.norm(difference, 2)),
            Jacobian_change_relative_frobenius=float(np.linalg.norm(difference) / np.linalg.norm(old_jac)),
            mechanical_block_change_spectral_norm=float(np.linalg.norm(difference[:24, :24], 2)),
            current_memory_block_change_spectral_norm=float(np.linalg.norm(difference[24:, :], 2)),
            actual_final_state_change_norm=float(np.linalg.norm(final_difference[:24])),
            actual_final_current_change_norm_A=float(np.linalg.norm(final_difference[24:])),
            old_rank=old_row['numerical_rank_relative_1e_8'], new_rank=new_row['numerical_rank_relative_1e_8'],
            old_condition=old_row['full_augmented_jacobian_condition'], new_condition=new_row['full_augmented_jacobian_condition'],
            old_mechanical_K0_defect=old_row['conditional_mechanical_canonical_defect_2'],
            new_mechanical_K0_defect=new_row['conditional_mechanical_canonical_defect_2'],
            old_active_box_signature=old_row['active_box_signature'],
            new_active_box_signature=new_row['active_box_signature'],
            old_probe_signature_changes=old_row['active_signature_changes_in_72_coordinate_probes'],
            new_probe_signature_changes=new_row['active_signature_changes_in_72_coordinate_probes'],
            old_directional_checks=old_row['directional_checks'],
            new_directional_checks=new_row['directional_checks']))
    report = dict(
        status='actual_new_allocator_map_recomputed_and_compared',
        command=[sys.executable, *sys.argv], rows=rows,
        old_sources=old['source_sha256'], new_sources=new['source_sha256'],
        old_exact_source_locations={source: str(snapshot.relative_to(ROOT))
                                    for source, snapshot in retained_old_sources.items()},
        implementation_changes='Force-allocation warm start uses the feasible previous current; '
                               'coil distance norm is algebraically rewritten to support high AD. '
                               'The physical sampled-map protocol, constraints and tolerances are unchanged.',
        new_sources_unchanged_during_run=new['source_unchanged_during_run'],
        result_sha256={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                       for folder in (BASE, destination)
                       for path in (folder / 'sampled_jacobian.json', folder / 'sampled_jacobians.npz')},
        active_signature_limit='Old results retained only base signature and changed-probe count. '
                               'The new result additionally saves all 72 coordinate probe signatures; '
                               'full old/new per-probe signature comparison is unavailable.',
        interpretation='Both Jacobians belong to the actual 36D sampled map including current memory, '
                       'allocation and current ramps. Neither is declared a Hamiltonian/symplectic map. '
                       'A finite-difference matrix is not a neighborhood smoothness proof. '
                       'Condition numbers and relative-threshold numerical ranks use the reported '
                       'scaled Q,P and current-in-A coordinates and depend on this coordinate scaling.')
    (destination / 'version_comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
