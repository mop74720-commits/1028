"""Compare actual reruns with supplied numerical claims, retaining field paths."""
import json
import math
from pathlib import Path
from materials import BASE,resolve_source


def flatten(x,p=''):
    if isinstance(x,dict):
        for k,v in x.items():yield from flatten(v,p+'.'+k if p else k)
    elif isinstance(x,list):
        for k,v in enumerate(x):yield from flatten(v,f'{p}[{k}]')
    elif isinstance(x,(int,float)) and not isinstance(x,bool):yield p,x


def main():
    source=resolve_source()/'reproduction';out=BASE/'results/history';actual=out/'fusion_original_reproduction'
    records=[]
    for subdir in ['experiments','framework_experiments']:
        for p in sorted((actual/subdir).glob('*.json')):
            old=dict(flatten(json.loads((source/p.relative_to(actual)).read_text())))
            new=dict(flatten(json.loads(p.read_text())))
            matches=[];failed=[];excluded=[]
            for k,v in new.items():
                if any(s in k.lower() for s in ['elapsed','seconds_runtime','timing','provenance','wall_time']):excluded.append(k);continue
                if k not in old:continue
                a=old[k];err=abs(a-v);tol=1e-12+1e-9*max(abs(a),abs(v))
                item=dict(field=k,supplied=a,rerun=v,absolute_difference=err,tolerance=tol)
                (matches if math.isfinite(err) and err<=tol else failed).append(item)
            records.append(dict(file=str(p.relative_to(BASE)),compared_numeric_fields=len(matches)+len(failed),
                passed_fields=len(matches),failures=failed,excluded_runtime_metadata=excluded,
                maximum_absolute_difference=max((x['absolute_difference'] for x in matches+failed),default=0)))
    record=dict(status='passed' if all(not x['failures'] for x in records) else 'numerical differences require review',
        tolerance='absolute 1e-12 + relative 1e-9, independently declared comparison tolerance; original solve tolerance unchanged',files=records,
        caveat='This checks reproducibility of supplied float results, not interval validity or transfer to a different physical model.')
    (out/'supplied_vs_rerun_numeric.json').write_text(json.dumps(record,indent=2)+'\n')
    print(record['status'],sum(x['compared_numeric_fields'] for x in records),'numeric fields')
    if record['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
