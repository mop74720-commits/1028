"""Independent algebra and invariance checks for the restricted normal form.

S5-R04 never treats the first pair as an exact reduced physical plant.  It
checks the circular-action identity at independent points and evaluates the
original 24D vector field off that coordinate subspace.  Existing R01-R03
results and trained weights are only read.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import torch
from learning_models import RodROM

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'stage5/results/resonance'


def main():
    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    start = time.perf_counter()
    r3 = json.loads((OUT / 'S5_R03_pair_reduction.json').read_text())
    linear = np.asarray(r3['real_canonical_map'])
    rng = np.random.default_rng(510404)
    points = rng.normal(size=(32, 4)) * .02
    rows = []
    for z in points:
        q, p = z[:2], z[2:]
        N = (q @ q + p @ p) / 2
        L = q[0] * p[1] - q[1] * p[0]
        target = linear @ z
        actions = (target[:2]**2 + target[2:]**2) / 2
        before = r3['A'] * N**2 + r3['B'] * L**2
        after = r3['A'] * actions.sum()**2 + r3['B'] * (actions[0] - actions[1])**2
        rows.append(dict(action_identity_error=float(np.max(abs(actions - np.array([N+L,N-L])/2))),
                         energy_identity_error=float(abs(before-after))))
    rom = RodROM()
    n = rom.n
    selected = [0, 1, n, n+1]
    external = [j for j in range(2*n) if j not in selected]
    field_rows = []
    for scale in [.01, .02, .04]:
        z = torch.zeros(2*n)
        z[selected] = torch.tensor([.7, -.4, .2, .3]) * scale
        _, grad = rom.gradient(z[None, :])
        g = grad.detach().numpy()[0]
        f = np.r_[g[n:], -g[:n]]
        field_rows.append(dict(scale=scale,state=z.numpy().tolist(),
                               selected_field_norm=float(np.linalg.norm(f[selected])),
                               external_field_norm=float(np.linalg.norm(f[external])),
                               external_field_components=f[external].tolist()))
    result = dict(experiment='S5-R04',status='independently_executed',
                  circular_action_checks=rows,
                  maximum_action_error=max(r['action_identity_error'] for r in rows),
                  maximum_energy_error=max(r['energy_identity_error'] for r in rows),
                  original_first_pair_subspace_checks=field_rows,
                  interpretation='Nonzero external vector-field components show the original first-pair coordinate subspace is not an invariant physical subsystem. This does not rule out a transformed approximate normal-form subspace; the latter has not been certified.',
                  model='Full24D variable-mass H_ideal, not H_coil and not a truncated2DOF physical plant',
                  source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'stage3/source_inputs/starter/stage2/program/learning/rod_rom.py']},
                  input_result_sha256=hashlib.sha256((OUT/'S5_R03_pair_reduction.json').read_bytes()).hexdigest(),
                  wall_seconds=time.perf_counter()-start)
    if result['maximum_action_error']>1e-12 or result['maximum_energy_error']>1e-12:
        raise AssertionError('Circular coordinate/action convention failed independent point check')
    (OUT/'S5_R04_partial_scope.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','maximum_action_error','maximum_energy_error','original_first_pair_subspace_checks','wall_seconds']},indent=2))


if __name__ == '__main__':
    main()
