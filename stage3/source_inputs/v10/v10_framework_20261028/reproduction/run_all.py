"""Regenerate the mechanical baseline, compensation tests and framework verification."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
for relative in (
    'reproduce_baseline.py',
    'experiments/run_all.py',
    'framework_experiments/run_all.py',
):
    print(f'Running {relative}', flush=True)
    subprocess.run([sys.executable, str(root / relative)], cwd=root, check=True)
