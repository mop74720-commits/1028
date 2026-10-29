"""Execute the 23 frozen stage3 tests in an ordinary external copy.

Some legacy tests write diagnostic JSON. No symlink or source checkout is used
as their working directory. These are retained regressions, not stage5 coverage.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default='/workspace/1028-cloud/venvs/learning/bin/python')
    args = parser.parse_args()
    out = ROOT / 'stage5/results/regression'
    out.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='1028-stage5-regression-'))
    shutil.copytree(ROOT / 'stage3', scratch / 'stage3', ignore=shutil.ignore_patterns('__pycache__', 'install.sh'))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1')
    command = [args.python, '-m', 'unittest', 'discover', '-s', 'stage3/tests', '-v']
    started = time.perf_counter()
    record = dict(command=command, cwd=str(scratch), started_utc=datetime.now(timezone.utc).isoformat(),
                  scope='18 direct legacy tests and 5 saved-evidence acceptances; does not regenerate legacy experiments',
                  interpreter=args.python, source_commit='f3aa09c6449ff6d0ff732f2b19a4f65c6dcf4cda')
    with (out / 'legacy_23.log').open('w') as log:
        result = subprocess.run(command, cwd=scratch, env=env, stdout=log, stderr=subprocess.STDOUT)
    snapshot = json.loads((ROOT / 'stage5/results/start_provenance.json').read_text())
    differences = [name for name, sha in snapshot['frozen_files'].items()
                   if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha]
    record.update(exit_code=result.returncode, seconds=time.perf_counter()-started,
                  finished_utc=datetime.now(timezone.utc).isoformat(), frozen_differences=differences,
                  status='passed' if result.returncode == 0 and not differences else 'failed',
                  log='stage5/results/regression/legacy_23.log', scratch_retained_for_inspection=True)
    (out / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)
    if result.returncode or differences:
        sys.exit(1)


if __name__ == '__main__':
    main()
