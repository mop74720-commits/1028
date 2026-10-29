"""Run source-gauge transport and actual numerical Moser midpoint on the ROM.

Outputs retain time-truncation, coefficient-cache, chart, integration and
reference errors separately. Existing frozen stage2/3/4 evidence is read-only.
"""
from pathlib import Path
import argparse,hashlib,json,os,platform,sys,time,traceback
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.linalg import lu_factor,lu_solve
import torch
from transport_native import NativeTransport
from transport_cache import OneFormCache,CachedRepresentedField
from moser_chart import MoserChart

ROOT=Path(__file__).resolve().parents[2]
TOLERANCE=2e-13


def clean(obj):
    if isinstance(obj,np.ndarray):return obj.tolist()
    if isinstance(obj,np.generic):return obj.item()
    raise TypeError(type(obj).__name__)


def native_jet_diagnostics(native,cache,z,times,orders):
    """Compare full native b_j,Db_j against their cached spatial approximations."""
    x=torch.as_tensor(z);f,A,force=native.field_and_jacobian(z)
    native_b=[];native_D=[];costs=[]
    values,jac=cache.coefficient_data(z)
    for r in range(1,max(orders)+1):
        start=time.perf_counter();fun=native.source_coefficient_function(r)
        b=fun(x).detach().numpy();D=torch.func.jacrev(fun)(x).detach().numpy()
        native_b.append(b);native_D.append(D)
        costs.append(dict(order=r,seconds=time.perf_counter()-start,coefficient_cache_error_2=float(np.linalg.norm(values[r-1]-b)),coefficient_derivative_cache_error_2=float(np.linalg.norm(jac[r-1]-D,2))))
    rows=[]
    for r in orders:
        previous=None
        represented=CachedRepresentedField(native,cache,r)
        for t in times:
            b=sum(t**k*native_b[k-1] for k in range(1,r+1))
            Db=sum(t**k*native_D[k-1] for k in range(1,r+1))
            bt=sum(k*t**(k-1)*native_b[k-1] for k in range(1,r+1))
            K=cache.K0+Db.T-Db
            e=-(bt+Db@f+A.T@b+np.r_[force,np.zeros(native.n)])
            exact_jet_field=f-np.linalg.solve(K,e)
            cached,diagnostics=represented.evaluate(t,z,True)
            error=float(np.linalg.norm(exact_jet_field-f))
            rows.append(dict(order=r,time=t,native_time_jet_representation_residual_2=float(np.linalg.norm(e)),native_time_jet_field_error_2=error,
                             additional_coefficient_cache_field_error_2=float(np.linalg.norm(cached-exact_jet_field)),
                             additional_coefficient_cache_representation_residual_2=float(np.linalg.norm(np.asarray(diagnostics['e_B'])-e)),
                             observed_local_time_field_error_order=None if previous is None else float(np.log2(previous/error)),cached=diagnostics))
            previous=error
    return dict(state=np.asarray(z).tolist(),distance_from_cache_center=float(np.linalg.norm(z-cache.center)),coefficient_costs=costs,rows=rows)


