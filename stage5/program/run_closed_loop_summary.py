"""Validate and summarize already computed full-coil trajectories."""
from pathlib import Path
import csv
import json
import shutil
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/closed_loop'
path=OUT/'results.json'
report=json.loads(path.read_text())
assert report['status']=='completed',report['status']
# The first execution overlapped a metadata-only correction in CoilROM. Keep
# its actual source hash and snapshot, and label the physical input correctly.
correction=OUT/'source_metadata_correction.json'
if correction.exists():
    change=json.loads(correction.read_text())
    if report['source_sha256']['stage5/program/coil_rom.py']==change['executed_source_sha256']:
        report['model'].setdefault('input_at_execution',report['model']['input'])
        report['model']['input']=change['correct_input_label']
        report['metadata_correction']='stage5/results/closed_loop/source_metadata_correction.json'
        path.write_text(json.dumps(report,indent=2)+'\n')

rows=[]; checks=[]
fig,axes=plt.subplots(1,len(report['branches']),figsize=(5*len(report['branches']),4),squeeze=False)
for ax,(branch,data) in zip(axes[0],report['branches'].items()):
    for method,records in data['methods'].items():
        for r in records:
            row={k:v for k,v in r.items() if k not in ('solver_steps','structure_scope')}
            row.update(branch=branch,method=method)
            rows.append(row)
        target=4 if method=='central4' else 2
        observed=records[-1]['observed_order']
        checks.append(dict(branch=branch,method=method,expected_order=target,
            observed_order=observed,order_band=[target-.2,target+.2],
            order_passed=target-.2<observed<target+.2,
            reference_refinement=data['reference_refinement_max'],
            reference_resolved=bool(data['reference_resolution'][method])))
        ax.loglog([r['step'] for r in records],[r['maximum_state_error'] for r in records],
                  'o-',label=method+' (p=%.3f)'%observed)
    ax.set(title=branch,xlabel='step h in dimensionless time',ylabel='maximum state error to same field')
    ax.grid(True,which='both',alpha=.3);ax.legend()
fig.suptitle('12-DOF variable-mass ROM with full Biot–Savart coils; common T=%.4g'%report['duration_tau'])
fig.tight_layout();fig.savefig(OUT/'convergence.png',dpi=180);fig.savefig(OUT/'convergence.pdf');plt.close(fig)
with (OUT/'metrics.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
verification=dict(status='passed' if all(r['order_passed'] and r['reference_resolved'] for r in checks) else 'failed',
    checks=checks,command=[sys.executable,*sys.argv],
    criteria='Observed order within expected +/-0.2; refined reference difference <1% finest error; no threshold relaxed.',
    limitation='Finite-grid experiment, not a uniform mathematical convergence certificate.')
(OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
log=Path('/workspace/1028-stage5-closed-loop-run.log')
if log.exists():shutil.copy2(log,OUT/'run.log')
print(json.dumps(verification,indent=2))
raise SystemExit(0 if verification['status']=='passed' else 1)
