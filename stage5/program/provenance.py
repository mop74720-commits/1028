"""Read-only provenance for the stage5 experiment inputs; writes only stage5."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'stage5/results'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    inputs = {p: sha(ROOT / p) for p in tracked if p and not p.startswith('stage5/')}
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).strip()
    inventory = json.loads((ROOT / 'stage3/results/material_inventory.json').read_text())
    archives = []
    for item in inventory['archives']:
        with ZipFile(ROOT / item['path']) as archive:
            for entry in item['entries']:
                data = archive.read(entry['path'])
                assert data == (ROOT / item['extracted_root'] / entry['path']).read_bytes()
        archives.append(dict(path=item['path'], sha256=sha(ROOT / item['path']),
                             matched_entries=len(item['entries']), crc='passed'))
    matrix = list(csv.DictReader((ROOT / 'stage4/audit/full_inheritance_matrix.csv').open(encoding='utf-8-sig')))
    assert len(matrix) == 115 and len({r['id'] for r in matrix}) == 115
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(), start_head=head,
                  remote_main=remote, branch=subprocess.check_output(
                      ['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
                  python=platform.python_version(), frozen_files=inputs, archives=archives,
                  inheritance_ids=[r['id'] for r in matrix],
                  preserved_local_draft='stage3/install.sh; not part of stage5 delivery',
                  scope='File identity and provenance, not proof of scientific validity.')
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'start_provenance.json'
    if path.exists():
        raise FileExistsError('Do not replace the experiment start snapshot; use --verify')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(start_head=head, frozen_files=len(inputs), archives=archives), ensure_ascii=False))


def verify():
    original = json.loads((OUT / 'start_provenance.json').read_text())
    changed = [p for p, h in original['frozen_files'].items()
               if not (ROOT / p).exists() or sha(ROOT / p) != h]
    report = dict(checked_utc=datetime.now(timezone.utc).isoformat(),
                  frozen_files=len(original['frozen_files']), changed=changed,
                  status='passed' if not changed else 'failed')
    (OUT / 'frozen_preservation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    assert not changed, changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    verify() if args.verify else capture()
