"""Independent high-order AD counterexamples and safe reverse/inverse checks.

All dense physical-energy tensors are restricted to FOUR input coordinates.
The 24D mass is never frozen. Bad outputs are retained as evidence; detecting
the known solve/mixed-AD bug is a successful diagnostic, not a patched result.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time
import traceback
import numpy as np
import torch

torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'stage3/program'))
OUT=ROOT/'stage5/results/high_derivatives'


def repeated(fun,modes):
    """Modes are chronological: RRF = grad then jacrev then jacfwd."""
    for mode in modes:
        fun=(torch.func.jacrev if mode=='R' else torch.func.jacfwd)(fun)
    return fun


def permutation_defect(tensor):
    return max(float(torch.max(abs(tensor-tensor.permute(*p))))
               for p in itertools.permutations(range(tensor.ndim)))


def directional_reverse(fun,point,direction,order):
    x=point.detach().clone().requires_grad_(True)
    value=fun(x)
    for _ in range(order):
        value=torch.dot(torch.autograd.grad(value,x,create_graph=True)[0],direction)
    return float(value.detach())


def minimal_check():
    records=[];arrays={}
    for power in (1,2):
        functions={
            'division':lambda x,power=power:.5*x[1]**2/(1+x[0]**power),
            'solve':lambda x,power=power:.5*x[1:2]@torch.linalg.solve((1+x[0]**power).reshape(1,1),x[1:2]),
            'inverse':lambda x,power=power:.5*x[1:2]@torch.linalg.inv((1+x[0]**power).reshape(1,1))@x[1:2]}
        for point in (torch.zeros(2),torch.tensor([.2,.3])):
            for order in (2,3,4):
                truth=repeated(functions['division'],'R'*order)(point)
                for name,fun in functions.items():
                    mixed=repeated(fun,'R'+'F'*(order-1))(point)
                    reverse=repeated(fun,'R'*order)(point)
                    tag=f'p{power}_{name}_d{order}_x{float(point[0])}'
                    arrays[tag+'_mixed']=mixed.detach().numpy();arrays[tag+'_reverse']=reverse.detach().numpy()
                    records.append(dict(mass_power=power,implementation=name,point=point.tolist(),order=order,
                        mixed_vs_analytic_division_max=float(torch.max(abs(mixed-truth))),
                        reverse_vs_analytic_division_max=float(torch.max(abs(reverse-truth))),
                        mixed_full_permutation_defect=permutation_defect(mixed)))
    # Different nestings matter: an outermost forward pass can be correct even
    # while differentiating an earlier forward pass produces a wrong result.
    fun=lambda x:.5*x[1:2]@torch.linalg.solve((1+x[0]+x[0]**2).reshape(1,1),x[1:2])
    point=torch.tensor([.2,.3]);patterns=[]
    for order in (3,4):
        truth=repeated(fun,'R'*order)(point)
        for tail in itertools.product('RF',repeat=order-1):
            modes='R'+''.join(tail);value=repeated(fun,modes)(point)
            patterns.append(dict(modes_chronological=modes,
                maximum_difference_from_reverse=float(torch.max(abs(value-truth)))))
    bad=[r for r in records if r['implementation']=='solve' and r['mixed_vs_analytic_division_max']>1e-3]
    safe=[r for r in records if r['implementation']!='solve']
    assert bad,'Known mixed solve failure was not observed; re-evaluate this guard for the installed torch version.'
    assert max(r['mixed_vs_analytic_division_max'] for r in safe)<1e-12
    assert max(r['reverse_vs_analytic_division_max'] for r in records)<1e-12
    return dict(status='known_failure_detected_and_safe_paths_verified',records=records,nesting_patterns=patterns,
                cause_scope='torch 2.5.1 CPU nested AD of linalg.solve; this is not a proof about every PyTorch version or every possible nesting.'),arrays


def physical_energy_check():
    from rom_bridge import ROMBridge
    from transport_native import NativeTransport
    base=ROMBridge();inverse=NativeTransport(base=base,kind='conservative',ad_backend='inverse')
    selected=[0,1,12,13];embedding=torch.zeros(24,4)
    for j,i in enumerate(selected):embedding[i,j]=1.
    origin=torch.zeros(4);direction=torch.tensor([1.,0.,0.,-1.])
    functions={'original_solve':lambda y:base.hamiltonian_tensor(embedding@y),
               'inverse_mass':lambda y:inverse.high_order_hamiltonian(embedding@y)}
    arrays={};records={}
    for name,fun in functions.items():
        before=time.perf_counter()
        h3=repeated(fun,'RFF')(origin)
        h3_reverse=repeated(fun,'RRR')(origin)
        h4=repeated(fun,'RFFF')(origin)
        reverse_direction=directional_reverse(fun,origin,direction,4)/24
        contraction=float(torch.einsum('abcd,a,b,c,d',h4,direction,direction,direction,direction))/24
        arrays[name+'_H3_mixed']=h3.detach().numpy();arrays[name+'_H3_reverse']=h3_reverse.detach().numpy()
        arrays[name+'_H4_mixed']=h4.detach().numpy()
        h2=directional_reverse(fun,origin,direction,2)/2
        f0=float(fun(origin));finite=[]
        for radius in (.004,.002):
            value=(float(fun(radius*direction))+float(fun(-radius*direction)))/2-f0-radius**2*h2
            finite.append(dict(radius=radius,quartic_coefficient=value/radius**4))
        records[name]=dict(seconds=time.perf_counter()-before,
            H3_mixed_vs_reverse_max=float(torch.max(abs(h3-h3_reverse))),
            H3_full_permutation_defect=permutation_defect(h3),
            H4_full_permutation_defect=permutation_defect(h4),
            directional_quartic_mixed=contraction,directional_quartic_pure_reverse=reverse_direction,
            finite_radius_even_energy=finite)
        print('physical',name,records[name],flush=True)
    # No averaging of the bad tensor is used to repair it.
    assert abs(records['original_solve']['directional_quartic_mixed']-records['original_solve']['directional_quartic_pure_reverse'])>1
    assert abs(records['inverse_mass']['directional_quartic_mixed']-records['inverse_mass']['directional_quartic_pure_reverse'])<1e-8
    assert records['inverse_mass']['H4_full_permutation_defect']<1e-8
    return dict(status='real_ROM_failure_detected_inverse_verified',selected_coordinates=selected,
                point='zero 24D phase state',direction_in_selected_coordinates=direction.tolist(),records=records,
                full_mass_retained=True),arrays


def transport_check():
    from rom_bridge import ROMBridge
    from transport_native import NativeTransport
    base=ROMBridge();models={name:NativeTransport(base=base,ad_backend=name) for name in ('original','inverse')}
    z=torch.tensor(base.initial_state(.01));selected=[0,1,12,13]
    E=torch.zeros(24,4)
    for j,i in enumerate(selected):E[i,j]=1.
    rng=np.random.default_rng(51031);w=torch.tensor(rng.normal(size=24));w/=torch.linalg.vector_norm(w)
    directions=[torch.tensor([1.,0.,0.,-1.])/np.sqrt(2),torch.tensor(rng.normal(size=4))]
    directions[1]/=torch.linalg.vector_norm(directions[1])
    safe=models['original']
    def b2_reverse(x):
        f=safe.field_tensor(x);a=safe.b1(x)
        return -.5*(torch.func.jacrev(safe.b1)(x)@f+torch.func.jacrev(safe.field_tensor)(x).T@a)
    # Only scalar Lie contractions are differentiated: no dense 24^4 tensor.
    def scalar_b3_reverse(x):
        alpha=b2_reverse(x);f=safe.field_tensor(x)
        Da=torch.func.jacrev(b2_reverse)(x)
        Df=torch.func.jacrev(safe.field_tensor)(x)
        return -torch.dot(w,Da@f+Df.T@alpha)/3
    exact_b2=b2_reverse(z).detach().numpy()
    arrays={'center':z.numpy(),'output_direction':w.numpy(),'selected_embedding':E.numpy()};records={}
    for name,model in models.items():
        before=time.perf_counter();b2=model.source_coefficient_function(2);b3=model.source_coefficient_function(3)
        value=b2(z).detach().numpy()
        scalar=lambda y:torch.dot(w,b2(z+E@y))
        hessian_mixed=torch.func.jacfwd(torch.func.jacrev(scalar))(torch.zeros(4))
        arrays[name+'_b2_scalar_selected_Hessian']=hessian_mixed.detach().numpy()
        directions_report=[]
        for v4 in directions:
            v=E@v4
            safe_hessian=directional_reverse(lambda x:torch.dot(w,b2_reverse(x)),z,v,2)
            original_native_hessian=directional_reverse(lambda x:torch.dot(w,b2(x)),z,v,2)
            contraction=float(v4@hessian_mixed@v4)
            fd=[]
            for eps in (2e-5,1e-5):
                fd.append(dict(epsilon=eps,value=float((torch.dot(w,b2(z+eps*v))-2*torch.dot(w,b2(z))+torch.dot(w,b2(z-eps*v)))/eps**2)))
            # Db3 is especially exposed: jvp of b2 followed by jacrev can
            # differentiate through the unreliable forward solve rule.
            safe_db3=directional_reverse(scalar_b3_reverse,z,v,1)
            native_db3=directional_reverse(lambda x:torch.dot(w,b3(x)),z,v,1)
            directions_report.append(dict(direction_selected=v4.tolist(),b2_hessian_pure_reverse=safe_hessian,
                b2_hessian_native_reverse=original_native_hessian,b2_hessian_mixed=contraction,
                b2_hessian_finite_difference=fd,b3_jacobian_direction_pure_reverse=safe_db3,
                b3_jacobian_direction_native=native_db3,
                b3_jacobian_direction_difference=native_db3-safe_db3))
        records[name]=dict(seconds=time.perf_counter()-before,b2_value_vs_reverse_norm=float(np.linalg.norm(value-exact_b2)),
            b2_scalar_hessian_antisymmetry=float(torch.max(abs(hessian_mixed-hessian_mixed.T))),directions=directions_report)
        print('transport',name,records[name],flush=True)
    # The safe backend must agree in actual contractions, not only symmetry.
    for row in records['inverse']['directions']:
        assert abs(row['b2_hessian_mixed']-row['b2_hessian_pure_reverse'])<1e-7*(1+abs(row['b2_hessian_pure_reverse']))
        assert abs(row['b3_jacobian_direction_difference'])<1e-7*(1+abs(row['b3_jacobian_direction_pure_reverse']))
    return dict(status='inverse_backend_directional_checks_passed',selected_coordinates=selected,
        source_model='NativeTransport synthetic state-dependent canonical drag, full inherited M(Q)',
        interpretation='Specific finite-point checks; tensor symmetry alone is not a derivative correctness test.',records=records),arrays


def main():
    p=argparse.ArgumentParser();p.add_argument('--section',choices=['minimal','rom','transport','all'],default='all');args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    funcs={'minimal':minimal_check,'rom':physical_energy_check,'transport':transport_check}
    for name,fun in funcs.items():
        if args.section not in ('all',name):continue
        before=time.perf_counter();report=dict(status='running',section=name,command=[sys.executable,*sys.argv],
            started_at=datetime.now(timezone.utc).isoformat(),torch_version=torch.__version__,numpy_version=np.__version__,
            source_sha256={str(q.relative_to(ROOT)):hashlib.sha256(q.read_bytes()).hexdigest() for q in
                [Path(__file__),ROOT/'stage3/source_inputs/starter/stage2/program/learning/rod_rom.py',ROOT/'stage5/program/transport_native.py']})
        destination=OUT/(name+'.json');destination.write_text(json.dumps(report,indent=2)+'\n')
        try:
            result,arrays=fun();report.update(result);np.savez_compressed(OUT/(name+'_arrays.npz'),**arrays)
        except Exception as exc:
            report.update(status='failed',exception=repr(exc),traceback=traceback.format_exc());raise
        finally:
            report.update(seconds=time.perf_counter()-before,ended_at=datetime.now(timezone.utc).isoformat())
            destination.write_text(json.dumps(report,indent=2)+'\n')
        print(name,report['status'],flush=True)


if __name__=='__main__':main()
