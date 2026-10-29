"""Verify the user's archived inputs and extract them without replacing sources.

This helper does not download, execute, or modify any upstream material.
It is not needed for the self-contained new 3-D/learning/route-A experiments.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile

BASE = Path(__file__).resolve().parent
INPUTS = {
    'birkhoff': ('c7df06ff2aaaf877f11133c18fca35d07c998b85648375e16bb3b2acbe78809a',
                 'birkhoff_supplied', 'birkhoff_supplied_manifest.json'),
    'latest': ('f809a715ad9e6696c418166db61137cf32d6ea888b39d74d732e8f30fc8c953d',
               'integration_latest', 'integration_latest_manifest.json'),
    'older': ('121fec60cea516667b964bfe4c593492c711c70542c92bddf33d9f7a62c53b81',
              'integration_older_copy2', 'integration_older_copy2_manifest.json'),
}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def tree_matches(directory, expected):
    files = {str(p.relative_to(directory)): p for p in directory.rglob('*') if p.is_file()}
    return (set(files) == set(expected) and
            all(files[k].stat().st_size == v['size'] and sha(files[k]) == v['sha256']
                for k, v in expected.items()))

def prepare(kind, archive):
    expected_sha, folder, manifest = INPUTS[kind]
    if sha(archive) != expected_sha:
        raise ValueError(f'{kind}: archive SHA256 differs from the audited input; no extraction')
    expected = {r['name']: r for r in json.loads((BASE/'notes'/manifest).read_text())}
    target = BASE/'sources'/folder
    if target.exists():
        if not tree_matches(target, expected):
            raise ValueError(f'{target}: existing tree differs; refusing to overwrite it')
        return {'kind': kind, 'status': 'already verified', 'path': str(target)}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='verified_input_', dir=target.parent))
    try:
        with zipfile.ZipFile(archive) as z:
            entries = [r for r in z.infolist() if not r.is_dir()]
            if len(entries) != len(expected) or {r.filename for r in entries} != set(expected):
                raise ValueError('ZIP entry names do not match the audited manifest')
            for item in entries:
                name = PurePosixPath(item.filename)
                if (name.is_absolute() or '..' in name.parts or '\\' in item.filename or
                    ':' in name.parts[0] or stat.S_ISLNK(item.external_attr >> 16)):
                    raise ValueError('Non-regular or unsafe ZIP entry: ' + item.filename)
                record = expected[item.filename]
                if item.file_size != record['size']:
                    raise ValueError('ZIP entry size differs: ' + item.filename)
                destination = temporary.joinpath(*name.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with z.open(item) as src, destination.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
                if sha(destination) != record['sha256']:
                    raise ValueError('ZIP entry SHA256 differs: ' + item.filename)
        temporary.rename(target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {'kind': kind, 'status': 'verified and extracted', 'path': str(target)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in INPUTS:
        parser.add_argument('--'+name, type=Path)
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error('Provide at least one of --birkhoff, --latest, --older')
    for name in INPUTS:
        if getattr(args, name) is not None:
            print(json.dumps(prepare(name, getattr(args, name)), ensure_ascii=False))

if __name__ == '__main__':
    main()
