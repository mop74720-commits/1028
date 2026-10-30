"""Actual nonautonomous full-coil experiment; stage5 algorithms are reused."""
from pathlib import Path
import argparse,hashlib,json,os,platform,sys,time,traceback,csv
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import numpy as np
import scipy
from scipy.integrate import solve_ivp
import torch
from nonautonomous_transport import (ROOT,TimeGainCoilTransport,TimeGainRepresentedField,
    inherit_second_order_cache,MoserChart)
from run_transport_experiments import chart_midpoint,clean,TOLERANCE
from closed_loop import implicit_midpoint


def native_point(native,cache,oldcache,z,times):
    x=torch.as_tensor(z);coeff=[];deriv=[];cost=[]
    cv,cD=cache.coefficient_data(z)
    for k in (1,2):
        start=time.perf_counter();fun=native.source_coefficient_function(k)
        b=fun(x).detach().numpy();D=torch.func.jacrev(fun)(x).detach().numpy()
        coeff.append(b);deriv.append(D)
        cost.append(dict(order=k,seconds=time.perf_counter()-start,
            cache_value_error_2=float(np.linalg.norm(cv[k-1]-b)),
            cache_Jacobian_error_2=float(np.linalg.norm(cD[k-1]-D,2))))
    rows=[]
    for order in (1,2):
        previous=None
        for t in times:
            f,A,R=native.field_and_jacobian_at(t,z)
            b=sum(t**k*coeff[k-1] for k in range(1,order+1))
            Db=sum(t**k*deriv[k-1] for k in range(1,order+1))
            bt=sum(k*t**(k-1)*coeff[k-1] for k in range(1,order+1))
            K=cache.K0+Db.T-Db
            S=bt+Db@f+A.T@b+np.r_[R,np.zeros(native.n)]
            native_delta=np.linalg.solve(K,S)
            cached,diag=TimeGainRepresentedField(native,cache,order).evaluate(t,z,True)
            _,bad=TimeGainRepresentedField(native,oldcache,order).evaluate(t,z,True)
            error=float(np.linalg.norm(native_delta))
            rows.append(dict(order=order,time=t,native_representation_residual_2=float(np.linalg.norm(S)),
                native_field_error_2=error,native_observed_time_order=None if previous is None else float(np.log2(previous/error)),
                additional_spatial_cache_field_error_2=float(np.linalg.norm(cached-f-native_delta)),
                cached=diag,omitted_time_force_coefficient=bad))
            previous=error
    return dict(state=z,coefficient_checks=cost,rows=rows)


