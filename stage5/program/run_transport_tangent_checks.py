"""Independent directional checks of the actual 24D transformed field.

Finite differences call the complete map/field again, including its time term.
This complements cheap polynomial unit tests and does not assert a uniform bound.
"""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np
import torch
from transport_native import NativeTransport
from transport_cache import OneFormCache,CachedRepresentedField
from moser_chart import MoserChart
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='inverse_verified');args=p.parse_args()
    out=ROOT/'stage5/results/transport';destination=out/f'{args.run_id}_tangents.json'
    if destination.exists():raise FileExistsError(destination)
    start=time.perf_counter();report=dict(status='running',command=sys.argv,source_sha256={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ['run_transport_tangent_checks.py','transport_native.py','transport_cache.py','moser_chart.py','coil_rom.py']},models=[])
    save=lambda:destination.write_text(json.dumps(report,indent=2)+'\n');save();arrays={}
    for name in ['synthetic','fullcoil_collocated']:
        main=json.loads((out/name/f'{args.run_id}.json').read_text());order=max(main['orders']);cache=OneFormCache.load(next((out/name).glob(f"cache_*_{main['cache_fingerprint'][:12]}.npz")))
        if name=='synthetic':native=NativeTransport()
        else:
            from coil_rom import CoilROM
            base=CoilROM();native=NativeTransport(base=base,kind='fullcoil_collocated')
            def force(z):
                G=base.current_port_tensor(z[:base.n]);return -base.collocated_gain*G@(G.T@native._gradH(z)[base.n:])
            def numeric_force(z):
                G=base.current_port_tensor(z[:base.n]);return -base.collocated_gain*G@(G.T@torch.func.grad(base.hamiltonian_tensor)(z)[base.n:])
            native.force_override=force;native.numeric_force_override=numeric_force
        z=cache.center;t=main['duration_tau']/2;chart=MoserChart(cache,order,rtol=3e-13,atol=3e-15,max_step=.125);field=CachedRepresentedField(native,cache,order)
        y,Dchi,chit,_=chart.map(z,t,inverse=True);Ag,_=chart.transformed_jacobian(t,y,field)
        a=cache.data(z,t,order);fa=field(t,z);Aa=field.jacobian(t,z)
        compatibility=a['Kt']+np.einsum('ijk,k->ij',a['DK'],fa)+Aa.T@a['K']+a['K']@Aa
        row=dict(model=name,order=order,time=t,represented_transport_compatibility_2=float(np.linalg.norm(compatibility,2)),transformed_hamiltonian_jacobian_defect_2=float(np.linalg.norm(Ag.T@cache.K0+cache.K0@Ag,2)),directions=[],time_finite_difference=[])
        for j,direction in enumerate([np.eye(cache.d)[0],np.random.default_rng(1025).normal(size=cache.d)]):
            direction/=np.linalg.norm(direction)
            for eps in [1e-6,5e-7]:
                fd=(chart.transformed_field(t,y+eps*direction,field)-chart.transformed_field(t,y-eps*direction,field))/(2*eps)
                row['directions'].append(dict(index=j,epsilon=eps,absolute_error_2=float(np.linalg.norm(fd-Ag@direction)),relative_error=float(np.linalg.norm(fd-Ag@direction)/max(np.linalg.norm(Ag@direction),1e-300))))
        for eps in [1e-6,5e-7]:
            fd=(chart.map(z,t+eps,inverse=True,sensitivities=False)[0]-chart.map(z,t-eps,inverse=True,sensitivities=False)[0])/(2*eps)
            row['time_finite_difference'].append(dict(epsilon=eps,absolute_error_2=float(np.linalg.norm(fd-chit)),relative_error=float(np.linalg.norm(fd-chit)/max(np.linalg.norm(chit),1e-300))))
        arrays[f'{name}_Ag']=Ag;arrays[f'{name}_A_represented']=Aa;arrays[f'{name}_chi_t']=chit
        report['models'].append(row);save();np.savez_compressed(out/f'{args.run_id}_tangents.npz',**arrays)
    report.update(status='completed',seconds=time.perf_counter()-start);save()

if __name__=='__main__':main()
