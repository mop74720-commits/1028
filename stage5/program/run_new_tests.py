"""Run each stage5 test module in its documented interpreter and record it.

The Cosserat dependencies and NumPy versions are intentionally isolated from
the learning/AD environment. Each module has a separate process and log.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--learning-python', default='/workspace/1028-cloud/venvs/learning/bin/python')
    parser.add_argument('--rod-python', default='/workspace/1028-cloud/venvs/rod/bin/python')
    parser.add_argument('--pattern', default='test_*.py')
    args = parser.parse_args()
    runid = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'stage5/results/tests' / runid
    out.mkdir(parents=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1',
               NUMBA_CACHE_DIR='/tmp/1028-stage5-rod-numba')
    result = dict(runid=runid, started_utc=datetime.now(timezone.utc).isoformat(), runs=[],
                  source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for folder in ('program', 'tests')
                                 for p in sorted((ROOT / 'stage5' / folder).glob('*.py'))},
                  scope='Module-specific mathematical and interface tests, not completion percentage.')
    for path in sorted((ROOT / 'stage5/tests').glob(args.pattern)):
        interpreter = args.rod_python if path.name == 'test_rod_transfer.py' else args.learning_python
        command = [interpreter, '-m', 'unittest', 'discover', '-s', 'stage5/tests', '-p', path.name, '-v']
        logpath = out / (path.stem + '.log')
        start = time.perf_counter()
        with logpath.open('w') as log:
            completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        record = dict(command=command, cwd=str(ROOT), exit_code=completed.returncode,
                      seconds=time.perf_counter()-start, log=str(logpath.relative_to(ROOT)),
                      status='passed' if completed.returncode == 0 else 'failed')
        result['runs'].append(record)
        (out / 'execution.json').write_text(json.dumps(result, indent=2) + '\n')
        print(path.name, record['status'], round(record['seconds'], 3), flush=True)
    result['status'] = 'passed' if result['runs'] and all(r['exit_code'] == 0 for r in result['runs']) else 'failed'
    result['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (out / 'execution.json').write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'stage5/results/tests/latest.json').write_text(json.dumps(result, indent=2) + '\n')
    if result['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
