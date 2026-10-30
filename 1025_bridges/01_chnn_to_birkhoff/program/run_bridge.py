"""Actual minimal B01 experiment; no training, Moser chart or new integrator."""
import argparse
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,json,platform,sys,time,traceback
from pathlib import Path
import numpy as np
import scipy
from scipy.integrate import solve_ivp
import torch
from bridge_interface import (ROOT,ROMBridge,LearnedIdealBase,GeneralHamiltonianTransport,
    NativeTransport,OneFormCache,LearnedRepresentedField,fit_network_cache,
    tensor_data,independent_pair_diagnostics)

BASE=Path(__file__).resolve().parents[1]
OLD_CACHE=ROOT/'stage5/results/transport/synthetic/cache_r3_q2_inverse_3c8879dd39a6.npz'


def exact_cache_domain(cache,T=Fraction(1,2000),radius=Fraction(1,500)):
    """Rational row/column bound for the saved polynomial, NOT true-error bound.

    All saved float coefficients are interpreted as their exact binary rationals.
    On |z-center|_infty<=r, 0<=t<=T, ||K-K0||2 <= max(||.||1,||.||inf).
    """
    F=lambda x:Fraction(float(x));d=cache.d
    bound=[[Fraction(0) for _ in range(d)] for _ in range(d)]
    for k in range(cache.maximum_order):
        J=cache.jacobians[k];H=cache.hessians[k]
        for i in range(d):
            for j in range(d):
                value=abs(F(J[j,i])-F(J[i,j]))
                value+=radius*sum((abs(F(H[j,i,l])-F(H[i,j,l])) for l in range(d)),Fraction(0))
                bound[i][j]+=T**(k+1)*value
    rho=max(max(sum(row,Fraction(0)) for row in bound),
            max(sum((bound[i][j] for i in range(d)),Fraction(0)) for j in range(d)))
    return dict(interpretation='Exact rational bound for the fixed saved cache polynomial; not a true network/ROM error certificate or floating execution enclosure.',
        time_interval=[0,str(T)],state_box_half_width=str(radius),
        perturbation_bound_exact=str(rho),perturbation_bound=float(rho),
        minimum_singular_lower_exact=str(1-rho),minimum_singular_lower=float(1-rho),
        nondegenerate=bool(rho<1))


