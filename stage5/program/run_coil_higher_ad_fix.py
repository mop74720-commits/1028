"""Verify an off-wire algebraic norm rewrite and preserve both source versions.

The old torch.linalg.vector_norm fails for mixed high-order AD in PyTorch 2.5.1.
The new sqrt(sum(d*d)) is identical on the strictly positive-distance domain.
This records old/new actual fields/Jacobians and an independent high-derivative
directional finite difference; it does not relabel historical trajectory hashes.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
import types
import traceback
import numpy as np
import torch
from coil_rom import CoilROM

ROOT=Path(__file__).resolve().parents[2]


def main():
    out=ROOT/'stage5/results/coil';oldpath=out/'source_before_higher_ad_fix.py'
    actualpath=Path(__file__).with_name('coil_rom.py')
    oldbytes=oldpath.read_bytes();newbytes=actualpath.read_bytes()
    oldmodule=types.ModuleType('coil_rom_before_norm_fix')
    # Execute the immutable snapshot with its original source location so all
    # inherited read-only imports resolve identically to the recorded program.
    oldmodule.__file__=str(actualpath)
    exec(compile(oldbytes,str(actualpath),'exec'),oldmodule.__dict__)
    start=time.perf_counter();old=oldmodule.CoilROM();new=CoilROM()
    z=new.initial_state();direction=np.cos(np.arange(z.size)+.37);direction/=np.linalg.norm(direction)
    data={}
    for label,fun in [('fixed_field',lambda m:m.field(z)),('fixed_jacobian',lambda m:m.jacobian(z)),
                      ('feedback_field',lambda m:m.feedback_field(z)),('feedback_jacobian',lambda m:m.feedback_jacobian(z)),
                      ('current_port',lambda m:m.current_port(z[:m.n]))]:
        before=fun(old);after=fun(new)
        data[label]=dict(absolute_norm_difference=float(np.linalg.norm(after-before)),reference_norm=float(np.linalg.norm(before)))
        assert np.linalg.norm(after-before)<1e-9
    old_mixed={}
    try:
        result=torch.func.jvp(torch.func.jacrev(old.feedback_field_tensor),(old.tensor(z),),(old.tensor(direction),))[1]
        old_mixed=dict(status='executed',norm=float(torch.linalg.vector_norm(result)))
    except RuntimeError as exc:
        old_mixed=dict(status='failed_preserved',exception=str(exc),traceback=traceback.format_exc())
    mixed=torch.func.jvp(torch.func.jacrev(new.feedback_field_tensor),(new.tensor(z),),(new.tensor(direction),))[1].detach().numpy()
    refinement=[]
    for eps in (2e-6,1e-6):
        fd=(new.feedback_jacobian(z+eps*direction)-new.feedback_jacobian(z-eps*direction))/(2*eps)
        refinement.append(dict(eps=eps,absolute_error=float(np.linalg.norm(fd-mixed)),relative_error=float(np.linalg.norm(fd-mixed)/max(np.linalg.norm(mixed),1e-30))))
    assert max(x['relative_error'] for x in refinement)<2e-6
    report=dict(status='actually_executed_pass',old_source=str(oldpath.relative_to(ROOT)),
        old_sha256=hashlib.sha256(oldbytes).hexdigest(),new_source=str(actualpath.relative_to(ROOT)),new_sha256=hashlib.sha256(newbytes).hexdigest(),
        change='r=linalg.vector_norm(distance) changed to sqrt(sum(distance*distance)); domain excludes wires, so r>0. No mass, force, current, gain or physical model modification.',
        comparison=data,old_mixed_AD=old_mixed,new_mixed_AD=dict(status='passed',derivative='Directional derivative of complete feedback Jacobian; forward-over-reverse high-order AD',norm=float(np.linalg.norm(mixed)),finite_difference_refinement=refinement),
        tolerances=dict(old_new_absolute=1e-9,higher_derivative_relative=2e-6),
        torch=torch.__version__,python=sys.version,elapsed_seconds=time.perf_counter()-start,
        historical_scope='validation.json and closed_loop_summary.json retain SHA53004846... and original actual numerical outputs. Their exact source bytes are the immutable snapshot. This equivalence check connects them to the current algebraically identical implementation, rather than fabricating a new long execution.')
    (out/'higher_ad_fix_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
