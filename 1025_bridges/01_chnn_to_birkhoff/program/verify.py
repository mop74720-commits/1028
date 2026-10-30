"""Run only bridge tests and directly reused learning/transport regressions."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys,time

BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]


def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out=BASE/'results'/('verification_'+stamp);out.mkdir()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report=dict(command=sys.argv,python=sys.version,status='running',runs=[],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in [BASE/'program',BASE/'tests'] for p in sorted(folder.glob('*.py'))})
    cases=[('bridge01','1025_bridges/01_chnn_to_birkhoff/tests','test_*.py'),
           ('inherited_learning','stage5/tests','test_learning_research.py'),
           ('inherited_transport','stage5/tests','test_transport_moser.py')]
    for name,directory,pattern in cases:
        command=[sys.executable,'-m','unittest','discover','-s',directory,'-p',pattern,'-v']
        start=time.perf_counter();path=out/(name+'.log')
        with path.open('w') as log:
            proc=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        match=re.search(r'Ran (\d+) tests?',path.read_text())
        report['runs'].append(dict(command=command,cwd=str(ROOT),exit_code=proc.returncode,
            seconds=time.perf_counter()-start,tests=int(match[1]) if match else None,log=str(path.relative_to(ROOT))))
        print(name,proc.returncode,flush=True)
    old=json.loads((BASE/'results/provenance.json').read_text())['frozen_sha256']
    changed=[p for p,h in old.items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    report.update(status='passed' if not changed and all(r['exit_code']==0 for r in report['runs']) else 'failed',
        frozen_files=len(old),frozen_changed=changed,tests=sum(r['tests'] or 0 for r in report['runs']),
        finished_utc=datetime.now(timezone.utc).isoformat(),scope='No training, new KAM/generator work or full physical validation.')
    (out/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
    (BASE/'results/latest_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','tests','frozen_files','frozen_changed']}))
    if report['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
