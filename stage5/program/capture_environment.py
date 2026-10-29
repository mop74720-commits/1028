"""Record the two actual interpreters; contains no credentials or setup draft."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--learning-python', default='/workspace/1028-cloud/venvs/learning/bin/python')
    parser.add_argument('--rod-python', default='/workspace/1028-cloud/venvs/rod/bin/python')
    args = parser.parse_args()
    probe = '''import importlib.metadata as m,json,platform,sys
print(json.dumps(dict(executable=sys.executable,python=sys.version,platform=platform.platform(),
                     packages={d.metadata['Name']:d.version for d in m.distributions()}),sort_keys=True))
'''
    result = dict(recorded_utc=datetime.now(timezone.utc).isoformat(), interpreters={})
    for name, interpreter in [('learning', args.learning_python), ('rod', args.rod_python)]:
        completed = subprocess.run([interpreter, '-c', probe], check=True, text=True, capture_output=True)
        result['interpreters'][name] = json.loads(completed.stdout)
    result['thread_settings'] = dict(PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
                                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1')
    result['scope'] = 'Dependency inventory, not environment provisioning or a reproducibility guarantee across hardware.'
    out = ROOT / 'stage5/results/environment.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
