"""Compare actual audit reruns with published stage3 scientific values.

Runtime durations and absolute paths are intentionally not scientific equality
targets. All reported differences are measured, including zero differences.
"""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np

REPO=Path(__file__).resolve().parents[3]
OLD=REPO/'stage3/results'
NEW=REPO/'stage4/audit/results/reproduced'
OUT=REPO/'stage4/audit/results/rerun_comparison.json'
run_path=REPO/'stage4/audit/results/reproduction.json'
execution=json.loads(run_path.read_text())
start=json.loads((REPO/'stage4/audit/results/start_provenance.json').read_text())
changed=[]
for relative, expected in start['tracked_files_before'].items():
    path=REPO/relative
    actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if actual != expected:
        changed.append(dict(path=relative,before=expected,after=actual))
preservation=dict(source_head=start['audit_start_head'],
    tracked_files_checked=len(start['tracked_files_before']),changed=changed,
    all_starting_tracked_files_unchanged=not changed,
    preserved_untracked=start['preserved_untracked'])
(REPO/'stage4/audit/results/frozen_preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
execution['starting_tracked_file_preservation']=preservation
assert not changed,changed
for name in ('rom_bridge.json','birkhoff_identity_checks.json'):
    src=Path(execution['scratch_root'])/'stage3/results'/name
    dst=NEW/name
    shutil.copy2(src,dst)
    relative=str(dst.relative_to(REPO))
    execution['fresh_outputs']=[x for x in execution['fresh_outputs'] if x['path']!=relative]
    execution['fresh_outputs'].append(dict(path=relative,bytes=dst.stat().st_size,sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
correction=REPO/'stage4/audit/results/test_side_effect_restore.json'
if execution['runs'][0]['cwd']==str(REPO) and correction.exists():
    execution['execution_corrections']=dict(record=str(correction.relative_to(REPO)),
        detail='The first tests were initially run in the source checkout, revealing test teardown evidence writes. The affected files were restored byte-for-byte from the pre-run copy after checking HEAD. The harness was corrected to isolate even this initial test invocation; its logged cwd remains the actual historical cwd. The final23-test run uses scratch and fresh scientific outputs.')
run_path.write_text(json.dumps(execution,ensure_ascii=False,indent=2)+'\n')
report={'meaning':'Same source and scientific settings on this machine, freshly executed; not an independent solver implementation or a domain-wide proof.','scalar_comparisons':[],'array_comparisons':[]}

def scalar(label,old,new):
    report['scalar_comparisons'].append(dict(label=label,published=float(old),rerun=float(new),absolute_difference=float(abs(old-new))))

old=json.loads((OLD/'integrators/integrators.json').read_text())
new=json.loads((NEW/'integrators/integrators.json').read_text())
for branch,b in old['branches'].items():
    for method,rows in b['methods'].items():
        for i,row in enumerate(rows):
            fresh=new['branches'][branch]['methods'][method][i]
            for key in ('maximum_state_error','max_increment_residual_inf','maximum_midpoint_power_balance_residual'):
                scalar(f'integrators.{branch}.{method}.h{row["step"]}.{key}',row[key],fresh[key])
            if row['observed_order'] is not None:scalar(f'integrators.{branch}.{method}.h{row["step"]}.order',row['observed_order'],fresh['observed_order'])

old=json.loads((OLD/'birkhoff/results_T0.0005.json').read_text())
new=json.loads((NEW/'birkhoff/results_T0.0005.json').read_text())
for i,row in enumerate(old['rows']):
    fresh=new['rows'][i]
    for key in ('error_to_original_max','error_to_represented_max','original_power_balance_residual_max','residual_inf'):
        scalar(f'birkhoff.{row["method"]}.h{row["h"]}.{key}',row[key],fresh[key])
    if row['observed_order_to_integrated_field'] is not None:scalar(f'birkhoff.{row["method"]}.h{row["h"]}.order',row['observed_order_to_integrated_field'],fresh['observed_order_to_integrated_field'])
scalar('birkhoff.reference_gap',old['represented_vs_original_reference_gap'],new['represented_vs_original_reference_gap'])

for name in ('integrators/integrators_traces.npz','birkhoff/trajectories_T0.0005.npz','control/trajectories.npz','control_learning/learning_data_and_trajectories.npz'):
    a=np.load(OLD/name);b=np.load(NEW/name)
    assert sorted(a.files)==sorted(b.files),name
    for key in a.files:
        assert a[key].shape==b[key].shape,(name,key)
        assert np.isfinite(b[key]).all(),(name,key)
        report['array_comparisons'].append(dict(path=name,array=key,shape=list(a[key].shape),maximum_absolute_difference=float(np.max(np.abs(a[key]-b[key]))) if a[key].size else 0.))

old=json.loads((OLD/'control_learning/learning_results.json').read_text())
new=json.loads((NEW/'control_learning/learning_results.json').read_text())
scalar('learning.beta_fitted',old['beta_fitted'],new['beta_fitted'])
scalar('learning.heldout_force_relative_l2',old['scores']['heldout']['force_relative_l2'],new['scores']['heldout']['force_relative_l2'])
old=json.loads((OLD/'control/full_coil_force_audit.json').read_text())
new=json.loads((NEW/'control/full_coil_force_audit.json').read_text())
for i,r in enumerate(old['records']):
    scalar(f'coil.{i}.full_minus_affine_relative',r['full_minus_affine_relative'],new['records'][i]['full_minus_affine_relative'])
report['max_scalar_absolute_difference']=max(x['absolute_difference'] for x in report['scalar_comparisons'])
report['max_array_absolute_difference']=max(x['maximum_absolute_difference'] for x in report['array_comparisons'])
report['status']='all_compared_arrays_finite_and_shapes_match'
OUT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('scalar_comparisons','array_comparisons')}))
