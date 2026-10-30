"""Run old and new tests without writing old result directories."""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,time,shutil,tempfile

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--suite',choices=['previous','current','all'],default='all')
    p.add_argument('--learning-python',default='/workspace/1028-cloud/venvs/learning/bin/python')
    p.add_argument('--rod-python',default='/workspace/1028-cloud/venvs/rod/bin/python')
    args=p.parse_args()
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out=BASE/'results/tests'/run_id;out.mkdir(parents=True)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
        MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_CACHE_DIR='/tmp/1028-stage6-numba')
    suites=[]
    if args.suite in ('previous','all'):
        # Legacy tearDownClass methods write fixed result paths. Execute byte
        # copies in an independent tree; never allow those writes in ROOT.
        scratch=Path(tempfile.mkdtemp(prefix='1028-s6-legacy-tests-'))
        for name in ('stage3','stage4','stage5'):
            shutil.copytree(ROOT/name,scratch/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','install.sh'))
        suites.append((scratch/'stage5/tests',scratch))
    if args.suite in ('current','all'):suites.append((BASE/'tests',ROOT))
    report=dict(status='running',command=[*__import__('sys').argv],started_utc=datetime.now(timezone.utc).isoformat(),
        runs=[],source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in [BASE/'program',BASE/'tests',ROOT/'stage5/program',ROOT/'stage5/tests']
            for p in sorted(folder.glob('*.py'))},scope='Tests of declared formulas/interfaces; neither test count nor passing establishes complete robot or KAM validation.')
    for directory,execution_root in suites:
        for path in sorted(directory.glob('test_*.py')):
            python=args.rod_python if path.name=='test_rod_transfer.py' else args.learning_python
            command=[python,'-m','unittest','discover','-s',str(directory.relative_to(execution_root)),'-p',path.name,'-v']
            log=out/(directory.parent.name+'_'+path.stem+'.log');start=time.perf_counter()
            with log.open('w') as stream:
                result=subprocess.run(command,cwd=execution_root,env=env,stdout=stream,stderr=subprocess.STDOUT)
            output=log.read_text();match=re.search(r'Ran (\d+) tests?',output)
            report['runs'].append(dict(command=command,cwd=str(execution_root),status='passed' if result.returncode==0 else 'failed',
                exit_code=result.returncode,seconds=time.perf_counter()-start,tests=int(match[1]) if match else None,
                log=str(log.relative_to(ROOT))))
            (out/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
            print(str(path.relative_to(execution_root)),report['runs'][-1]['status'],flush=True)
    if args.suite in ('previous','all'):
        produced=out/'legacy_results';produced.mkdir()
        for name in ('closed_loop/independent_checks.json','rod_transfer/operator_tests.json'):
            source=scratch/'stage5/results'/name
            shutil.copy2(source,produced/Path(name).name)
        report['legacy_isolation']=dict(directory=str(scratch),outputs=str(produced.relative_to(ROOT)),
            reason='Frozen legacy tests contain fixed-path output side effects; run in independent copies.')
    report.update(status='passed' if report['runs'] and all(x['exit_code']==0 for x in report['runs']) else 'failed',
        finished_utc=datetime.now(timezone.utc).isoformat(),total_tests=sum(x['tests'] or 0 for x in report['runs']))
    (out/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
    (BASE/'results/tests'/f'latest_{args.suite}.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
