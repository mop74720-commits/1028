"""Verify and extract the supplied fusion archive outside frozen repository inputs."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import argparse
from datetime import datetime, timezone
import hashlib
import json
import stat
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'stage6/fusion_reconciliation'
ARCHIVE = ROOT / 'stage3/source_inputs/v10/v10_birkhoff_20261028_no_fonts_for_github.zip'
EXPECTED = '416bdb3c8337816c9ef041bcaa5d5a4b8a8276c6d7be6172e37a0dec0dd9ec7f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_archive():
    """Byte-verified new temporary extraction; never execute archive programs."""
    assert sha(ARCHIVE) == EXPECTED
    target = Path(tempfile.mkdtemp(prefix='1028-stage6-fusion-', dir='/tmp'))
    entries = []
    with ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        for info in z.infolist():
            rel = PurePosixPath(info.filename)
            if rel.is_absolute() or '..' in rel.parts or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Unsupported archive path/type: '+info.filename)
            dest = target / str(rel)
            if info.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                continue
            data = z.read(info)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            assert sha(dest) == digest
            entries.append(dict(path=info.filename, bytes=info.file_size, crc32=f'{info.CRC:08x}', sha256=digest))
    return target, entries


def resolve_source():
    """Find this run's scratch source, or recover it on a fresh checkout.

    The committed starting manifest is never rewritten. Recovery uses a new
    temporary directory and a separate local pointer under stage6/results.
    """
    out = BASE/'results'
    original = json.loads((out/'materials.json').read_text())
    for record in [out/'local_extraction.json', out/'materials.json']:
        if not record.exists():
            continue
        path = Path(json.loads(record.read_text())['manuscript_root'])
        if path.is_dir() and all((path.parent/e['path']).exists() and
                               sha(path.parent/e['path']) == e['sha256'] for e in original['entries']):
            return path
    target, entries = extract_archive()
    assert entries == original['entries']
    path = target/'v10_birkhoff_20261028'
    (out/'local_extraction.json').write_text(json.dumps(dict(manuscript_root=str(path),
        archive_sha256=EXPECTED, recovered_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
    return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--verify-frozen', action='store_true')
    p.add_argument('--extract-only', action='store_true')
    args = p.parse_args()
    out = BASE / 'results'
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / 'materials.json'
    if args.extract_only:
        print(resolve_source())
        return
    if args.verify_frozen:
        original = json.loads(manifest.read_text())
        changed = [name for name, value in original['frozen_sha256'].items()
                   if not (ROOT/name).exists() or sha(ROOT/name) != value]
        report = dict(status='passed' if not changed else 'failed', changed=changed,
                      frozen_files=len(original['frozen_sha256']), checked_utc=datetime.now(timezone.utc).isoformat())
        (out/'frozen_preservation.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report)); assert not changed
        return
    if manifest.exists():
        raise FileExistsError('Preserve original provenance; use --verify-frozen')
    target, entries = extract_archive()
    tracked = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0')
    report = dict(status='verified_and_extracted', started_utc=datetime.now(timezone.utc).isoformat(),
                  start_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
                  source_branch='stage5/unified-3d-repairs', archive=str(ARCHIVE.relative_to(ROOT)),
                  archive_sha256=EXPECTED, bytes=ARCHIVE.stat().st_size, crc='all_passed', entries=entries,
                  temporary_extraction_root=str(target), manuscript_root=str(target/'v10_birkhoff_20261028'),
                  frozen_sha256={name:sha(ROOT/name) for name in tracked if name and not name.startswith('stage6/')},
                  scope='Archive/input provenance only; not mathematical acceptance of manuscript claims.')
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['start_head','branch','archive_sha256','temporary_extraction_root','manuscript_root']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