def convert(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='B01_run01');args=p.parse_args()
    out=BASE/'results'/args.run_id
    if out.exists():raise FileExistsError('Choose new run-id; preserve failures and results')
    out.mkdir(parents=True);start=time.perf_counter()
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
    record=dict(status='running',command=sys.argv,started_utc=datetime.now(timezone.utc).isoformat(),
        environment=dict(python=sys.version,numpy=np.__version__,torch=torch.__version__,scipy=scipy.__version__,platform=platform.platform()),
        scope='CHNN -> same explicit phase field -> Birkhoff only; no training, KAM or endpoint-generator research.',
        source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
            for folder in [BASE/'program',BASE/'tests'] for f in folder.glob('*.py')})
    def save():
        (out/'report.json').write_text(json.dumps(record,default=convert,indent=2,allow_nan=False)+'\n')
    try:
        physical=ROMBridge();learned=LearnedIdealBase(physical)
        native=GeneralHamiltonianTransport(learned)
        old=OneFormCache.load(OLD_CACHE);center=old.center.copy();T=.0005;radius=.002
        # Same S5 initial state and time window; no changes to physical parameters.
        probe=np.load(ROOT/'stage5/results/transport/synthetic/inverse_verified_traces.npz')['original_reference'][-1].copy()
        record.update(model=learned.metadata(),load=native.metadata(),initial_state=center,
            time_window_tau=[0,T],time_window_seconds=[0,T/physical.rom.omega0],
            cache_center_source=str(OLD_CACHE.relative_to(ROOT)),old_cache_sha256=hashlib.sha256(OLD_CACHE.read_bytes()).hexdigest(),
            physical_metadata=physical.metadata(),local_radius=radius,probe=probe)
        cache=fit_network_cache(native,center,lambda x:print(json.dumps(x),flush=True));cache.save(out/'cache_r2.npz')
        record['cache']=cache.metadata
        record['cache_reuse_check']=dict(b1_difference=float(np.linalg.norm(cache.values[0]-old.values[0])),
            b2_difference=float(np.linalg.norm(cache.values[1]-old.values[1])),
            interpretation='Only algorithm and same-load b1 inherited; H-dependent b2 recomputed for the network.')
        record['cache_domain']=exact_cache_domain(cache)
        record['floating_ball_bound']=cache.ball_bounds(T,2,radius)
        record['physical_mass']=dict(min_eigen_center=float(np.linalg.eigvalsh(physical.mass(center[:12]))[0]),
            variation_from_origin=float(np.linalg.norm(physical.mass(center[:12])-physical.mass(np.zeros(12)))))
        # Exact canonical baseline and known exact proportional-load regression.
        baseline=[]
        for name,z in [('center',center),('old_physical_endpoint',probe)]:
            x=torch.tensor(z);g=torch.func.grad(learned.hamiltonian_tensor)(x).detach().numpy()
            f=learned.field(z);a0=np.r_[z[12:],np.zeros(12)]
            gamma=.2;factor=np.exp(gamma*T)
            fd=f+np.r_[np.zeros(12),-gamma*z[12:]]
            baseline.append(dict(point=name,canonical_residual=float(np.linalg.norm(physical.K0@f-g)),
                canonical_closed=True,canonical_sigma_min=1.,canonical_power=float(g@f),
                proportional_exact_residual=float(np.linalg.norm(factor*physical.K0@fd-factor*g-gamma*factor*a0)),
                learned_Hpp_min=float(torch.linalg.eigvalsh(torch.autograd.functional.hessian(learned.hamiltonian_tensor,x)[12:,12:])[0])))
        record['exact_baselines']=baseline
        rows=[];native_rows=[]
        for name,z in [('center',center),('old_physical_endpoint',probe)]:
            for r in (1,2):
                for t in (T,T/2,T/4,T/8):
                    d=independent_pair_diagnostics(native,physical,cache,z,t,r);d['point']=name;rows.append(d)
                    a=tensor_data(native,z,t,r)
                    native_rows.append(dict(point=name,order=r,time=t,native_eB=float(np.linalg.norm(a['eB'])),
                        native_field_representation_error=float(np.linalg.norm(np.linalg.solve(a['K'],a['eB']))),
                        cache_eB_difference=float(np.linalg.norm(np.asarray(d['e_B'])-a['eB'])),
                        native_cache_form_difference=float(np.linalg.norm(a['b']-cache.data(z,t,r)['b']))))
            print('point diagnostics',name,flush=True)
        record['point_diagnostics']=rows;record['native_vs_cache']=native_rows
        record['observed_native_time_orders']={f'{point}_r{r}':[float(np.log2(vals[i]/vals[i+1])) for i in range(3)]
            for point in ('center','old_physical_endpoint') for r in (1,2)
            for vals in [[x['native_eB'] for x in native_rows if x['point']==point and x['order']==r]]}
        save()
        # Independent convergence/refinement of each field; no common-reference conflation.
        represented=LearnedRepresentedField(native,cache,2)
        force=lambda z:native.force_tensor(torch.as_tensor(z,dtype=torch.float64)).detach().numpy()
        fields={'truth':lambda t,z:physical.field(z)+np.r_[np.zeros(12),force(z)],
                'learned':lambda t,z:native.field(z),'represented':represented}
        grid=np.linspace(0,T,17);arrays={'time_tau':grid};integrations=[]
        for name,field in fields.items():
            for level,rtol,atol,max_step in [('base',2e-10,2e-12,T/4),('fine',5e-12,5e-14,T/8)]:
                begin=time.perf_counter()
                sol=solve_ivp(field,(0,T),center,method='DOP853',rtol=rtol,atol=atol,max_step=max_step,t_eval=grid)
                if not sol.success:raise RuntimeError(name+': '+sol.message)
                arrays[name+'_'+level]=sol.y.T
                integrations.append(dict(field=name,level=level,method='DOP853',rtol=rtol,atol=atol,max_step=max_step,
                    nfev=sol.nfev,seconds=time.perf_counter()-begin))
                print('integrated',name,level,flush=True)
        np.savez_compressed(out/'trajectories.npz',**arrays)
        truth=arrays['truth_fine'];pred=arrays['learned_fine'];rep=arrays['represented_fine']
        record['integration']=dict(runs=integrations,
            refinement_max={n:float(np.max(np.linalg.norm(arrays[n+'_fine']-arrays[n+'_base'],axis=1))) for n in fields},
            learned_vs_true_max=float(np.max(np.linalg.norm(pred-truth,axis=1))),
            represented_vs_learned_max=float(np.max(np.linalg.norm(rep-pred,axis=1))),
            represented_vs_true_max=float(np.max(np.linalg.norm(rep-truth,axis=1))),
            trajectory_split_identity=float(np.max(np.abs((rep-truth)-((rep-pred)+(pred-truth))))),
            max_cache_distance=float(np.max(np.linalg.norm(rep-center,axis=1))),
            interpretation='Distinct finite-window numerical errors, not uniform domain learning bounds; no integrator-order claim here.')
        tolerances=dict(split_identity=2e-12,direct_eB=2e-12,represented_compatibility=2e-9,closure=2e-12,power=2e-12)
        checks=dict(split=all(r['split_identity_defect']<tolerances['split_identity'] for r in rows),
            direct=all(r['direct_vs_inherited_eB']<tolerances['direct_eB'] for r in rows),
            compatibility=all(r['represented_compatibility_max']<tolerances['represented_compatibility'] for r in rows),
            closure=all(r['closure_max']<tolerances['closure'] for r in rows),
            power=all(max(r['true_power_identity'],r['learned_power_identity'])<tolerances['power'] for r in rows),
            domain=record['cache_domain']['nondegenerate'] and record['integration']['max_cache_distance']<radius)
        record.update(status='passed' if all(checks.values()) else 'failed_checks',checks=checks,tolerances=tolerances,
            elapsed_seconds=time.perf_counter()-start,finished_utc=datetime.now(timezone.utc).isoformat())
        save();print(json.dumps(dict(status=record['status'],checks=checks,integration=record['integration']),indent=2),flush=True)
        if not all(checks.values()):raise RuntimeError(checks)
    except Exception as exc:
        record.update(status='failed',error=repr(exc),traceback=traceback.format_exc(),elapsed_seconds=time.perf_counter()-start)
        save();raise


if __name__=='__main__':main()
