"""Compare retained legacy transport caches with independent reverse directions."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/high_derivatives'
report=json.loads((OUT/'transport.json').read_text())
assert report['status']=='inverse_backend_directional_checks_passed'
data=np.load(OUT/'transport_arrays.npz')
w=data['output_direction'];E=data['selected_embedding']
paths={'Hessian_b2':ROOT/'stage5/results/transport/prototype_r3_jac3_source_hess2_D2b2.npy',
       'Jacobian_b3':ROOT/'stage5/results/transport/prototype_r3_jac3_source_hess2_Db3.npy'}
H=np.load(paths['Hessian_b2']);J=np.load(paths['Jacobian_b3']);rows=[]
for row in report['records']['original']['directions']:
    v=E@np.asarray(row['direction_selected'])
    hessian=float(np.einsum('i,ijk,j,k',w,H,v,v))
    jacobian=float(w@J@v)
    rows.append(dict(direction_selected=row['direction_selected'],
        legacy_b2_Hessian_contraction=hessian,
        independently_reversed_b2_Hessian_contraction=row['b2_hessian_pure_reverse'],
        legacy_b2_Hessian_error=hessian-row['b2_hessian_pure_reverse'],
        legacy_b3_Jacobian_contraction=jacobian,
        independently_reversed_b3_Jacobian_contraction=row['b3_jacobian_direction_pure_reverse'],
        legacy_b3_Jacobian_error=jacobian-row['b3_jacobian_direction_pure_reverse']))
result=dict(status='legacy_Db3_error_confirmed' if max(abs(v['legacy_b3_Jacobian_error']) for v in rows)>1e-3 else 'unexpected_legacy_comparison',
    command=[sys.executable,*sys.argv],
    legacy_file_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},
    coordinate_center=data['center'].tolist(),rows=rows,
    action='Retain failed caches as evidence; do not reuse Db3 for new represented-field results. Source/cache identity and independent derivatives are required.')
(OUT/'legacy_cache_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
