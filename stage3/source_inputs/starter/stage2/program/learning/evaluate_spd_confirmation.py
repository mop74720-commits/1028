"""Freeze the two SPD checkpoints, then evaluate fresh confirmation data only.

No optimizer, training or checkpoint selection is performed here.  All inputs
and outputs belong to the separate SPD experiment; older results stay intact.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import time

import numpy as np
import torch

from rod_rom import RodROM
from train_spd_complex import MechanicalComplexResidual
from run_learning import network_prediction, scores
from evaluate_models import grad_metrics, row_set


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run(args):
    start = time.perf_counter()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parent
    groups = [('main', 'local', 'learning', .08), ('stress', 'stress', 'learning_stress', .35)]
    manifests = []
    for group, trained_dir, old_dir, amp in groups:
        checkpoint = args.spd_root/trained_dir/'spd_complex_seed1025.pt'
        summary = args.spd_root/trained_dir/'learning_summary.json'
        if not checkpoint.exists() or not summary.exists():
            raise RuntimeError('Both training runs must finish before freezing either confirmation evaluation.')
        record = json.loads(summary.read_text())
        if sha(checkpoint) != record['checkpoint_sha256'] or record['amplitude'] != amp:
            raise ValueError('Checkpoint differs from the validation-selected training result.')
        manifests.append({'group': group, 'amplitude': amp, 'checkpoint': str(checkpoint),
                          'checkpoint_sha256': sha(checkpoint), 'training_summary': str(summary),
                          'training_summary_sha256': sha(summary),
                          'best_validation_step': record['best_validation_step']})
    freeze_path = out/'freeze_manifest.json'
    if freeze_path.exists():
        raise RuntimeError('Confirmation already frozen; use a new destination rather than overwrite evidence.')
    for item in manifests:
        target = out/'frozen'/item['group']/'spd_complex_seed1025.pt'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item['checkpoint'], target)
        item['frozen_checkpoint'] = str(target)
    freeze = {
        'frozen_utc_before_opening_confirmation_labels': now(),
        'scope': 'Two predeclared SPD models, selected by existing validation only; fresh data were generated independently before this evaluation.',
        'confirmation_data_preexisted_freeze': True,
        'training_or_tuning_performed': False,
        'checkpoints': manifests,
        'source_sha256': {name: sha(source/name) for name in ['train_spd_complex.py', 'evaluate_spd_confirmation.py', 'rod_rom.py', 'run_learning.py', 'evaluate_models.py']},
        'rule': 'Evaluate both frozen checkpoints, test and OOD. No architecture, hyperparameter, seed or step selection from these results.',
    }
    freeze_path.write_text(json.dumps(freeze, indent=2)+'\n')
    print(json.dumps({'stage': 'frozen_before_confirmation_labels', 'manifest_sha256': sha(freeze_path)}), flush=True)

    model = RodROM(config_path=args.confirmation_root/'frozen/config.json')
    results = {}
    for group, trained_dir, old_dir, amp in groups:
        record = next(r for r in manifests if r['group'] == group)
        checkpoint_path = Path(record['frozen_checkpoint'])
        state = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
        if state['n'] != model.n or state['amplitude'] != amp:
            raise ValueError('Checkpoint coordinate dimension or amplitude mismatch.')
        with np.load(args.confirmation_root/'frozen/models'/group/'rom_matrices.npz') as matrix:
            identities = {key: bool(np.array_equal(matrix[key], current)) for key, current in {
                'M0': model.M0.numpy(), 'K0': model.K0, 'Sq': model.Sq.numpy(),
                'Sp': model.Sp.numpy(), 'nu': model.nu.numpy(), 'omega': model.omega}.items()}
        if not all(identities.values()):
            raise ValueError('Confirmation ROM chart is not the fixed training chart.')
        net = MechanicalComplexResidual(state['n'], state['width'], state['amplitude'], state['output_scale'])
        net.load_state_dict(state['state_dict'])
        net.eval()
        data_path = args.confirmation_root/group/'confirmation_data.npz'
        dataset_manifest = json.loads((args.confirmation_root/group/'dataset_manifest.json').read_text())
        data_hash = sha(data_path)
        if data_hash != dataset_manifest['data_sha256'] or dataset_manifest['amplitude'] != amp:
            raise ValueError('Confirmation data changed or amplitude metadata disagree.')
        raw = np.load(data_path)
        sets = {split: {key: raw[split+'_'+key] for key in ['x', 'h_res', 'g_res', 'q_raw', 'tip_m']}
                for split in ['test', 'ood']}
        old_data = np.load(args.spd_root.parent/old_dir/'learning_data.npz')
        prior_rows = {name: row_set(old_data[name+'_x']) for name in ['train', 'validation', 'test', 'ood']}
        intersections = {split: {name: len(row_set(data['x']) & rows) for name, rows in prior_rows.items()}
                         for split, data in sets.items()}
        if any(n for old in intersections.values() for n in old.values()):
            raise ValueError('Confirmation row overlap detected.')
        scale = np.sqrt(np.r_[model.nu.numpy(), model.nu.numpy()])/amp
        row = {
            'group': group, 'amplitude': amp, 'seed': 1025,
            'checkpoint_sha256': sha(checkpoint_path), 'data_sha256': data_hash,
            'sampling_seed': dataset_manifest['sampling_seed'],
            'freeze_manifest_sha256': sha(freeze_path), 'training_or_checkpoint_selection': False,
            'model_chart_exact_identity': identities,
            'split_counts': {split: len(data['x']) for split, data in sets.items()},
            'old_data_exact_row_intersections': intersections, 'splits': {},
        }
        for split, data in sets.items():
            ph, pg = network_prediction(net, data['x'])
            metrics = grad_metrics(pg, data, amp, scale, model.Sq.numpy(), model.omega0, model.E0)
            metrics.update(scores(ph, pg, data, amp))
            metrics['physical_energy_rmse_J'] = model.E0*metrics['energy_rmse']
            row['splits'][split] = metrics
            np.savez_compressed(out/f'{group}_{split}_predictions.npz', h_res=ph, g_res=pg)
        unrestricted = json.loads((args.confirmation_root/group/'confirmation_summary.json').read_text())
        row['same_seed_unrestricted_confirmation'] = next(r for r in unrestricted['complex_checkpoints'] if r['seed'] == 1025)
        row['baseline_confirmation'] = unrestricted['baselines']
        if sha(checkpoint_path) != record['checkpoint_sha256'] or sha(data_path) != data_hash:
            raise RuntimeError('Frozen weights or confirmation data changed during evaluation.')
        row['evaluation_completed_utc'] = now()
        row['interpretation_limits'] = [
            'One predeclared seed; no robustness conclusion over initialization or model-family search.',
            'This is confirmation on newly sampled synthetic states of the same 12-DoF ROM, not physical experiment or full Cosserat validation.',
            'Positive mass and a valid momentum Legendre inverse do not prove accurate forces, integration convergence, closed-loop stability or KAM.',
        ]
        (out/f'{group}_summary.json').write_text(json.dumps(row, indent=2)+'\n')
        results[group] = row
        print(json.dumps({'group': group, 'splits': row['splits']}), flush=True)
    completion = {'elapsed_seconds': time.perf_counter()-start, 'completed_utc': now(),
                  'all_checkpoints_unchanged': all(sha(r['checkpoint']) == r['checkpoint_sha256'] for r in manifests),
                  'groups': {group: {'summary': str(out/f'{group}_summary.json'),
                                     'checkpoint_sha256': row['checkpoint_sha256']} for group, row in results.items()}}
    (out/'completion.json').write_text(json.dumps(completion, indent=2)+'\n')
    print(json.dumps(completion), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spd-root', type=Path, default=Path('stage2/results/learning_spd'))
    parser.add_argument('--confirmation-root', type=Path, default=Path('stage2/results/learning_confirmation'))
    parser.add_argument('--output', type=Path, default=Path('stage2/results/learning_spd/confirmation'))
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    run(args)
