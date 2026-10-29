"""Cross-check equivalent inverse high-AD expression against pure reverse AD.

Raw homogeneous coefficients and their gauge relation are also actually
evaluated at the native 24D state; this is not a polynomial surrogate test.
"""
from pathlib import Path
import argparse,json,time,hashlib,traceback
import numpy as np
import torch
from transport_native import NativeTransport


def scalar_directional_reverse(function,z,d,order):
    x=torch.tensor(z,requires_grad=True);v=function(x)
    for _ in range(order):v=torch.dot(torch.autograd.grad(v,x,create_graph=True)[0],d)
    return float(v.detach())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['synthetic','fullcoil'],default='synthetic');parser.add_argument('--run-id',default='inverse');args=parser.parse_args()
    out=Path(__file__).resolve().parents[1]/'results/transport';dest=out/f'backend_validation_{args.model}_{args.run_id}.json'
    if dest.exists():raise FileExistsError(dest)
    result=dict(status='running',rows=[],model=args.model,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());save=lambda:dest.write_text(json.dumps(result,indent=2)+'\n');save();started=time.perf_counter()
    try:
        if args.model=='fullcoil':
            from coil_rom import CoilROM
            base=CoilROM();m=NativeTransport(base=base,ad_backend='inverse')
        else:m=NativeTransport(ad_backend='inverse')
        z=m.base.initial_state();x=torch.tensor(z);rng=np.random.default_rng(51025)
        original=m.base.hamiltonian_tensor;safe=m.high_order_hamiltonian
        for name,op in [('value',lambda f:f),('gradient',torch.func.grad),('hessian',lambda f:torch.func.jacrev(torch.func.grad(f)))]:
            a=op(original)(x).detach().numpy();b=op(safe)(x).detach().numpy()
            error=float(np.linalg.norm(a-b));relative=error/max(float(np.linalg.norm(a)),1.)
            result['rows'].append(dict(kind=name,error_2=error,relative_error=relative));save()
            assert relative<2e-11,(name,relative)
        Hess=torch.func.jacrev(torch.func.grad(safe))
        for direction_index in range(2):
            d=torch.tensor(rng.normal(size=len(z)));d=d/torch.linalg.vector_norm(d)
            def Hess_d(y):return torch.func.jvp(Hess,(y,),(d,))[1]
            D3=Hess_d(x)
            D4=torch.func.jvp(Hess_d,(x,),(d,))[1]
            for order,A in [(3,D3),(4,D4)]:
                mixed=float((d@A@d).detach())
                reverse=scalar_directional_reverse(original,z,d,order)
                relative=abs(mixed-reverse)/max(abs(reverse),1.)
                result['rows'].append(dict(kind='directional_H',order=order,direction_index=direction_index,mixed_inverse=mixed,pure_reverse_original=reverse,relative_error=relative));save()
                assert relative<2e-9,(order,relative)
        if args.model=='synthetic':
            # Actual native homogeneous a1/a2/a3. Sigma coefficient relation
            # distinguishes homogeneous transport from the source-gauge jet.
            sigma=[None,lambda y:-m.legendre_difference(y)]
            for k in (2,3):
                previous=sigma[-1]
                sigma.append(lambda y,previous=previous,k=k:-torch.func.jvp(previous,(y,),(m.field_tensor(y),))[1]/k)
            for k in (1,2,3):
                before=time.perf_counter();raw=m.coefficient_function(k)(x)
                source=m.source_coefficient_function(k)(x)
                gauge=source-torch.func.grad(sigma[k])(x)
                difference=float(torch.linalg.vector_norm(raw-gauge).detach())
                result['rows'].append(dict(kind='native_homogeneous_source_gauge_coefficient_relation',order=k,raw_norm=float(torch.linalg.vector_norm(raw).detach()),difference_2=difference,seconds=time.perf_counter()-before));save()
                assert difference/max(float(torch.linalg.vector_norm(raw).detach()),1.)<2e-9
        result.update(status='completed',seconds=time.perf_counter()-started);save()
        print(json.dumps(result,indent=2),flush=True)
    except BaseException as exc:
        result.update(status='failed',exception=repr(exc),traceback=traceback.format_exc(),seconds=time.perf_counter()-started);save();raise


if __name__=='__main__':main()
