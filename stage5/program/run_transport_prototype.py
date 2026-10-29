"""Incrementally record native derivative/transport costs before large runs."""
from pathlib import Path
import argparse,json,os,resource,time,traceback
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
import numpy as np
import torch
from transport_native import NativeTransport

OUT=Path(__file__).resolve().parents[1]/'results/transport'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--max-order',type=int,default=2)
    parser.add_argument('--jac-order',type=int,default=1)
    parser.add_argument('--source-gauge',action='store_true')
    parser.add_argument('--third-H',action='store_true')
    parser.add_argument('--hess-order',type=int,default=0)
    args=parser.parse_args()
    torch.set_num_threads(1)
    OUT.mkdir(parents=True,exist_ok=True)
    report=dict(status='running',pid=os.getpid(),rows=[],max_order=args.max_order,jac_order=args.jac_order)
    tag=f'r{args.max_order}_jac{args.jac_order}'+('_source' if args.source_gauge else '')+('_thirdH' if args.third_H else '')+(f'_hess{args.hess_order}' if args.hess_order else '')
    destination=OUT/f'prototype_{tag}.json'
    save=lambda:destination.write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        start=time.perf_counter();model=NativeTransport();z=torch.tensor(model.base.initial_state())
        report.update(initialization_seconds=time.perf_counter()-start,metadata=model.metadata(),initial_state=z.tolist());save()
        tasks=[('field',model.field_tensor),('field_jacobian',torch.func.jacrev(model.field_tensor))]
        cf=model.source_coefficient_function if args.source_gauge else model.coefficient_function
        label='b' if args.source_gauge else 'a'
        tasks += [(f'{label}{k}',cf(k)) for k in range(1,args.max_order+1)]
        tasks += [(f'D{label}{k}',torch.func.jacrev(cf(k))) for k in range(1,args.jac_order+1)]
        tasks += [(f'D2{label}{k}',torch.func.jacfwd(torch.func.jacrev(cf(k)))) for k in range(1,args.hess_order+1)]
        if args.third_H:
            tasks.append(('H3',torch.func.jacfwd(torch.func.jacrev(torch.func.grad(model.base.hamiltonian_tensor)))))
        for name,fun in tasks:
            report['current_task']=name;save();print('START',name,flush=True)
            start=time.perf_counter();out=fun(z).detach().numpy()
            row=dict(name=name,seconds=time.perf_counter()-start,shape=list(out.shape),norm=float(np.linalg.norm(out)),max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            report['rows'].append(row);save();np.save(OUT/f'prototype_{tag}_{name}.npy',out)
            print(json.dumps(row),flush=True)
        report['status']='completed';save()
    except BaseException as exc:
        report.update(status='failed',exception=repr(exc),traceback=traceback.format_exc());save();raise

if __name__=='__main__':main()
