"""Re-run supplied G1/G2/G3 algorithms on an isolated copy, preserving the archive."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from materials import resolve_source

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'stage6/fusion_reconciliation'


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='fusion_original');args=p.parse_args()
    material=json.loads((BASE/'results/materials.json').read_text())
    source=resolve_source()
    out=BASE/'results/algorithms'/args.run_id
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True)
    scratch=Path(tempfile.mkdtemp(prefix='1028-stage6-G123-',dir='/tmp'))/'fusion'
    shutil.copytree(source,scratch)
    command=[sys.executable,'reproduction/general_birkhoff_experiments/run_all.py','--timing-repetitions','3']
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    start=time.perf_counter()
    record=dict(status='running',command=command,cwd=str(scratch),started_utc=datetime.now(timezone.utc).isoformat(),
                source_archive_sha256=material['archive_sha256'],source_sha256={str(x.relative_to(source)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (source/'reproduction/general_birkhoff_experiments').glob('*.py')},
                scope='Independent rerun of historical 4D mathematical and two-mode baselines; not a new 3D robot experiment.')
    (out/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
    with (out/'run.log').open('w') as log:
        result=subprocess.run(command,cwd=scratch,env=env,stdout=log,stderr=subprocess.STDOUT)
    record.update(status='passed' if result.returncode==0 else 'failed',exit_code=result.returncode,seconds=time.perf_counter()-start)
    folder=scratch/'reproduction/general_birkhoff_experiments'
    for name in ['magnetic_method_comparison.json','synthetic_method_comparison.json','run_validation.json']:
        if (folder/name).exists():shutil.copyfile(folder/name,out/name)
    comparisons=[]
    for name in ['magnetic_method_comparison.json','synthetic_method_comparison.json']:
        if not (out/name).exists():continue
        old=json.loads((source/'reproduction/general_birkhoff_experiments'/name).read_text())
        new=json.loads((out/name).read_text())
        for oldcase,newcase in zip(old['cases'],new['cases']):
            assert oldcase['name']==newcase['name']
            for method,rows in newcase['methods'].items():
                for earlier,current in zip(oldcase['methods'][method],rows):
                    comparisons.append(dict(file=name,case=newcase['name'],method=method,step=current['step'],
                        endpoint_error=current['endpoint_error'],previous_endpoint_error=earlier['endpoint_error'],
                        endpoint_difference=abs(current['endpoint_error']-earlier['endpoint_error']),
                        grid_error=current['maximum_grid_error'],order=current['endpoint_error_order'],
                        structure_defect=current['max_ideal_K_defect_spectral2'],
                        cold_median_s=current['cost']['median_cold_total_seconds'],
                        previous_cold_median_s=earlier['cost']['median_cold_total_seconds']))
    (out/'comparison.json').write_text(json.dumps(dict(rows=comparisons,interpretation='Tolerance/order conclusions compare like models; timings are new measurements, not expected identical.'),indent=2)+'\n')
    (out/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2));raise SystemExit(result.returncode)


if __name__=='__main__':main()
