"""Check whether magnetic rank is tied to distal-magnet quadrature."""
from pathlib import Path
import json
import time
import numpy as np
from rom_bridge import ROMBridge
ROOT=Path(__file__).resolve().parents[1]
start=time.perf_counter();records=[]
for elements in (20,40,80):
    model=ROMBridge(elements=elements);z=model.initial_state();g=model.magnetic_map(z[:12])
    scale=np.array([.001]*3+[.01]*5);singular=np.linalg.svd(g*scale,compute_uv=False)
    records.append(dict(elements=elements,magnetized_quadrature_cells=int(np.sum(model.rom.segment_moment.numpy()>0)),
       rank_rcond_1e_8=int(np.sum(singular>1e-8*singular[0])),singular_values=singular.tolist(),
       initial_state_rule='initial_state(.01) in each quadrature-specific linear modal scaling; these are rank diagnostics, not trajectory convergence comparisons'))
report=dict(status='executed',records=records,elapsed_seconds=time.perf_counter()-start,
  conclusion='Rank depends on the selected ROM geometry/quadrature. Any 12x8 magnetic input map has rank at most8; do not generalize rank5 from the delivered20-cell quadrature to all spatial resolutions.')
out=ROOT/'results/control/port_quadrature_rank.json';out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
