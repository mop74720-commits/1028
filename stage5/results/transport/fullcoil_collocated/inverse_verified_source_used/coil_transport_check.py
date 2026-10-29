"""Reproduce the full-coil / native-transport interface cross-check.

Uses the same inverse high-AD velocity as the actual transport driver; compares
against the independently retained physical solve-based CoilROM field/Jacobian.
No coefficient symmetrization or frozen-mass surrogate enters these checks.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]
FILES=[Path(__file__).with_name(name) for name in ('coil_rom.py','transport_native.py','run_transport_experiments.py')]+[Path(__file__)]
HASHES={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
from coil_rom import CoilROM
from transport_native import NativeTransport


def main():
    start=time.perf_counter();base=CoilROM()
    native=NativeTransport(base=base,kind='fullcoil_collocated',ad_backend='inverse')
    def force(z):
        G=base.current_port_tensor(z[:base.n])
        velocity=native._gradH(z)[base.n:]
        return -base.collocated_gain*G@(G.T@velocity)
    native.force_override=force
    z=base.initial_state();x=base.tensor(z)
    f,A,_=native.field_and_jacobian(z)
    native_tensor=native.field_tensor(x).detach().numpy()
    results=dict(native_numeric_vs_actual_feedback_field=float(np.linalg.norm(f-base.feedback_field(z))),
        native_tensor_vs_numeric_field=float(np.linalg.norm(native_tensor-f)),
        native_vs_actual_feedback_J=float(np.linalg.norm(A-base.feedback_jacobian(z))),
        inverse_vs_solve_H_difference=float(abs(native.high_order_hamiltonian(x)-base.hamiltonian_tensor(x))),
        homogeneous_a1_plus_Lie_a0=float(torch.linalg.vector_norm(native.a1(x)+native.lie_oneform(native.a0,x))),
        source_b1_plus_force=float(torch.linalg.vector_norm(native.b1(x)+torch.cat((force(x),torch.zeros(base.n))))))
    assert results['native_numeric_vs_actual_feedback_field']<1e-11
    assert results['native_tensor_vs_numeric_field']<1e-11
    assert results['native_vs_actual_feedback_J']<1e-9
    assert results['inverse_vs_solve_H_difference']<1e-12
    assert results['homogeneous_a1_plus_Lie_a0']<1e-11
    assert results['source_b1_plus_force']<1e-14
    unchanged={str(p.relative_to(ROOT)):HASHES[str(p.relative_to(ROOT))]==hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
    report=dict(status='actually_executed_pass',command=' '.join(sys.argv),initial_state=z.tolist(),currents_A=base.bias_currents.tolist(),
        model='Same full 20-cell/256-wire-point 3D ROM and physical total bias; pure smooth collocated feedback, gamma=0',
        force_override='-gain Gcoil Gcoil.T H_P, using NativeTransport inverse backend velocity for high AD',
        checks=results,source_sha256_at_import=HASHES,source_unchanged_during_run=unchanged,
        tolerances=dict(field_absolute=1e-11,jacobian_absolute=1e-9,H_absolute=1e-12,a1_absolute=1e-11,b1_absolute=1e-14),
        elapsed_seconds=time.perf_counter()-start,python=sys.version,torch=torch.__version__,numpy=np.__version__,
        scope='Physical field, low-order Jacobian and first transport/source coefficient interfaces. This is not a full fourth-order tensor, higher native coefficient, chart or integration certificate.')
    out=ROOT/'stage5/results/coil/transport_interface_check.json'
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
