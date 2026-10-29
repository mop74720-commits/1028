"""Package new research artifacts and evidence, excluding upstream repositories."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'stage2'
ARCHIVE = BASE / 'deliverables/1025_v10_stage2_reproducible_bundle.zip'
SKIP_PARTS = {'__pycache__', 'vendor_wheels', 'reference_sources', 'third_party', 'render', 'build', '.venv', 'venv'}
SKIP_SUFFIXES = {'.pyc', '.nbc', '.nbi', '.whl'}
RAW_NOTES = {'v10_main.txt', 'v10_supplement.txt', 'v10_Birkhoff_融合修订与复算说明.txt',
             '1025_stage1_review.txt', '1025_stage1_detailed.md'}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def select():
    selected, excluded = [], []
    for section in ['program', 'results', 'evidence_v10', 'notes', 'report', 'paper']:
        for path in sorted((BASE / section).rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(BASE)
            reason = None
            if any(p in SKIP_PARTS or p.startswith('render_') or p.startswith('cache_') for p in rel.parts):
                reason = 'dependency, cache, duplicate build, or page preview'
            elif path.is_symlink():
                raise RuntimeError(f'Symlink not allowed: {rel}')
            elif path.suffix in SKIP_SUFFIXES:
                reason = 'compiled dependency or cache'
            elif section == 'notes' and path.name in RAW_NOTES:
                reason = 'verbatim extraction of separately supplied original document'
            elif section == 'report' and path.suffix not in {'.md', '.py', '.json', '.log'}:
                reason = 'intermediate document'
            elif 'supplied_replay' in rel.parts:
                replay = path.relative_to(BASE / 'results/route_a/supplied_replay')
                if replay.parts[0] == 'reproduction':
                    source = BASE / 'sources/integration_latest/v10_birkhoff_20261028' / replay
                elif replay.parts[0] == 'birkhoff_supplied':
                    source = BASE / 'sources/birkhoff_supplied' / Path(*replay.parts[1:])
                else:
                    raise RuntimeError(f'Unclassified replay path: {replay}')
                if path.suffix not in {'.json', '.npz', '.csv', '.log', '.svg', '.png', '.txt'}:
                    reason = 'supplied source restored with prepare_inputs.py'
                elif source.is_file() and sha(path) == sha(source):
                    reason = 'unchanged supplied input, not a new result'
            if reason:
                excluded.append({'path': str(path.relative_to(ROOT)), 'reason': reason})
            else:
                selected.append(path)
    for name in ['README.md', 'requirements_route_a.txt', 'requirements_learning.txt',
                 'prepare_inputs.py', 'verify_delivery.py']:
        selected.append(BASE / name)
    for ext in ['docx', 'pdf']:
        selected.append(BASE / f'deliverables/1025_v10_第二阶段融合研究报告.{ext}')
    return sorted(set(selected)), excluded

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory-only', action='store_true')
    args = parser.parse_args()
    files, excluded = select()
    if args.inventory_only:
        print(json.dumps({'files': len(files), 'existing_bytes': sum(p.stat().st_size for p in files if p.exists()),
                          'missing': [str(p.relative_to(ROOT)) for p in files if not p.exists()],
                          'excluded': len(excluded)}, ensure_ascii=False, indent=2))
        return
    selection = BASE / 'notes/bundle_selection.json'
    selection.write_text(json.dumps({'scope': 'New stage-2 programs, outputs, report, bilingual framework, and v10 rerun evidence.',
                                    'original_inputs': 'Obtain the pinned upstream repository/S1 and user ZIPs separately; see README and prepare_inputs.py.',
                                    'excluded': excluded}, ensure_ascii=False, indent=2) + '\n')
    files = sorted(set(files + [selection]))
    manifest = {'format_version': 1, 'scope': 'SHA256 and byte identity of delivered files; not a scientific proof.',
                'self_exclusion': 'delivery_manifest.json is the index and does not hash itself.',
                'files': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files]}
    index = BASE / 'delivery_manifest.json'
    index.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    ARCHIVE.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in files + [index]:
            z.write(path, str(path.relative_to(ROOT)))
    with tempfile.TemporaryDirectory(prefix='stage2_delivery_check_', dir='/tmp') as tmp:
        with zipfile.ZipFile(ARCHIVE) as z:
            bad = z.testzip()
            if bad is not None:
                raise RuntimeError(f'ZIP CRC failure: {bad}')
            z.extractall(tmp)
        result = subprocess.run([sys.executable, str(Path(tmp) / 'stage2/verify_delivery.py')],
                                cwd=tmp, text=True, capture_output=True, check=True)
    print(json.dumps({'archive': str(ARCHIVE), 'files': len(files) + 1,
                      'uncompressed_bytes': sum(p.stat().st_size for p in files + [index]),
                      'archive_bytes': ARCHIVE.stat().st_size, 'archive_sha256': sha(ARCHIVE),
                      'extracted_integrity_check': json.loads(result.stdout)}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
