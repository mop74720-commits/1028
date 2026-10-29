"""Same-field comparison and physical power audit for accepted Moser runs.

Postprocesses retained trajectories; does not rerun/change their integrators.
Power uses the actual total-current plant and mechanical/fixed-bias Hamiltonians.
The represented-field correction is an algorithmic error, not an actuator force.
"""
from pathlib import Path
import argparse,csv,hashlib,json,sys,time
import numpy as np
import torch
from coil_rom import CoilROM
from closed_loop import ClosedLoop
from transport_native import NativeTransport
from transport_cache import OneFormCache,CachedRepresentedField

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='inverse_verified');args=parser.parse_args()
    out=ROOT/'stage5/results/transport';target=out/f'{args.run_id}_comparison.json'
    if target.exists():raise FileExistsError(target)
    started=time.perf_counter();reports={name:json.loads((out/name/f'{args.run_id}.json').read_text()) for name in ['synthetic','fullcoil_collocated']}
    if any(r['status']!='completed' for r in reports.values()):raise ValueError('Main accepted runs must finish first')
    report=dict(status='running',command=sys.argv,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).parent/'coil_rom.py',Path(__file__).parent/'closed_loop.py',Path(__file__).parent/'transport_native.py',Path(__file__).parent/'transport_cache.py']},physical_power_rows=[],same_field_rows=[],interpretation='All fullcoil rows share H_coil, collocated total-current law, z0, tau=0.0005 and the same full-f reference. Synthetic branch is separate. Moser advances a represented approximation fa, whose excess power is not attributed to a magnetic actuator. Sampled amplitude/field/slew checks do not prove continuous constraint satisfaction.')
    save=lambda:target.write_text(json.dumps(report,indent=2)+'\n')
    save()
    base=CoilROM();loop=ClosedLoop(base,'collocated');native=NativeTransport(base=base,kind='fullcoil_collocated')
    def force(z):
        G=base.current_port_tensor(z[:base.n]);return -base.collocated_gain*G@(G.T@native._gradH(z)[base.n:])
    def numeric_force(z):
        G=base.current_port_tensor(z[:base.n]);v=torch.func.grad(base.hamiltonian_tensor)(z)[base.n:];return -base.collocated_gain*G@(G.T@v)
    native.force_override=force;native.numeric_force_override=numeric_force
    source=reports['fullcoil_collocated'];cachepath=next((out/'fullcoil_collocated').glob(f"cache_*_{source['cache_fingerprint'][:12]}.npz"));cache=OneFormCache.load(cachepath)
    traces=np.load(out/'fullcoil_collocated'/f'{args.run_id}_traces.npz');T=source['duration_tau']
    before=json.loads((ROOT/'stage5/results/closed_loop/results.json').read_text())
    assert abs(before['duration_tau']-T)<1e-15
    assert np.max(abs(np.asarray(before['initial_state'])-np.asarray(source['initial_state'])))<1e-15
    report['same_field_verification']=[dict(state_index=k,field_difference_2=float(np.linalg.norm(native.field(z)-loop.field(0.,z)))) for k,z in enumerate([np.asarray(source['initial_state']),traces['original_reference'][-1]])]
    save()
    for row in before['branches']['collocated']['methods']['midpoint']:
        report['same_field_rows'].append(dict(method='ordinary implicit midpoint',order=None,steps=row['steps'],error_to_original=row['maximum_state_error'],observed_order=row['observed_order'],form_used='K0; not preserved by this dissipative field',form_defect=row['maximum_sampled_canonical_defect_2'],fixed_bias_power_balance=row['maximum_fixed_bias_power_balance_residual'],mechanical_power_balance=row['maximum_mechanical_power_balance_residual'],seconds=row['seconds'],newton_residual=row['maximum_increment_residual_inf'],allocation_residual=0.,allocation_interpretation='Prescribed attainable collocated current law; no bounded-force projection in this branch.'))
    original_traces=np.load(ROOT/'stage5/results/closed_loop/trajectories.npz')
    original_states=original_traces['collocated_midpoint_4_states']
    zleft,zright=original_states[:2];hcoarse=T/4
    A=loop.jacobian((zleft+zright)/2);eye=np.eye(len(zleft))
    tangent=np.linalg.solve(eye-hcoarse*A/2,eye+hcoarse*A/2)
    report['same_cached_form_first_step']=[]
    for order in source['orders']:
        left=cache.data(zleft,0.,order)['K'];right=cache.data(zright,hcoarse,order)['K']
        original_defect=float(np.linalg.norm(tangent.T@right@tangent-left,2))
        chart_row=next(r for r in source['rows'] if r['order']==order and r['steps']==4)
        chart_defect=chart_row['records'][0]['K_step_defect_2']
        report['same_cached_form_first_step'].append(dict(order=order,h=hcoarse,ordinary_original_field_midpoint_Ku_defect=original_defect,moser_represented_field_midpoint_Ku_defect=chart_defect,interpretation='Same cached Ku, same initial state. Ordinary midpoint advances original f; graph advances fa. The difference is not proof that fa equals f.'))
    save()
    arrays={}
    for row in source['rows']:
        order=row['order'];count=row['steps'];h=T/count;states=traces[f'chart_r{order}_steps{count}'];represented=CachedRepresentedField(native,cache,order)
        endpoint=[loop.energy_and_power(z) for z in states]
        middles=[]
        for k,(za,zb) in enumerate(zip(states[:-1],states[1:])):
            z=(za+zb)/2;t=(k+.5)*h;x=torch.as_tensor(z)
            powers=loop.energy_and_power(z);fa,diag=represented.evaluate(t,z,True);f=loop.field(t,z);delta=fa-f
            grad_fixed=torch.func.grad(loop.fixed.hamiltonian_tensor)(x).detach().numpy()
            grad_mech=torch.func.grad(lambda xx:base.hamiltonian_tensor(xx,currents=torch.zeros(base.current_channels)))(x).detach().numpy()
            port=base.current_port(z[:base.n]);current=np.asarray(powers['current'])
            desired=-base.collocated_gain*port@(port.T@grad_fixed[base.n:]);realized=port@(current-base.bias_currents)
            allocation=float(np.linalg.norm(realized-desired))
            middles.append(dict(time=t,**powers,original_field_representation_error=float(np.linalg.norm(delta)),representation_residual=diag['representation_residual_2'],fixed_bias_representation_power=float(grad_fixed@delta),mechanical_representation_power=float(grad_mech@delta),allocation_residual_2=allocation))
        fixed=np.array([x['fixed_bias_energy'] for x in endpoint]);mech=np.array([x['mechanical_energy'] for x in endpoint])
        def residual(H,key,extra=None):
            powers=np.array([x[key]+(x[extra] if extra else 0.) for x in middles]);return H-H[0]-np.r_[0.,np.cumsum(h*powers)]
        fixed_res=residual(fixed,'fixed_bias_power');mech_res=residual(mech,'mechanical_power')
        corrected_fixed=residual(fixed,'fixed_bias_power','fixed_bias_representation_power');corrected_mech=residual(mech,'mechanical_power','mechanical_representation_power')
        current=np.array([x['current'] for x in endpoint]);physical=[base.physical_samples(z[:base.n],ii) for z,ii in zip(states,current)]
        tag=f'r{order}_steps{count}'
        for key,value in dict(currents_A=current,fixed_bias_H=fixed,mechanical_H=mech,fixed_balance=fixed_res,mechanical_balance=mech,fixed_balance_after_representation_work=corrected_fixed,mechanical_balance_after_representation_work=corrected_mech).items():arrays[f'{tag}_{key}']=value
        detail=dict(order=order,steps=count,h=h,maximum_fixed_bias_balance=float(np.max(abs(fixed_res))),maximum_mechanical_balance=float(np.max(abs(mech_res))),maximum_fixed_balance_after_representation_work=float(np.max(abs(corrected_fixed))),maximum_mechanical_balance_after_representation_work=float(np.max(abs(corrected_mech))),maximum_original_continuous_power_identity_residual=max(abs(x[k]) for x in endpoint+middles for k in ['fixed_bias_power_identity_residual','mechanical_power_identity_residual']),maximum_representation_power= max(abs(x['fixed_bias_representation_power']) for x in middles),maximum_current_A=float(np.max(abs(current))),maximum_endpoint_difference_slew_A_per_s=float(np.max(abs(np.diff(current,axis=0)))/(h/base.rom.omega0)),maximum_sampled_B_T=max(x['maximum_B_T'] for x in physical),maximum_sampled_G_T_per_m=max(x['maximum_G_T_per_m'] for x in physical),allocation_residual=max(x['allocation_residual_2'] for x in middles),power_quadrature='Endpoint physical state averages, midpoint time. These are not the exact Moser-chart internal midpoint states; residual includes quadrature, time discretization, and representation effects.',midpoint_records=middles)
        report['physical_power_rows'].append(detail)
        defect=next((r['K_step_defect_2'] for r in row['records'] if 'K_step_defect_2' in r),None)
        report['same_field_rows'].append(dict(method='Moser implicit midpoint',order=order,steps=count,error_to_original=row['error_to_original_max'],error_to_represented=row['error_to_represented_max'],observed_order_to_represented=row['observed_order_to_represented'],form_used=f'Cached time-dependent K_u order {order}',form_defect=defect,form_defect_scope='First step of coarsest grid only; null means not separately sampled, not zero.',fixed_bias_power_balance=detail['maximum_fixed_bias_balance'],mechanical_power_balance=detail['maximum_mechanical_balance'],seconds=row['seconds'],newton_residual=row['max_residual_inf'],allocation_residual=detail['allocation_residual']))
        save();np.savez_compressed(out/f'{args.run_id}_power.npz',**arrays)
    flat=report['same_field_rows'];keys=list(dict.fromkeys(k for row in flat for k in row))
    with (out/f'{args.run_id}_same_field.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(flat)
    # Standalone scientific plots; raw JSON/CSV/NPZ remain the evidence.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True,layout='constrained')
    for axis,(name,data) in zip(axes,reports.items()):
        for r in data['orders']:
            rows=[x for x in data['rows'] if x['order']==r]
            line,=axis.loglog([x['steps'] for x in rows],[x['error_to_original_max'] for x in rows],'-o',label=f'r{r}: original field')
            axis.loglog([x['steps'] for x in rows],[x['error_to_represented_max'] for x in rows],'--x',color=line.get_color(),label=f'r{r}: represented field')
        axis.set_title('Synthetic smooth load' if name=='synthetic' else 'Full-coil collocated control')
        axis.set_xlabel('Time steps in fixed window')
        axis.set_xticks([4,8,16],labels=['4','8','16'])
        axis.grid(True,which='both',alpha=.25);axis.legend(fontsize=8)
    axes[0].set_ylabel('Maximum canonical state error (2-norm)')
    fig.suptitle('24D geometric ROM: Moser implicit midpoint')
    fig.savefig(out/f'{args.run_id}_convergence.svg')
    fig.savefig(out/f'{args.run_id}_convergence.png',dpi=180)
    plt.close(fig)
    report.update(status='completed',seconds=time.perf_counter()-started);save()

if __name__=='__main__':main()
