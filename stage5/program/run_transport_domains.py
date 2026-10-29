"""Exact-structure regression and declared numerical Moser domain probes.

No physical trajectory is replaced by an analytic-flow oracle. The canonical
and proportional identities below are evaluated on the full nonlinear rod.
The cached Moser probes test a local numerical construction, not a global chart.
"""
from pathlib import Path
import argparse, hashlib, json, platform, sys, time, traceback
import numpy as np
from transport_native import NativeTransport
from transport_cache import OneFormCache
from moser_chart import MoserChart

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='inverse_verified');p.add_argument('--output-id');args=p.parse_args()
    destination=ROOT/'stage5/results/transport'/f'{args.output_id or args.run_id}_domains.json'
    if destination.exists():raise FileExistsError(destination)
    start=time.perf_counter()
    report=dict(status='running',command=sys.argv,python=sys.version,platform=platform.platform(),regressions=[],probes=[],limitations='Finite numerical samples and sufficient bounds of the cached polynomial. Not global physical-domain certificates.')
    report['source_sha256']={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ['run_transport_domains.py','transport_native.py','transport_cache.py','moser_chart.py']}
    save=lambda:destination.write_text(json.dumps(report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n')
    save()
    for kind in ['conservative','proportional']:
        model=NativeTransport(kind=kind);z=model.base.initial_state(.01)
        f,A,R=model.field_and_jacobian(z);K0=model.base.K0;gamma=0. if kind=='conservative' else .2
        gradH=-model.base.J@model.base.field(z)
        alpha=np.r_[z[model.n:],np.zeros(model.n)]
        for t in [0.,.0005,.005]:
            factor=np.exp(gamma*t);K=factor*K0;at=gamma*factor*alpha
            e=K@f-factor*gradH-at
            compatibility=gamma*K+A.T@K+K@A
            report['regressions'].append(dict(kind=kind,time=t,representation_residual_2=float(np.linalg.norm(e)),transport_compatibility_2=float(np.linalg.norm(compatibility,2)),K_condition=float(np.linalg.cond(K)),formula='K=exp(gamma*t) K0, a=exp(gamma*t)(P,0), B=exp(gamma*t) H; gamma=0 conservative'))
        save()
    for modelname in ['synthetic','fullcoil_collocated']:
        runfile=ROOT/'stage5/results/transport'/modelname/f'{args.run_id}.json'
        run=json.loads(runfile.read_text());cachepath=runfile.parent/next(p.name for p in runfile.parent.glob('cache_*.npz') if run['cache_fingerprint'][:12] in p.name)
        cache=OneFormCache.load(cachepath)
        for order in run['orders']:
            for t in [.0005,.002,.01,.05,.2]:
                row=dict(model=modelname,order=order,time=t,cache=str(cachepath.relative_to(ROOT)))
                try:row.update(status='completed',diagnostics=MoserChart(cache,order).diagnostics(cache.center,t))
                except Exception as exc:row.update(status='failed',error=repr(exc),traceback=traceback.format_exc())
                report['probes'].append(row);save()
        # Deliberate outside-domain rejection is an independent guard test;
        # it does not imply failure of a physical system or the Moser theorem.
        z=cache.center.copy();z[0]+=.0021
        row=dict(model=modelname,order=1,time=.0005,probe='explicit point outside declared radius .002')
        try:MoserChart(cache,1).map(z,.0005);row.update(status='unexpected_acceptance')
        except ValueError as exc:row.update(status='expected_domain_rejection',error=repr(exc))
        report['probes'].append(row);save()
    report.update(status='completed',seconds=time.perf_counter()-start);save()

if __name__=='__main__':main()
