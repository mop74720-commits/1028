"""Retained full-coil higher-AD diagnostic; records failures without hiding them."""
from pathlib import Path
import argparse,json,time,traceback,hashlib
import numpy as np
import torch
from coil_rom import CoilROM
from transport_native import NativeTransport

def main():
    p=argparse.ArgumentParser();p.add_argument('--method',choices=['reverse','forward_reverse'],default='reverse');p.add_argument('--label',default='reverse_first');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=root/'results/transport/fullcoil_collocated';out.mkdir(parents=True,exist_ok=True)
    destination=out/f'ad_{args.label}.json'
    if destination.exists():raise FileExistsError(destination)
    result=dict(method=args.method,status='running',coil_sha256=hashlib.sha256((Path(__file__).parent/'coil_rom.py').read_bytes()).hexdigest())
    destination.write_text(json.dumps(result,indent=2)+'\n');start=time.perf_counter()
    try:
        base=CoilROM();n=base.n
        def force(z):
            G=base.current_port_tensor(z[:n]);v=torch.func.grad(base.hamiltonian_tensor)(z)[n:]
            return -base.collocated_gain*G@(G.T@v)
        model=NativeTransport(base=base,force=force)
        function=model.source_coefficient_function(1)
        op=torch.func.jacrev(torch.func.jacrev(function)) if args.method=='reverse' else torch.func.jacfwd(torch.func.jacrev(function))
        value=op(torch.as_tensor(base.initial_state())).detach().numpy()
        np.save(out/f'ad_{args.label}_D2b1.npy',value)
        result.update(status='completed',norm=float(np.linalg.norm(value)),symmetry_max=float(np.max(np.abs(value-value.swapaxes(1,2)))))
    except BaseException as exc:result.update(status='failed',exception=repr(exc),traceback=traceback.format_exc())
    result['seconds']=time.perf_counter()-start
    destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
