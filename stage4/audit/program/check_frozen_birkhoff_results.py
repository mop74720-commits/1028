"""Independently recompute all stored short-window trajectory metrics.

Reads frozen NPZ/JSON only; this does not re-integrate either field. The separate
stage4 reproduction jobs re-integrate the fields and methods.
"""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
archive = ROOT / 'stage3/results/birkhoff/trajectories_T0.0005.npz'
report = ROOT / 'stage3/results/birkhoff/results_T0.0005.json'
a = np.load(archive)
r = json.loads(report.read_text())
gap = float(np.max(np.linalg.norm(a['represented_reference']-a['original_reference'],axis=1)))
rows = []
for row in r['rows']:
    key = f"{row['method']}_h{row['h']:g}"
    states = a[key]
    stride = (len(a['reference_times'])-1)//(len(states)-1)
    assert (len(states)-1)*stride == len(a['reference_times'])-1
    eo = float(np.max(np.linalg.norm(states-a['original_reference'][::stride],axis=1)))
    ea = float(np.max(np.linalg.norm(states-a['represented_reference'][::stride],axis=1)))
    rows.append(dict(key=key,recomputed_error_to_original=eo,recomputed_error_to_represented=ea,
                     json_original_difference=abs(eo-row['error_to_original_max']),
                     json_represented_difference=abs(ea-row['error_to_represented_max'])))
    assert abs(eo-row['error_to_original_max']) < 1e-16
    assert abs(ea-row['error_to_represented_max']) < 1e-16
assert abs(gap-r['represented_vs_original_reference_gap']) < 1e-16
out = dict(status='all six stored trajectory metrics independently recomputed from NPZ',
           command=' '.join(sys.argv),executable=sys.executable,numpy_version=np.__version__,
           source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           archive=str(archive.relative_to(ROOT)),
           archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
           reference_gap=gap,gap_difference=abs(gap-r['represented_vs_original_reference_gap']),
           rows=rows,tolerance=1e-16,
           scope='Recompute frozen data metrics; not a fresh numerical integration.')
destination = ROOT/'stage4/audit/results/birkhoff_frozen_npz_check.json'
destination.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
