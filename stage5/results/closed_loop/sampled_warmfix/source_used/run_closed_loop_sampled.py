"""Finite-difference the complete constrained sampled-current map, not a frozen field."""
from datetime import datetime,timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
import numpy as np
from coil_rom import CoilROM
from closed_loop_sampled import SampledCurrentMap,finite_difference_jacobian

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=ROOT/'stage5/results/closed_loop')
args=parser.parse_args()
OUT=args.output.resolve()
OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'sampled_jacobian.json').exists():
    raise FileExistsError(f'Preserve previous evidence; choose another --output: {OUT}')
SOURCES=[Path(__file__),ROOT/'stage5/program/closed_loop_sampled.py',ROOT/'stage5/program/coil_control.py',ROOT/'stage5/program/coil_rom.py']
(OUT/'source_used').mkdir()
for path in SOURCES:
    (OUT/'source_used'/path.name).write_bytes(path.read_bytes())
start=time.perf_counter()
report=dict(status='running',command=[sys.executable,*sys.argv],cwd=str(Path.cwd()),
    started_at=datetime.now(timezone.utc).isoformat(),runs=[],
    coordinate_order='(Q[12],P[12],previous_total_current_A[12]); dimension 36',
    scope='One actual controller period with continuous current ramp, full-coil plant, gamma=.2; no continuous-time or symplectic claim.',
    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES},
    baseline_json='stage5/results/closed_loop/sampled_jacobian.json',
    mathematical_protocol_changed=False,
    runner_change='Add nonoverwriting output option, exact source snapshots, and retain probe active signatures; initial state, map, epsilon, random seed and directions are unchanged.')
def save():
    (OUT/'sampled_jacobian.json').write_text(json.dumps(report,indent=2)+'\n')
save();arrays={}
try:
    model=CoilROM()
    x=np.r_[model.initial_state(.01),model.bias_currents]
    rng=np.random.default_rng(51030)
    directions=rng.normal(size=(2,36));directions/=np.linalg.norm(directions,axis=1)[:,None]
    for kind in ('collocated','damping_compensation'):
        begin=time.perf_counter();mapping=SampledCurrentMap(model,kind)
        base,metadata=mapping(x)
        jac,signatures=finite_difference_jacobian(mapping,x,1e-6)
        stability=[]
        for v in directions:
            coarse=(mapping(x+2e-6*v)[0]-mapping(x-2e-6*v)[0])/(4e-6)
            fine=(mapping(x+1e-6*v)[0]-mapping(x-1e-6*v)[0])/(2e-6)
            stability.append(dict(epsilon_refinement_relative=float(np.linalg.norm(coarse-fine)/max(np.linalg.norm(fine),1e-15)),
                matrix_direction_relative=float(np.linalg.norm(jac@v-fine)/max(np.linalg.norm(fine),1e-15))))
        singular=np.linalg.svd(jac,compute_uv=False)
        mechanical=jac[:24,:24]
        forms=np.zeros((36,36));forms[:24,:24]=model.K0
        base_signature=metadata['active_box_signature']
        active_changed=sum(s['lower']!=base_signature['lower'] or s['upper']!=base_signature['upper'] for s in signatures)
        record=dict(kind=kind,interval_tau=mapping.interval,interval_seconds=mapping.interval/model.rom.omega0,
            RK4_substeps=mapping.substeps,gamma=mapping.gamma,allocation=metadata['allocation'],
            active_box_signature=base_signature,active_signature_changes_in_72_coordinate_probes=active_changed,
            coordinate_probe_active_signatures=signatures,
            finite_difference_epsilon=1e-6,directional_checks=stability,
            full_augmented_jacobian_condition=float(np.linalg.cond(jac)),
            singular_values=singular.tolist(),numerical_rank_relative_1e_8=int(np.sum(singular>singular[0]*1e-8)),
            current_memory_to_mechanics_norm=float(np.linalg.norm(jac[:24,24:],2)),
            state_to_next_current_norm=float(np.linalg.norm(jac[24:,:24],2)),
            conditional_mechanical_canonical_defect_2=float(np.linalg.norm(mechanical.T@model.K0@mechanical-model.K0,2)),
            augmented_degenerate_form_defect_2=float(np.linalg.norm(jac.T@forms@jac-forms,2)),
            structure_interpretation='24x24 block fixes previous current; it is not the whole map. diag(K0,0) is degenerate, so its defect is only a diagnostic, never a symplectic certificate.',
            smoothness_interpretation='Stable sampled active box signatures do not exclude field-constraint or optimizer sensitivity and do not prove a neighborhood theorem.',
            seconds=time.perf_counter()-begin)
        arrays[kind+'_initial']=x;arrays[kind+'_final']=base;arrays[kind+'_jacobian']=jac
        report['runs'].append(record);save()
        np.savez_compressed(OUT/'sampled_jacobians.npz',**arrays)
        print(kind,json.dumps(record),flush=True)
        assert np.isfinite(jac).all()
    report['status']='completed'
except Exception as exc:
    report['status']='failed';report['failure']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    raise
finally:
    report['source_unchanged_during_run']={str(p.relative_to(ROOT)):report['source_sha256'][str(p.relative_to(ROOT))]==hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}
    report['ended_at']=datetime.now(timezone.utc).isoformat();report['elapsed_seconds']=time.perf_counter()-start;save()
