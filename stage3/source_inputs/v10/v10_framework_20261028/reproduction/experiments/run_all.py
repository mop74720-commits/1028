"""Reproduce the new control tests in their required dependency order."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
env = dict(os.environ)
env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
           MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
for script in ['minimal_control_loop.py', 'route_b_shared_data.py',
               'damping_sensitivity.py', 'summarize_results.py']:
    print('Running', script, flush=True)
    subprocess.run([sys.executable, str(ROOT/script)], cwd=ROOT, env=env, check=True)
