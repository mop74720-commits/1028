"""Fresh 24D gauge/operator/chart derivatives on frozen stage5 trajectory/cache.
No trajectory integration or training is falsely counted as rerun here.
"""
from pathlib import Path
import sys,json,hashlib,time,platform,argparse,traceback
import numpy as np
import torch
from fusion_theory import ROOT,PhysicalHamiltonianGauge,chart_defect_decomposition,formal_self_adjoint_defect
from transport_native import NativeTransport
from transport_cache import OneFormCache,CachedRepresentedField
from moser_chart import MoserChart


def clean(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)


def native_model(name):
    if name=='synthetic':return NativeTransport()
    from coil_rom import CoilROM
    base=CoilROM();native=NativeTransport(base=base,kind='fullcoil_collocated')
    def force(z):
        G=base.current_port_tensor(z[:base.n]);v=native._gradH(z)[base.n:]
        return -base.collocated_gain*G@(G.T@v)
    def numeric_force(z):
        G=base.current_port_tensor(z[:base.n]);v=torch.func.grad(base.hamiltonian_tensor)(z)[base.n:]
        return -base.collocated_gain*G@(G.T@v)
    native.force_override=force;native.numeric_force_override=numeric_force
    return native


def run(name):
    started=time.perf_counter();directory=ROOT/'stage5/results/transport'/name
    old=json.loads((directory/'inverse_verified.json').read_text())
    paths=list(directory.glob('cache_*inverse_'+old['cache_fingerprint'][:12]+'.npz'))
    if len(paths)!=1:raise ValueError('Expected exactly one verified inverse-AD cache')
    cache=OneFormCache.load(paths[0]);r=cache.maximum_order
    if cache.metadata['fingerprint']!=old['cache_fingerprint']:raise ValueError('Fingerprint mismatch')
    native=native_model(name);represented=CachedRepresentedField(native,cache,r)
    gauge=PhysicalHamiltonianGauge(native,cache,r);z=cache.center.copy();t=.00025
    result=dict(model=name,order=r,cache=str(paths[0].relative_to(ROOT)),cache_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
        reused_stage5_result=str((directory/'inverse_verified.json').relative_to(ROOT)),state=z,time=t,
        scope='Fresh gauge, full-field derivatives and chart defect decomposition; frozen stage5 cache and first-step trajectory reused, no new trajectory integration',
        mass_frozen=False,physical_flow_oracle=False)
    print('GAUGE',name,flush=True);start=time.perf_counter();g=gauge.diagnostics(z,t)
    result['gauge_seconds']=time.perf_counter()-start
    fa,stage5diag=represented(t,z,True)
    result['stage5_field_agreement']=float(np.linalg.norm(fa-g['represented_field']))
    result['source_gauge_diagnostics']=stage5diag
    result['wrong_B_H_without_oneform_change_error']=float(np.linalg.norm(g['wrong_unchanged_oneform_field']-fa))
    delta=1e-7;x=torch.as_tensor(z);direction=np.cos(np.arange(native.d));direction/=np.linalg.norm(direction)
    sigma=lambda zz,tt:float(gauge.sigma_tensor(torch.as_tensor(zz),tt).detach())
    result['sigma_t_centered_fd_error']=abs((sigma(z,t+delta)-sigma(z,t-delta))/(2*delta)-(g['source_scalar']-g['gauge_scalar_H']))
    result['sigma_direction_centered_fd_error']=abs((sigma(z+delta*direction,t)-sigma(z-delta*direction,t))/(2*delta)-g['gradient_sigma']@direction)
    result['gauge']=g
    print('OPERATOR',name,flush=True);start=time.perf_counter()
    a=cache.data(z,t,r);A=represented.jacobian(t,z)
    Db=np.einsum('ijk,j->ik',a['DK'],fa)+a['K']@A
    velocity=.003*np.sin(np.arange(native.d)+.3)
    defect=formal_self_adjoint_defect(a['Kt'],a['DK'],Db,velocity)
    f,F,_=native.field_and_jacobian(z)
    Db_original=np.einsum('ijk,j->ik',a['DK'],f)+a['K']@F
    result['formal_operator']=dict(represented_off_shell_defect_2=float(np.linalg.norm(defect,2)),
        original_field_with_truncated_form_off_shell_defect_2=float(np.linalg.norm(formal_self_adjoint_defect(a['Kt'],a['DK'],Db_original,velocity),2)),
        physical_Df_antisymmetry_2=float(np.linalg.norm(F-F.T,2)),velocity=velocity,seconds=time.perf_counter()-start)
    print('CHART',name,flush=True);start=time.perf_counter()
    trace=np.load(directory/'inverse_verified_traces.npz');states=trace[f'chart_r{r}_steps4'];zm,zp=states[:2];h=.000125
    chart=MoserChart(cache,r)
    ym,Tm,_,_=chart.map(zm,0.,inverse=True)
    yp,Tp,_,_=chart.map(zp,h,inverse=True)
    _,Rp,_,_=chart.map(yp,h)
    Ag,_=chart.transformed_jacobian(h/2,(ym+yp)/2,represented)
    internal=np.linalg.solve(np.eye(native.d)-h*Ag/2,np.eye(native.d)+h*Ag/2)
    D=Rp@internal@Tm
    decomp=chart_defect_decomposition(cache.K0,cache.data(zm,0.,r)['K'],cache.data(zp,h,r)['K'],Tm,Tp,internal,D)
    result['chart']=dict(time_start=0.,h=h,trajectory_key=f'chart_r{r}_steps4',
        trajectory_sha256=hashlib.sha256((directory/'inverse_verified_traces.npz').read_bytes()).hexdigest(),
        matrices=decomp,norms={k:float(np.linalg.norm(v,2)) for k,v in decomp.items() if isinstance(v,np.ndarray)},
        implicit_midpoint_residual_inf=float(np.linalg.norm(yp-ym-h*chart.transformed_field(h/2,(ym+yp)/2,represented),np.inf)),
        implicit_matrix_condition=float(np.linalg.cond(np.eye(native.d)-h*Ag/2)),seconds=time.perf_counter()-start,
        tolerances=dict(rtol=chart.rtol,atol=chart.atol,max_step=chart.max_step))
    result['checks']=dict(gauge_rhs=g['rhs_gauge_defect']<2e-12,gauge_form=g['raw_gauge_hessian_antisymmetry']<2e-12,
        stage5_field_agreement=result['stage5_field_agreement']<2e-12,
        gauge_time_fd=result['sigma_t_centered_fd_error']<2e-9,gauge_space_fd=result['sigma_direction_centered_fd_error']<2e-9,
        variational_operator=result['formal_operator']['represented_off_shell_defect_2']<2e-8,
        complete_chart_decomposition=decomp['decomposition_residual']<3e-14,
        nonzero_original_representation_error=g['original_field_representation_residual']>1e-14,
        nonzero_power=g['original_H_rate']<0,
        incorrect_gauge_changes_field=result['wrong_B_H_without_oneform_change_error']>1e-12)
    result['seconds']=time.perf_counter()-started
    print('DONE',name,json.dumps(result['checks'],default=clean),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='S6_THEORY01');args=parser.parse_args()
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
    out=ROOT/'stage6/fusion_reconciliation/results/theory'/args.run_id;out.mkdir(parents=True,exist_ok=True)
    path=out/'results.json'
    if path.exists():raise FileExistsError('Use a fresh run-id to preserve prior evidence')
    report=dict(status='running',command=' '.join(sys.argv),python=sys.version,platform=platform.platform(),versions=dict(numpy=np.__version__,torch=torch.__version__),rows=[])
    report['sources']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('fusion_theory.py'),ROOT/'stage5/program/transport_native.py',ROOT/'stage5/program/transport_cache.py',ROOT/'stage5/program/moser_chart.py']}
    def save():path.write_text(json.dumps(report,indent=2,default=clean)+'\n')
    save()
    try:
        for name in ['synthetic','fullcoil_collocated']:
            report['rows'].append(run(name));save()
        report['status']='passed' if all(all(x['checks'].values()) for x in report['rows']) else 'failed'
    except Exception:
        report['status']='failed';report['exception']=traceback.format_exc();save();raise
    save()
    if report['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
