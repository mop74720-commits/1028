"""Independent reruns on a disposable copy; never rewrite frozen stage3 files.

The copied long-window interruption record is explicitly historical. New output
directories are removed from the copy before their generators run, preventing
old successful JSON from being mistaken for freshly completed calculations.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import time

REPO=Path(__file__).resolve().parents[3]
AUDIT=REPO/'stage4/audit'
SOURCE=REPO/'stage3'
PYTHON=Path('/workspace/1028-cloud/venvs/learning/bin/python')
SCRATCH_BASE=Path('/workspace/1028-stage4-runs')
SCRATCH_BASE.mkdir(exist_ok=True)
RUN=Path(tempfile.mkdtemp(prefix='reproduction-',dir=SCRATCH_BASE))
COPY=RUN/'stage3'
DELIVERED=RUN/'delivered/stage3'
LOGS=AUDIT/'logs/reproduction'
OUTPUT=AUDIT/'results'
LOGS.mkdir(parents=True,exist_ok=True);OUTPUT.mkdir(parents=True,exist_ok=True)

def utc():return datetime.now(timezone.utc).isoformat()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def source_inventory():
    return {str(p.relative_to(SOURCE)):sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}

baseline=source_inventory()
shutil.copytree(SOURCE,COPY,ignore=shutil.ignore_patterns('__pycache__','*.pyc','install.sh'))
shutil.copytree(SOURCE,DELIVERED,ignore=shutil.ignore_patterns('__pycache__','*.pyc','install.sh'))
# Keep this one record only for the historical-status regression test. It is
# never listed among newly computed scientific outputs in this audit.
long_record=(COPY/'results/birkhoff/results_T0.004.json').read_bytes()
for name in ('integrators','birkhoff','control','control_learning'):
    shutil.rmtree(COPY/'results'/name)
(COPY/'results/birkhoff').mkdir()
(COPY/'results/birkhoff/results_T0.004.json').write_bytes(long_record)
ENV=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
         NUMBA_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',MPLBACKEND='Agg',
         MPLCONFIGDIR=str(SCRATCH_BASE/'cache/matplotlib'),
         XDG_CACHE_HOME=str(SCRATCH_BASE/'cache'),NUMBA_CACHE_DIR=str(SCRATCH_BASE/'cache/numba'))

version_cmd=[str(PYTHON),'-c',"import json,platform,importlib.metadata as m; print(json.dumps({'python':platform.python_version(),'packages':{p:m.version(p) for p in ['numpy','scipy','torch','matplotlib','sympy']}}))"]
versions=json.loads(subprocess.check_output(version_cmd,env=ENV,text=True))
report=dict(started_at=utc(),source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            original_source_root=str(SOURCE),scratch_root=str(RUN),environment=versions,
            thread_settings={k:ENV[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','PYTHONDONTWRITEBYTECODE']},
            runs=[],fresh_outputs=[],historical_copied_records=['birkhoff/results_T0.004.json'],
            tolerances={'implicit_increment_inf':2e-13,'integrator_reference':[[2e-11,2e-13],[5e-13,5e-15]],
                        'birkhoff_reference':[[2e-10,2e-12],[5e-12,5e-14]],
                        'birkhoff_max_step_refinement':['T/8','T/16'],
                        'control':'RK4 8/16 steps on tau=.004; this is a refinement observation, not an implicit residual tolerance'})

def execute(name,args,cwd,expected=()):
    start=time.monotonic();wall_start=time.time_ns()
    record=dict(name=name,command=[str(PYTHON),*args],cwd=str(cwd),started_at=utc(),
                log=str((LOGS/(name+'.log')).relative_to(REPO)))
    with (LOGS/(name+'.log')).open('w') as log:
        completed=subprocess.run(record['command'],cwd=cwd,env=ENV,stdout=log,stderr=subprocess.STDOUT)
    record.update(exit_code=completed.returncode,ended_at=utc(),seconds=time.monotonic()-start,
                  status='passed' if completed.returncode==0 else 'failed')
    text=(LOGS/(name+'.log')).read_text(errors='replace')
    match=re.search(r'Ran (\d+) tests? in',text)
    if match:
        record['test_count']=int(match.group(1))
        record['skipped']=int(re.search(r'skipped=(\d+)',text).group(1)) if re.search(r'skipped=(\d+)',text) else 0
        record['runner_outcome']=text.strip().splitlines()[-1]
    record['expected_outputs']=[]
    for relative in expected:
        p=COPY/'results'/relative
        data=dict(path=relative,present=p.is_file())
        if p.is_file():data.update(sha256=sha(p),modified_after_command_started=p.stat().st_mtime_ns>=wall_start,bytes=p.stat().st_size)
        record['expected_outputs'].append(data)
        if not data['present'] or not data.get('modified_after_command_started',False):
            record['status']='failed_output_freshness'
    if completed.returncode:
        record['failure_tail']=text.splitlines()[-30:]
    print(json.dumps(record,ensure_ascii=False),flush=True)
    return record

# This first run re-executes the tests, but saved-result tests still inspect the
# delivered evidence. The final run below also sees newly regenerated outputs.
report['runs'].append(execute('original_23_tests',['-m','unittest','discover','-s','stage3/tests','-v'],DELIVERED.parent))

def integration_group():
    records=[]
    records.append(execute('fresh_integrators',['stage3/program/run_integrators.py'],RUN,
          ['integrators/integrators.json','integrators/integrators_traces.npz','integrators/integrators.csv']))
    records.append(execute('window_diagnostic',['stage3/program/diagnose_birkhoff_window.py'],RUN,
          ['birkhoff/window_diagnostic.json']))
    return records

def birkhoff_control_group():
    records=[]
    for name,args,expected in [
        ('fresh_local_birkhoff',['stage3/program/run_birkhoff.py','--duration','.0005'],['birkhoff/results_T0.0005.json','birkhoff/trajectories_T0.0005.npz','birkhoff/metrics_T0.0005.csv']),
        ('fresh_control',['stage3/program/control_experiments.py'],['control/control_results.json','control/trajectories.npz','control/control_summary.csv']),
        ('fresh_coil_force',['stage3/program/control_coil_force.py'],['control/full_coil_force_audit.json']),
        ('fresh_quadrature',['stage3/program/control_quadrature.py'],['control/port_quadrature_rank.json']),
        ('fresh_analytic_learning',['stage3/program/control_learning.py'],['control_learning/learning_results.json','control_learning/learning_data_and_trajectories.npz']),
    ]:records.append(execute(name,args,RUN,expected))
    return records

with ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(integration_group),pool.submit(birkhoff_control_group)]
    for future in futures:
        report['runs'].extend(future.result())
        (OUTPUT/'reproduction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

report['runs'].append(execute('fresh_23_tests',['-m','unittest','discover','-s','stage3/tests','-v'],RUN))
saved=OUTPUT/'reproduced'
saved.mkdir(exist_ok=True)
for folder in ('integrators','birkhoff','control','control_learning'):
    shutil.copytree(COPY/'results'/folder,saved/folder,dirs_exist_ok=True)
    for p in sorted((saved/folder).rglob('*')):
        if p.is_file() and p.name!='results_T0.004.json':
            report['fresh_outputs'].append(dict(path=str(p.relative_to(REPO)),sha256=sha(p),bytes=p.stat().st_size))
for name in ('rom_bridge.json','birkhoff_identity_checks.json'):
    p=saved/name
    shutil.copy2(COPY/'results'/name,p)
    report['fresh_outputs'].append(dict(path=str(p.relative_to(REPO)),sha256=sha(p),bytes=p.stat().st_size))
report['source_unchanged']=baseline==source_inventory()
report['source_files_hashed']=len(baseline)
report['source_manifest_sha256']=hashlib.sha256(json.dumps(baseline,sort_keys=True).encode()).hexdigest()
report['ended_at']=utc()
report['status']='all_selected_reruns_passed' if report['source_unchanged'] and all(r['status']=='passed' for r in report['runs']) else 'failures_recorded'
(OUTPUT/'reproduction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUTPUT/'stage3_source_hashes.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n')
print(report['status'],flush=True)
raise SystemExit(0 if report['status']=='all_selected_reruns_passed' else 1)
