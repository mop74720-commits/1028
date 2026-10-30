"""Rerun the supplied historical baseline/control suites in a disposable copy.

This never writes into the extracted archive or the frozen repository inputs.
The archived two-mode objects remain historical regressions, not new 3D results.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'stage6/fusion_reconciliation'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--python', default='/workspace/1028-cloud/venvs/learning/bin/python')
    p.add_argument('--run-id', default='fusion_original_reproduction')
    args = p.parse_args()
    from materials import resolve_source
    source = resolve_source()/'reproduction'
    out = BASE/'results/history'/args.run_id
    if out.exists(): raise FileExistsError(out)
    out.mkdir(parents=True)
    scratch = Path(tempfile.mkdtemp(prefix='1028-stage6-history-', dir='/tmp'))
    copied = scratch/'reproduction'
    shutil.copytree(source, copied)
    source_hashes = {str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in source.rglob('*') if p.is_file()}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1')
    report = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                  source_root=str(source), scratch=str(scratch), commands=[],
                  source_sha256=source_hashes,
                  scope='Fresh reruns of supplied 2-DOF/linear algorithm regressions; not 3D generalization, CHNN training or KAM certification.')
    save=lambda:(out/'execution.json').write_text(json.dumps(report, indent=2)+'\n')
    save()
    for name in ['verify_baseline.py','experiments/minimal_control_loop.py',
                 'experiments/route_b_shared_data.py','experiments/damping_sensitivity.py',
                 'experiments/summarize_results.py','framework_experiments/run_all.py']:
        start=time.perf_counter();command=[args.python,str(copied/name)]
        log=out/(name.replace('/','__')+'.log')
        with log.open('w') as stream:
            result=subprocess.run(command,cwd=copied,env=env,stdout=stream,stderr=subprocess.STDOUT)
        report['commands'].append(dict(command=command,cwd=str(copied),exit_code=result.returncode,
            seconds=time.perf_counter()-start,status='passed' if result.returncode==0 else 'failed',
            log=str(log.relative_to(ROOT))))
        save();print(name,report['commands'][-1]['status'],flush=True)
        if result.returncode:
            report['status']='failed';break
    else:report['status']='completed'
    outputs=['baseline_reverification.json','experiments/minimal_control_results.json',
             'experiments/route_b_shared_results.json','experiments/damping_sensitivity_results.json',
             'experiments/control_audit_summary.json','framework_experiments/matrix_structure_results.json',
             'framework_experiments/closed_loop_convergence_results.json',
             'framework_experiments/closed_loop_convergence_traces.npz',
             'framework_experiments/algebraic_defect_results.json',
             'framework_experiments/nonlinear_weighted_results.json']
    for name in outputs:
        # Complete successful reruns can be byte-identical (the framework is
        # deterministic). Preserve those actual outputs too; after failure only
        # changed outputs are exported and command status identifies coverage.
        path=copied/name
        if path.exists() and (report['status']=='completed' or hashlib.sha256(path.read_bytes()).hexdigest()!=source_hashes.get(name)):
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    report['source_unchanged']=all(hashlib.sha256((source/name).read_bytes()).hexdigest()==digest
        for name,digest in source_hashes.items())
    assert report['source_unchanged']
    report['finished_utc']=datetime.now(timezone.utc).isoformat();save()
    if report['status']!='completed': raise SystemExit(1)


if __name__=='__main__':main()