def chart_midpoint(native,represented,chart,z0,T,h,diagnose=True):
    y,_,_,_=chart.map(z0,0.,inverse=True,sensitivities=False)
    z=np.asarray(z0);Rold=np.eye(len(z));states=[z.copy()];records=[]
    started=time.perf_counter();eye=np.eye(len(z))
    for k in range(round(T/h)):
        t=k*h;tm=t+h/2;old=y.copy()
        # Only a preconditioner. Acceptance always uses the actual transformed
        # field with numerical Moser rho, D rho and rho_t, and full original H.
        _,A,_=native.field_and_jacobian(z)
        matrix=eye-h*A/2;factor=lu_factor(matrix)
        g=lambda x:chart.transformed_field(tm,x,represented)
        y=old+h*g(old)
        history=[]
        for iteration in range(21):
            residual=y-old-h*g((y+old)/2)
            norm=float(np.linalg.norm(residual,np.inf));history.append(norm)
            if norm<=TOLERANCE:break
            if iteration==20:raise RuntimeError(f'chart midpoint failed, r={represented.order}, h={h}, step={k}, residual={norm}')
            y-=lu_solve(factor,residual)
        znew,Rnew,_,aux=chart.map(y,t+h,sensitivities=True)
        row=dict(step=k,time=t,increment_residual_inf=norm,nonlinear_corrections=iteration,
                 chord_condition=float(np.linalg.cond(matrix)),residual_history=history)
        if diagnose and k==0:
            begin=time.perf_counter();Ag,work=chart.transformed_jacobian(tm,(old+y)/2,represented)
            Cayley=np.linalg.solve(eye-h*Ag/2,eye+h*Ag/2)
            tangent=Rnew@Cayley@np.linalg.inv(Rold)
            Km=chart.cache.data(z,t,represented.order)['K'];Kp=chart.cache.data(znew,t+h,represented.order)['K']
            row.update(K_step_defect_2=float(np.linalg.norm(tangent.T@Kp@tangent-Km,2)),
                       transformed_Hamiltonian_Jacobian_defect_2=float(np.linalg.norm(Ag.T@chart.cache.K0+chart.cache.K0@Ag,2)),
                       actual_implicit_matrix_condition=float(np.linalg.cond(eye-h*Ag/2)),
                       actual_implicit_matrix_min_singular=float(np.linalg.svd(eye-h*Ag/2,compute_uv=False)[-1]),
                       structure_diagnostic_seconds=time.perf_counter()-begin,
                       derivative_scope='Differentiated implicit equation; numerical Moser first/second and time sensitivities; full H AD3. Not finite-iteration program exactness.')
        z=znew;Rold=Rnew;states.append(z.copy());records.append(row)
    return np.asarray(states),dict(seconds=time.perf_counter()-started,records=records,
                                   max_residual_inf=max(r['increment_residual_inf'] for r in records),steps=len(records))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',choices=['synthetic','fullcoil_collocated'],default='synthetic')
    parser.add_argument('--maximum-order',type=int,default=3)
    parser.add_argument('--quadratic-through',type=int,default=2)
    parser.add_argument('--duration',type=float,default=.0005)
    parser.add_argument('--points-only',action='store_true')
    parser.add_argument('--skip-probe',action='store_true')
    parser.add_argument('--run-id',default='main')
    parser.add_argument('--ad-backend',choices=['inverse','original'],default='inverse')
    args=parser.parse_args();torch.set_num_threads(1)
    out=ROOT/'stage5/results/transport'/args.model;out.mkdir(parents=True,exist_ok=True)
    destination=out/f'{args.run_id}.json'
    if destination.exists():raise FileExistsError(f'Preserve previous evidence: choose a new --run-id rather than overwriting {destination}')
    start=time.perf_counter();report=dict(status='running',command=' '.join(sys.argv),python=sys.version,platform=platform.platform(),versions=dict(numpy=np.__version__,scipy=scipy.__version__,torch=torch.__version__),rows=[],phases=[],solver_tolerance=TOLERANCE)
    save=lambda:destination.write_text(json.dumps(report,indent=2,default=clean)+'\n')
    save()
    try:
        sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*transport*.py')}
        sources['moser_chart.py']=hashlib.sha256((Path(__file__).parent/'moser_chart.py').read_bytes()).hexdigest()
        report['source_sha256_at_start']=sources
        snapshot=out/f'{args.run_id}_source_used';snapshot.mkdir(exist_ok=True)
        for name in sources:(snapshot/name).write_bytes((Path(__file__).parent/name).read_bytes())
        if args.model=='synthetic':native=NativeTransport(ad_backend=args.ad_backend)
        else:
            from coil_rom import CoilROM
            base=CoilROM()
            native=NativeTransport(base=base,kind='fullcoil_collocated',ad_backend=args.ad_backend)
            def force(z):
                G=base.current_port_tensor(z[:base.n]);velocity=native._gradH(z)[base.n:]
                return -base.collocated_gain*G@(G.T@velocity)
            native.force_override=force
            sources['coil_rom.py']=hashlib.sha256((Path(__file__).parent/'coil_rom.py').read_bytes()).hexdigest()
            (snapshot/'coil_rom.py').write_bytes((Path(__file__).parent/'coil_rom.py').read_bytes())
        z0=native.base.initial_state(.01);T=args.duration;orders=list(range(1,args.maximum_order+1))
        report.update(metadata=native.metadata(),initial_state=z0,duration_tau=T,orders=orders)
        fingerprint_payload=dict(center=z0.tolist(),model=native.metadata(),sources=sources,maximum_order=args.maximum_order,quadratic_through=args.quadratic_through,ad_backend=args.ad_backend,
                                 gain=getattr(native.base,'collocated_gain',None))
        fingerprint=hashlib.sha256(json.dumps(fingerprint_payload,sort_keys=True,default=clean).encode()).hexdigest()
        cachepath=out/f'cache_r{args.maximum_order}_q{args.quadratic_through}_{args.ad_backend}_{fingerprint[:12]}.npz'
        report['cache_fingerprint']=fingerprint
        if cachepath.exists():
            cache=OneFormCache.load(cachepath)
            if cache.metadata.get('fingerprint')!=fingerprint:raise ValueError('Cache provenance mismatch')
            report['cache_reused']=str(cachepath.relative_to(ROOT))
        else:
            def progress(row):report['phases'].append(dict(cache=row));save();print('CACHE',json.dumps(row),flush=True)
            cache=OneFormCache.fit(native,z0,maximum_order=args.maximum_order,quadratic_through=args.quadratic_through,progress=progress)
            cache.metadata.update(fingerprint=fingerprint,fingerprint_payload=fingerprint_payload)
            cache.save(cachepath)
        report['cache']=cache.metadata;save()
        print('NATIVE_POINT_CENTER',flush=True)
        report['native_center']=native_jet_diagnostics(native,cache,z0,[T,T/2,T/4,T/8],orders);save()
        if not args.skip_probe:
            probe=z0+.75*T*native.field(z0)
            print('NATIVE_POINT_OFF_CENTER',flush=True)
            report['native_off_center']=native_jet_diagnostics(native,cache,probe,[T,T/2],orders);save()
        report['moser']=[]
        for r in orders:
            chart=MoserChart(cache,r)
            diag=chart.diagnostics(z0,T)
            refined=MoserChart(cache,r,rtol=3e-13,atol=3e-15,max_step=.125)
            coarse_y=chart.map(z0,T,inverse=True)[0];fine_y=refined.map(z0,T,inverse=True)[0]
            diag.update(order=r,tolerance_refinement_chart_difference_2=float(np.linalg.norm(coarse_y-fine_y)))
            report['moser'].append(diag);save();print('MOSER',r,diag['chart_matching_2'],flush=True)
        if args.points_only:
            report.update(status='completed_points_only',elapsed_seconds=time.perf_counter()-start);save();return
        # Use the independently computed same-field full-coil reference if it is
        # available; this is shared data, not an exact-flow algorithm ingredient.
        shared=ROOT/'stage5/results/closed_loop/shared_collocated_reference.npz'
        shared_data=np.load(shared) if args.model=='fullcoil_collocated' and shared.exists() else None
        if shared_data is not None and 'collocated_reference_states' in shared_data:
            grid=shared_data['collocated_reference_times'];original=shared_data['collocated_reference_states']
            assert abs(grid[-1]-T)<1e-15
            report['original_reference']=dict(source=str(shared.relative_to(ROOT)),scope='same actual fullcoil collocated field; independent tolerances and refinement in closed_loop/results.json',field_equality_protocol='same fixed bias, gain, partial-current force and initial_state')
        else:
            grid=np.linspace(0,T,65);refs=[]
            for rtol,atol,step in [(2e-10,2e-12,T/4),(5e-12,5e-14,T/8)]:
                before=time.perf_counter();sol=solve_ivp(lambda t,z:native.field(z),(0,T),z0,method='DOP853',rtol=rtol,atol=atol,max_step=step,dense_output=True)
                if not sol.success:raise RuntimeError(sol.message)
                refs.append(sol);report['phases'].append(dict(original_reference=dict(rtol=rtol,atol=atol,max_step=step,nfev=sol.nfev,seconds=time.perf_counter()-before)));save()
            original=refs[-1].sol(grid).T
            report['original_reference']=dict(refinement_max=float(np.max(np.linalg.norm(refs[0].sol(grid).T-original,axis=1))),scope='DOP853 original full-M field, independent of one-form cache')
        traces=dict(reference_times=grid,original_reference=original)
        npzpath=out/f'{args.run_id}_traces.npz';np.savez_compressed(npzpath,**traces);save()
        report['represented_references']=[]
        for r in orders:
            represented=CachedRepresentedField(native,cache,r);sols=[]
            for rtol,atol,step in [(2e-10,2e-12,T/4),(5e-12,5e-14,T/8)]:
                print('REFERENCE_REPRESENTED',r,rtol,flush=True);before=time.perf_counter()
                sol=solve_ivp(represented,(0,T),z0,method='DOP853',rtol=rtol,atol=atol,max_step=step,dense_output=True)
                if not sol.success:raise RuntimeError(sol.message)
                sols.append(sol);report['represented_references'].append(dict(order=r,rtol=rtol,atol=atol,max_step=step,nfev=sol.nfev,seconds=time.perf_counter()-before));save()
            ra=sols[-1].sol(grid).T;traces[f'represented_reference_r{r}']=ra
            report.setdefault('model_gaps',[]).append(dict(order=r,represented_reference_refinement_max=float(np.max(np.linalg.norm(sols[0].sol(grid).T-ra,axis=1))),represented_original_reference_gap=float(np.max(np.linalg.norm(ra-original,axis=1)))))
            save();np.savez_compressed(npzpath,**traces)
            previous=None
            for steps in [4,8,16]:
                h=T/steps;chart=MoserChart(cache,r)
                print('INTEGRATE',r,steps,flush=True)
                states,info=chart_midpoint(native,represented,chart,z0,T,h,diagnose=(steps==4))
                times=np.arange(steps+1)*h;stride=(len(grid)-1)//steps
                assert (len(grid)-1)%steps==0
                ea=float(np.max(np.linalg.norm(states-sols[-1].sol(times).T,axis=1)))
                eo=float(np.max(np.linalg.norm(states-original[::stride],axis=1)))
                row=dict(order=r,h=h,error_to_represented_max=ea,error_to_original_max=eo,
                         observed_order_to_represented=None if previous is None else float(np.log2(previous/ea)),
                         auxiliary_calls=chart.calls,auxiliary_nfev=chart.nfev,auxiliary_seconds=chart.seconds,**info)
                report['rows'].append(row);previous=ea;traces[f'chart_r{r}_steps{steps}']=states
                save();np.savez_compressed(npzpath,**traces);print('ROW',json.dumps({k:v for k,v in row.items() if k!='records'}),flush=True)
        report.update(status='completed',elapsed_seconds=time.perf_counter()-start)
        report['source_sha256']=sources
        save()
    except BaseException as exc:
        report.update(status='failed',exception=repr(exc),traceback=traceback.format_exc(),elapsed_seconds=time.perf_counter()-start);save();raise


if __name__=='__main__':main()