def midpoint(native,z0,T,steps):
    states=[z0];records=[];h=T/steps;start=time.perf_counter()
    for k in range(steps):
        tm=(k+.5)*h
        class FixedTime:
            def field(self,_unused,z):return native.field(z,tm)
            def jacobian(self,z):return native.field_and_jacobian_at(tm,z)[1]
        z,D,info=implicit_midpoint(FixedTime(),states[-1],h,tolerance=TOLERANCE)
        a=states[-1];mid=(a+z)/2
        grad=torch.func.grad(native.base.hamiltonian_tensor)(torch.as_tensor(mid)).detach().numpy()
        ideal=float(grad@native.field(mid,tm))
        info['discrete_H_power_residual']=float((native.base.hamiltonian(z)-native.base.hamiltonian(a))/h-ideal)
        states.append(z);records.append(info)
    return np.asarray(states),dict(seconds=time.perf_counter()-start,records=records,
        max_residual_inf=max(r['increment_residual_inf'] for r in records))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='time_gain_r2');parser.add_argument('--points-only',action='store_true')
    parser.add_argument('--reuse-reference-run',help='Reuse completed point diagnostics and two-tolerance reference arrays after a reporting failure; hash-verified physical/cache modules.')
    args=parser.parse_args();torch.set_num_threads(1)
    out=ROOT/'stage6/fusion_reconciliation/results/algorithms';out.mkdir(parents=True,exist_ok=True)
    dest=out/f'{args.run_id}.json'
    if dest.exists():raise FileExistsError('Preserve old evidence; select a new run-id')
    started=time.perf_counter();report=dict(status='running',command=[sys.executable,*sys.argv],python=sys.version,
        platform=platform.platform(),versions=dict(numpy=np.__version__,scipy=scipy.__version__,torch=torch.__version__),
        environment={k:os.environ.get(k) for k in ['PYTHONDONTWRITEBYTECODE','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']},
        implicit_tolerance=TOLERANCE,phases=[],rows=[])
    save=lambda:dest.write_text(json.dumps(report,indent=2,default=clean)+'\n');save()
    try:
        paths=[Path(__file__),Path(__file__).with_name('nonautonomous_transport.py')]+[ROOT/'stage5/program'/n for n in ['coil_rom.py','transport_native.py','transport_cache.py','moser_chart.py','run_transport_experiments.py','closed_loop.py']]
        report['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        native=TimeGainCoilTransport();cache,oldcache=inherit_second_order_cache(native)
        cache.save(out/f'{args.run_id}_cache.npz');z0=cache.center.copy();T=.0005
        report.update(metadata=native.metadata(),cache_metadata=cache.metadata,initial_state=z0,duration_tau=T,duration_seconds=T/native.base.rom.omega0)
        previous_report=None
        if args.reuse_reference_run:
            previous_report=json.loads((out/f'{args.reuse_reference_run}.json').read_text())
            for name,digest in report['source_sha256'].items():
                if name!=str(Path(__file__).relative_to(ROOT)) and previous_report['source_sha256'][name]!=digest:
                    raise ValueError('Physical/cache source differs from reference')
            np.testing.assert_array_equal(previous_report['initial_state'],z0)
            assert previous_report['duration_tau']==T and previous_report['metadata']==report['metadata']
            for key in ['native_center','native_probe','moser']:report[key]=previous_report[key]
            report['reused_reference_run']=dict(source=args.reuse_reference_run,sha256=hashlib.sha256((out/f'{args.reuse_reference_run}.json').read_bytes()).hexdigest(),reason='Unchanged numerical kernels; preceding run stopped only at duplicate steps keyword in result assembly. Failure retained.')
        else:
            print('NATIVE_CENTER',flush=True);report['native_center']=native_point(native,cache,oldcache,z0,[T,T/2,T/4,T/8]);save()
            print('NATIVE_PROBE',flush=True);probe=z0+.75*T*native.field(z0)
            report['native_probe']=native_point(native,cache,oldcache,probe,[T,T/2]);save()
            report['moser']=[]
            for r in (1,2):
                chart=MoserChart(cache,r);diag=chart.diagnostics(z0,T);diag['order']=r
                report['moser'].append(diag);save();print('MOSER',r,diag['chart_matching_2'],flush=True)
        if args.points_only:
            report.update(status='completed_points_only',elapsed_seconds=time.perf_counter()-started);save();return
        grid=np.linspace(0,T,33);traces=dict(reference_times=grid)
        originals=[];represented_refs=[];represented=TimeGainRepresentedField(native,cache,2)
        for label,fun,refs in [('original',lambda t,z:native.field(z,t),originals),('represented_r2',represented,represented_refs)]:
            if previous_report is not None:
                frozen=np.load(out/f'{args.reuse_reference_run}_traces.npz')
                np.testing.assert_array_equal(frozen['reference_times'],grid)
                values=frozen[label].copy();traces[label]=values
                class GridReference:
                    def __init__(self,values):self.values=values
                    def sol(self,times):
                        idx=np.rint(np.asarray(times)/T*(len(grid)-1)).astype(int)
                        np.testing.assert_allclose(grid[idx],times,atol=1e-17,rtol=0)
                        return self.values[idx].T
                refs.append(GridReference(values))
                report[label+'_reference_refinement_max']=previous_report[label+'_reference_refinement_max']
                report['phases'].extend(p for p in previous_report['phases'] if p['reference']==label)
                continue
            for rtol,atol,step in [(2e-10,2e-12,T/4),(5e-12,5e-14,T/8)]:
                print('REFERENCE',label,rtol,flush=True);before=time.perf_counter()
                sol=solve_ivp(fun,(0,T),z0,method='DOP853',rtol=rtol,atol=atol,max_step=step,dense_output=True)
                if not sol.success:raise RuntimeError(sol.message)
                refs.append(sol);report['phases'].append(dict(reference=label,rtol=rtol,atol=atol,max_step=step,nfev=sol.nfev,seconds=time.perf_counter()-before));save()
            values=refs[-1].sol(grid).T;traces[label]=values
            report[label+'_reference_refinement_max']=float(np.max(np.linalg.norm(refs[0].sol(grid).T-values,axis=1)));save()
            np.savez_compressed(out/f'{args.run_id}_traces.npz',**traces)
        report['represented_original_model_gap_max']=float(np.max(np.linalg.norm(traces['original']-traces['represented_r2'],axis=1)))
        previous={}
        for steps in (2,4,8):
            times=np.linspace(0,T,steps+1)
            for method in ('midpoint_original','moser_midpoint_r2'):
                print('INTEGRATE',method,steps,flush=True)
                if method=='midpoint_original':states,info=midpoint(native,z0,T,steps)
                else:
                    chart=MoserChart(cache,2);states,info=chart_midpoint(native,represented,chart,z0,T,T/steps,diagnose=(steps==2))
                    info.update(auxiliary_calls=chart.calls,auxiliary_nfev=chart.nfev,auxiliary_seconds=chart.seconds)
                eo=float(np.max(np.linalg.norm(states-originals[-1].sol(times).T,axis=1)))
                ea=float(np.max(np.linalg.norm(states-represented_refs[-1].sol(times).T,axis=1)))
                err=eo if method=='midpoint_original' else ea
                row=dict(info)
                row.update(method=method,steps=steps,h=T/steps,error_original_max=eo,error_represented_max=ea,
                    observed_order_to_own_field=None if method not in previous else float(np.log2(previous[method]/err)))
                previous[method]=err;report['rows'].append(row);traces[f'{method}_{steps}']=states
                save();np.savez_compressed(out/f'{args.run_id}_traces.npz',**traces)
        samples=[]
        for t,z in zip(grid[::4],traces['original'][::4]):
            current=native.currents(t,z);grad=torch.func.grad(native.base.hamiltonian_tensor)(torch.as_tensor(z)).detach().numpy()
            gain=native.base.collocated_gain*float(native.gain_factor(t));port=native.base.current_port(z[:native.n])
            expected=-gain*np.linalg.norm(port.T@grad[native.n:])**2
            actual=float(grad@native.field(z,t));sample=native.base.physical_samples(z[:native.n],current)
            samples.append(dict(time=t,current_A=current,maximum_current_A=float(np.max(abs(current))),power_H_tau=actual,
                collocated_power_formula=expected,power_identity_residual=actual-expected,
                maximum_B_T=sample['maximum_B_T'],maximum_G_T_per_m=sample['maximum_G_T_per_m']))
        report['physical_samples']=samples
        ts=np.asarray([s['time'] for s in samples])/native.base.rom.omega0
        report['sampled_current_slew_max_A_per_s']=float(np.max(abs(np.diff(np.asarray([s['current_A'] for s in samples]),axis=0)/np.diff(ts)[:,None])))
        report['constraint_scope']='Sampled smooth feedback only. No online limiter, no continuum field/slew certificate; compare coil configuration limits explicitly.'
        fields=['method','steps','h','error_original_max','error_represented_max','observed_order_to_own_field','seconds','max_residual_inf']
        with (out/f'{args.run_id}.csv').open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows({k:row[k] for k in fields} for row in report['rows'])
        report.update(status='completed',elapsed_seconds=time.perf_counter()-started);save()
    except BaseException as exc:
        report.update(status='failed',exception=repr(exc),traceback=traceback.format_exc(),elapsed_seconds=time.perf_counter()-started);save();raise


if __name__=='__main__':main()
