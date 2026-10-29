"""Recompute comparison tables and scientific plots from saved raw trajectories."""
from pathlib import Path
import argparse
import csv
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator,FixedLocator,FuncFormatter
from scipy.spatial.transform import Rotation,Slerp

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT.parents[1]/'results'/'rod3d'


def load_case(root,name):
    path=root/name
    summary=json.loads((path/'summary.json').read_text())
    state=dict(np.load(path/'trajectory.npz'))
    diag=np.genfromtxt(path/'diagnostics.csv',delimiter=',',names=True)
    return summary,state,diag


def trajectory_difference(root,a,b):
    _,x,_=load_case(root,a);_,y,_=load_case(root,b)
    if not np.allclose(x['time_s'],y['time_s'],atol=1e-12,rtol=0):
        raise ValueError('comparison requires matching saved times')
    grid=np.linspace(0,x['reference_s_m'][-1],257)
    def interp(z):
        return np.stack([np.column_stack([np.interp(grid,z['reference_s_m'],r[:,j]) for j in range(3)]) for r in z['r']])
    difference=interp(x)-interp(y)
    spatial=np.trapezoid(np.sum(difference*difference,axis=2),grid,axis=1)/grid[-1]
    tip=x['r'][:,-1]-y['r'][:,-1]
    xc=.5*(x['reference_s_m'][:-1]+x['reference_s_m'][1:])
    yc=.5*(y['reference_s_m'][:-1]+y['reference_s_m'][1:])
    angle=[]
    for i in range(0,len(x['time_s']),10):
        fine=Slerp(yc,Rotation.from_matrix(y['directors'][i]))(np.clip(xc,yc[0],yc[-1])).as_matrix()
        relative=np.einsum('eij,ekj->eik',x['directors'][i],fine)
        angle.extend(Rotation.from_matrix(relative).magnitude().tolist())
    return dict(coarser=a,finer=b,centerline_space_time_rms_difference_m=float(np.sqrt(np.mean(spatial))),
                max_centerline_difference_m=float(np.linalg.norm(difference,axis=2).max()),
                tip_time_rms_difference_m=float(np.sqrt(np.mean(np.sum(tip*tip,axis=1)))),
                final_tip_difference_m=float(np.linalg.norm(tip[-1])),
                director_geodesic_rms_rad=float(np.sqrt(np.mean(np.square(angle)))),
                scope='successive-mesh/time differences, not error against an exact continuum solution')


def group_convergence(root,names,label):
    if not all((root/n/'summary.json').exists() for n in names):return None
    pairs=[trajectory_difference(root,names[i],names[i+1]) for i in range(len(names)-1)]
    e=[p['centerline_space_time_rms_difference_m'] for p in pairs]
    return dict(type=label,cases=names,pairs=pairs,
                observed_successive_difference_order=float(np.log2(e[0]/e[1])) if len(e)==2 and min(e)>0 else None,
                qualification='empirical refinement evidence on this fixed finite-time benchmark; no general PDE convergence theorem')


def energy_probe(root,names):
    values=[]
    for name in names:
        if not (root/name/'summary.json').exists():continue
        s,_,d=load_case(root,name)
        initial=d['mechanical_energy_J'][0]
        values.append(dict(case=name,dt_s=s['dt_s'],initial_energy_J=float(initial),
                           max_relative_energy_defect=float(np.max(np.abs(d['mechanical_energy_J']-initial))/initial),
                           max_SO3_defect=float(d['so3_orthogonality_error'].max()),
                           max_twist_curvature_per_m=float(d['max_twist_curvature_per_m'].max())))
    return dict(values=values,orders=[float(np.log2(values[i]['max_relative_energy_defect']/values[i+1]['max_relative_energy_defect'])) for i in range(len(values)-1)],
                scope='unforced pure-torsion conservative diagnostic; not a symplecticity proof for the driven dissipative system')


def coil_comparison(root):
    name='coil_allocated_n32_h10us'
    if not (root/name/'summary.json').exists():return None
    sys.path.insert(0,str(ROOT.parent))
    from coil_field import basis,unpack
    s,x,d=load_case(root,name)
    cfg=json.loads((ROOT.parents[1]/'results'/'coil'/'coil_config.json').read_text())
    active=np.where(np.linalg.norm(x['magnetic_dipole_body_A_m2'],axis=1)>0)[0]
    records=[]
    field_error,field_true,force_error,force_true,torque_error,torque_true=[],[],[],[],[],[]
    eps=1e-6
    for i in range(0,len(x['time_s']),5):
        alpha=x['magnetic_barycentric_coordinate'][active,None]
        points=(1-alpha)*x['r'][i,active]+alpha*x['r'][i,active+1]
        currents=x['currents_A'][i]
        true=basis(points,cfg)@currents
        true_grad=np.stack([(basis(points+eps*np.eye(3)[j],cfg)-basis(points-eps*np.eye(3)[j],cfg))@currents/(2*eps) for j in range(3)],axis=2)
        b,g=unpack(x['u'][i])
        affine=b+(points-np.array(cfg['origin_m']))@g.T
        mu=np.einsum('eji,ej->ei',x['directors'][i,active],x['magnetic_dipole_body_A_m2'][active])
        ft=np.einsum('eij,ei->ej',true_grad,mu)
        fa=mu@g
        tt=np.cross(mu,true);ta=np.cross(mu,affine)
        for target,value in [(field_error,true-affine),(field_true,true),(force_error,ft-fa),(force_true,ft),(torque_error,tt-ta),(torque_true,tt)]:target.append(value)
        for j,e in enumerate(active):
            records.append([x['time_s'][i],int(e),*points[j],np.linalg.norm(true[j]-affine[j]),np.linalg.norm(ft[j]-fa[j]),np.linalg.norm(tt[j]-ta[j])])
    a=np.asarray(records)
    np.savetxt(root/'coil_actual_segment_comparison.csv',a,delimiter=',',header='time_s,element,x_m,y_m,z_m,B_error_T,force_error_N,torque_error_Nm',comments='')
    result={}
    for prefix,error,true in [('field',field_error,field_true),('force',force_error,force_true),('torque',torque_error,torque_true)]:
        error,true=np.asarray(error),np.asarray(true)
        result[prefix+'_relative_l2_error']=float(np.linalg.norm(error)/max(np.linalg.norm(true),1e-30))
        result[prefix+'_max_absolute_vector_error']=float(np.linalg.norm(error,axis=-1).max())
        result[prefix+'_true_vector_rms']=float(np.sqrt(np.mean(np.sum(true*true,axis=-1))))
        result[prefix+'_error_vector_rms']=float(np.sqrt(np.mean(np.sum(error*error,axis=-1))))
    hist=np.genfromtxt(root/name/'coil_commands.csv',delimiter=',',skip_header=1)
    scales=np.array([.001]*3+[.03]*5)
    result.update(sampled_times=len(field_error),sampled_magnetic_elements=len(active),
                  current_max_A=s['coil_max_current_A'],slew_max_A_per_s=s['coil_max_slew_A_per_s'],
                  allocation_scaled_rms=float(np.sqrt(np.mean(((hist[:,1:9]-hist[:,9:17])/scales)**2))),
                  current_bound_active_fraction=float(np.mean(np.any(np.abs(hist[:,17:])>=2.-1e-8,axis=1))),
                  discrete_slew_bound_active_fraction=float(np.mean(np.any(np.abs(np.diff(hist[:,17:],axis=0)/np.diff(hist[:,0])[:,None])>=20.-1e-8,axis=1))),
                  scope='postprocessing full Biot-Savart field/gradient at sampled actual magnetic subelement centroids; dynamics used the local affine map, not the full Biot-Savart field')
    (root/'coil_actual_segment_comparison.json').write_text(json.dumps(result,indent=2))
    return result


def save(fig,root,name):
    for ext in ['png','svg']:fig.savefig(root/f'{name}.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


def plots(root,results):
    figures=root/'figures';figures.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.constrained_layout.use':True,'svg.fonttype':'none'})
    main=[('uncontrolled_n32_h10us','No magnetic control'),('feedforward_n32_h10us','Static compliance feedforward'),('position_feedback_n32_h10us','Feedforward + position feedback'),('coil_allocated_n32_h10us','Affine coil model + current limits')]
    if all((root/n/'summary.json').exists() for n,_ in main):
        fig,axes=plt.subplots(2,2,figsize=(11,7))
        for name,label in main:
            s,x,d=load_case(root,name);t=x['time_s']
            axes[0,0].plot(t,d['tip_error_m']*1e3,label=label)
            axes[0,1].plot(x['r'][:,-1,0]*1e3,x['r'][:,-1,1]*1e3,label=label)
            axes[1,0].plot(t,np.linalg.norm(x['u'][:,:3],axis=1)*1e3,label=label)
            external=sum(d['work_'+key+'_J'] for key in ['magnetic','flow','contact_dissipative','residual_g','structural_damping'])
            residual=d['mechanical_energy_J']-d['mechanical_energy_J'][0]-external
            axes[1,1].plot(t,residual*1e12,label=label)
        axes[0,1].plot(x['target'][:,0]*1e3,x['target'][:,1]*1e3,'k--',label='Target')
        axes[0,0].set(xlabel='Time [s]',ylabel='3D tip error [mm]',title='32 elements, time step 10 microseconds')
        axes[0,1].set(xlabel='Tip x [mm]',ylabel='Tip y [mm]',title='Three-dimensional rod, transverse projection')
        axes[1,0].set(xlabel='Time [s]',ylabel='Uniform field norm [mT]')
        axes[1,1].set(xlabel='Time [s]',ylabel='Energy - external work [pJ]')
        axes[0,0].legend(fontsize=8);axes[0,1].legend(fontsize=8)
        save(fig,figures,'control_comparison')

    name='position_feedback_n64_h5us'
    if (root/name/'summary.json').exists():
        _,x,_=load_case(root,name)
        fig=plt.figure(figsize=(7,8));ax=fig.add_subplot(projection='3d')
        z=np.linspace(0,.102,65);theta=np.linspace(0,2*np.pi,25)
        center=np.column_stack([.0009*np.sin(2*np.pi*z/.1),.0006*np.sin(np.pi*z/.1),z])
        tangent=np.column_stack([.0009*2*np.pi/.1*np.cos(2*np.pi*z/.1),.0006*np.pi/.1*np.cos(np.pi*z/.1),np.ones_like(z)])
        tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        n1=np.cross(tangent,np.array([0.,1.,0.]));n1/=np.linalg.norm(n1,axis=1)[:,None]
        n2=np.cross(tangent,n1)
        tube=center[:,None,:]+.003*(np.cos(theta)[None,:,None]*n1[:,None,:]+np.sin(theta)[None,:,None]*n2[:,None,:])
        ax.plot_wireframe(tube[:,:,0]*1e3,tube[:,:,1]*1e3,tube[:,:,2]*1e3,color='#b5c9d7',linewidth=.5,alpha=.35,rstride=5,cstride=3)
        for t in [0,.5,1,1.5,2]:
            idx=np.argmin(abs(x['time_s']-t));r=x['r'][idx]*1e3
            ax.plot(r[:,0],r[:,1],r[:,2],label=f't = {t:g} s',lw=2)
        ax.set(xlabel='x [mm]',ylabel='y [mm]',zlabel='z [mm]',title='Full 3D rod inside curved lumen\nAxes use independent visual scales')
        ax.set_box_aspect((1,1,3));ax.view_init(elev=21,azim=-55);ax.legend(fontsize=8)
        save(fig,figures,'geometry_3d')

    groups=[results.get('space'),results.get('time'),results.get('contact_space')]
    if all(g is not None for g in groups):
        fig,axes=plt.subplots(1,3,figsize=(12,3.8))
        for ax,g,title in zip(axes,groups,['Smooth run: spatial refinement','Smooth run: time refinement','Contact stress: spatial refinement']):
            xx=[16,32] if g['type']!='time' else [10,5]
            scale=1e9 if g['type']=='time' else 1e6
            unit='nanometers' if g['type']=='time' else 'micrometers'
            yy=[p['centerline_space_time_rms_difference_m']*scale for p in g['pairs']]
            ax.loglog(xx,yy,'o-',lw=2)
            ax.set(title=title,xlabel='Coarser element count' if g['type']!='time' else 'Coarser time step [microseconds]',ylabel=f'Successive difference [{unit}]')
            ax.xaxis.set_major_locator(FixedLocator(xx));ax.xaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:g}'))
            ax.xaxis.set_minor_locator(NullLocator());ax.yaxis.set_major_locator(FixedLocator(yy))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:.4g}'));ax.yaxis.set_minor_locator(NullLocator())
            ax.text(.05,.08,f"Observed p = {g['observed_successive_difference_order']:.3f}",transform=ax.transAxes)
            ax.grid(alpha=.25,which='both')
        save(fig,figures,'refinement')

    contacts=['contact_stress_n16_h5us','contact_stress_n32_h5us','contact_stress_n64_h5us']
    if all((root/n/'summary.json').exists() for n in contacts):
        fig,axes=plt.subplots(2,2,figsize=(10,7))
        for name in contacts:
            s,x,d=load_case(root,name);t=x['time_s'];label=f"{s['n_elements']} elements"
            axes[0,0].plot(t,d['max_quadrature_penetration_m']*1e6,label=label)
            axes[0,1].plot(t,d['contact_normal_total_N']*1e6,label=label)
            axes[1,0].plot(t,d['power_contact_dissipative_W']*1e9,label=label)
            axes[1,1].plot(t,d['power_flow_W']*1e9,label=label)
        axes[0,0].set(ylabel='Quadrature penetration [micrometers]',title='Deliberately infeasible target stress test')
        axes[0,1].set(ylabel='Total normal contact force [micronewtons]')
        axes[1,0].set(ylabel='Contact dissipative power [nW]',xlabel='Time [s]')
        axes[1,1].set(ylabel='Flow power on rod [nW]',xlabel='Time [s]')
        axes[0,0].legend();save(fig,figures,'contact_and_flow')

    penalty_cases=['contact_stress_n64_h5us','contact_penalty_20000_n64_h5us','contact_penalty_200000_n64_h5us']
    if all((root/n/'summary.json').exists() for n in penalty_cases):
        fig,axes=plt.subplots(1,2,figsize=(10,4))
        for name,stiffness in zip(penalty_cases,[2000,20000,200000]):
            s,x,d=load_case(root,name)
            label=f'$k_H={stiffness:g}$ N/m$^{{5/2}}$'
            axes[0].plot(x['time_s'],d['max_quadrature_penetration_m']*1e6,label=label)
            axes[1].plot(x['time_s'],d['contact_normal_total_N']*1e6,label=label)
        axes[0].set(xlabel='Time [s]',ylabel='Quadrature penetration [micrometers]',title='64 elements, 5 microseconds: penalty sensitivity')
        axes[1].set(xlabel='Time [s]',ylabel='Total normal contact force [micronewtons]')
        axes[0].legend(fontsize=8);save(fig,figures,'contact_penalty_sensitivity')

    names=['conservative_twist_n32_h'+s for s in ['10us','5us','2p5us']]
    if all((root/n/'summary.json').exists() for n in names):
        fig,axes=plt.subplots(1,2,figsize=(10,3.8))
        for name in names:
            s,x,d=load_case(root,name);t=x['time_s'];e=d['mechanical_energy_J'];e0=e[0]
            axes[0].plot(t,(e-e0)/e0,label=f"h = {s['dt_s']*1e6:g} microseconds")
        vals=results['conservative_torsion']['values']
        axes[1].loglog([x['dt_s'] for x in vals],[x['max_relative_energy_defect'] for x in vals],'o-')
        axes[0].set(xlabel='Time [s]',ylabel='Relative mechanical energy defect',title='Conservative pure torsion diagnostic')
        axes[1].set(xlabel='Time step [s]',ylabel='Maximum relative energy defect')
        axes[0].legend(fontsize=8);save(fig,figures,'conservative_twist')

    fig,axes=plt.subplots(1,2,figsize=(11,4));found=False
    for n,ax in zip([32,64],axes):
        model_labels={'linear':'Linear ROM','analytic':'Analytic residual dictionary','complex':'Trainable complex network','truth':'Exact low-dimensional ROM'}
        for model in ['linear','analytic','complex','truth']:
            name=f'learned_{model}_n{n}_h'+('10us' if n==32 else '5us')
            if not (root/name/'summary.json').exists():continue
            found=True;s,x,d=load_case(root,name)
            ax.plot(x['time_s'],d['tip_error_m']*1e3,label=model_labels[model])
        baseline='position_feedback_n'+str(n)+'_h'+('10us' if n==32 else '5us')
        if (root/baseline/'summary.json').exists():
            s,x,d=load_case(root,baseline);ax.plot(x['time_s'],d['tip_error_m']*1e3,'k--',label='Static compliance baseline')
        ax.set(xlabel='Time [s]',ylabel='3D tip error [mm]',title=f'{n} elements: shared position feedback');ax.legend(fontsize=8)
    if found:save(fig,figures,'learned_feedforward_transfer')
    else:plt.close(fig)

    failures=root/'velocity_feedback_failure_study.json'
    if failures.exists():
        fig,axes=plt.subplots(1,2,figsize=(10,4))
        for result in json.loads(failures.read_text()):
            name=result['case'];path=root/name/'partial_diagnostics.csv'
            if not path.exists():path=root/name/'diagnostics.csv'
            if not path.exists():continue
            d=np.genfromtxt(path,delimiter=',',names=True)
            usable=np.isfinite(d['mechanical_energy_J'])&(d['max_shear_stretch_strain']<1.)
            axes[0].semilogy(d['time_s'][usable],d['max_shear_stretch_strain'][usable],label=f"h = {result['dt_s']*1e6:g} microseconds")
            axes[1].semilogy(d['time_s'][usable],d['mechanical_energy_J'][usable])
        axes[0].set(xlabel='Time [s]',ylabel='Maximum shear/stretch strain',title='Rejected noncollocated velocity feedback')
        axes[1].set(xlabel='Time [s]',ylabel='Mechanical energy [J]',title='Finite samples with strain below 1 only')
        axes[0].legend(fontsize=8);save(fig,figures,'failed_velocity_feedback')

    coils=[('coil_allocated_n32_h10us','Affine coil model'),('full_biot_savart_coils_n32_h10us','Full field: origin allocation'),
           ('full_biot_savart_tube_constrained_n32_h10us','Full field: sampled tube constraints'),
           ('full_biot_savart_tube_constrained_ramped_n32_h10us','Full field: constraints + current ramps')]
    if all((root/n/'summary.json').exists() for n,_ in coils):
        fig,axes=plt.subplots(2,2,figsize=(12,7))
        for name,label in coils:
            s,x,d=load_case(root,name);t=x['time_s']
            axes[0,0].plot(t,d['tip_error_m']*1e3,label=label)
            axes[0,1].plot(t,d['B_at_nodes_max_T']*1e3,label=label)
            gradient=d['true_G_at_nodes_frobenius_max_T_per_m'] if 'true_G_at_nodes_frobenius_max_T_per_m' in d.dtype.names else d['G_frobenius_T_per_m']
            axes[1,0].semilogy(t,np.maximum(gradient,1e-6),label=label)
            axes[1,1].plot(t,np.max(abs(x['currents_A']),axis=1),label=label)
        axes[0,0].set(ylabel='3D tip error [mm]',title='Physical coil constraints and model mismatch')
        axes[0,1].set(ylabel='Maximum field at rod nodes [mT]');axes[0,1].axhline(5,color='k',ls=':',label='Specified bound')
        axes[1,0].set(xlabel='Time [s]',ylabel='Maximum gradient norm [T/m]');axes[1,0].axhline(.03,color='k',ls=':')
        axes[1,1].set(xlabel='Time [s]',ylabel='Maximum absolute current [A]');axes[1,1].axhline(2,color='k',ls=':')
        axes[0,0].legend(fontsize=8);save(fig,figures,'full_coil_constraints')

    name='womersley_position_feedback_n32_h10us'
    if (root/name/'summary.json').exists():
        _,w,wd=load_case(root,name);_,p,pd=load_case(root,'position_feedback_n32_h10us')
        table=np.loadtxt(root/'womersley_lookup.csv',delimiter=',',skiprows=1);r=table[:,0]
        fig,axes=plt.subplots(2,2,figsize=(10,7))
        for phase,label in zip([0,np.pi/2,np.pi,3*np.pi/2],['0','pi/2','pi','3pi/2']):
            u=.04*(1-r*r)+.009*(table[:,1]*np.sin(phase)+table[:,2]*np.cos(phase))
            line=axes[0,0].plot(r*3,u*1e3,label='Phase '+label)[0]
            axes[0,0].plot(r*3,.04*(1+.45*np.sin(phase))*(1-r*r)*1e3,'--',color=line.get_color(),alpha=.6)
        axes[0,0].set(xlabel='Radius [mm]',ylabel='Axial velocity [mm/s]',title='Solid: Womersley; dashed: instantaneous parabola');axes[0,0].legend(fontsize=8)
        t=w['time_s'];axes[0,1].plot(t,pd['tip_error_m']*1e3,label='Instantaneous parabola');axes[0,1].plot(t,wd['tip_error_m']*1e3,label='Local Womersley')
        axes[0,1].set(xlabel='Time [s]',ylabel='3D tip error [mm]');axes[0,1].legend(fontsize=8)
        for j,label in enumerate(['x','y','z']):axes[1,0].plot(t,(w['r'][:,-1,j]-p['r'][:,-1,j])*1e6,label=label)
        axes[1,0].set(xlabel='Time [s]',ylabel='Tip position change [micrometers]');axes[1,0].legend()
        axes[1,1].plot(t,pd['power_flow_W']*1e9,label='Instantaneous parabola');axes[1,1].plot(t,wd['power_flow_W']*1e9,label='Local Womersley')
        axes[1,1].set(xlabel='Time [s]',ylabel='Flow mechanical power [nW]');axes[1,1].legend(fontsize=8)
        save(fig,figures,'womersley_sensitivity')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=DEFAULT);args=parser.parse_args();root=args.output
    space=['position_feedback_n16_h5us','position_feedback_n32_h5us','position_feedback_n64_h5us']
    time=['position_feedback_n32_h10us','position_feedback_n32_h5us','position_feedback_n32_h2p5us']
    contact=['contact_stress_n16_h5us','contact_stress_n32_h5us','contact_stress_n64_h5us']
    torsion=['conservative_twist_n32_h'+s for s in ['10us','5us','2p5us']]
    results=dict(space=group_convergence(root,space,'space'),time=group_convergence(root,time,'time'),
                 contact_space=group_convergence(root,contact,'contact_space'),conservative_torsion=energy_probe(root,torsion),coil=coil_comparison(root))
    summaries=[json.loads(p.read_text()) for p in sorted(root.glob('*/summary.json')) if not p.parent.name.startswith('smoke') and p.parent.name!='feedback_h10us_before_failure' and not p.parent.name.endswith('_multithread_record')]
    for s in summaries:
        s['interpretation']='finite-time numerical benchmark; no general stability theorem'
        if s['case'].startswith('failed_velocity'):s['interpretation']='rejected despite completion: large strain and unresolved energy-work balance'
        if s['case'].startswith('conservative'):
            s['interpretation']='unforced torsional energy diagnostic; tracking error is not applicable'
        if s['case'].startswith('full_biot_savart_coils'):s['interpretation']='numerically resolved full-field dynamics; engineered spatial field bounds violated'
        if s['case'].startswith('full_biot_savart_tube'):s['interpretation']='full-field dynamics with validated sampled-tube/actual-node constraints; no continuous spatial bound'
    cols=['case','interpretation','n_elements','dt_s','duration_s','tip_rmse_after_ramp_m','max_contact_penetration_m','max_total_contact_normal_N','max_abs_shear_stretch_strain','max_so3_orthogonality_error','energy_work_residual_scaled','max_B_at_rod_nodes_T','max_G_frobenius_T_per_m','input_clipped_or_allocated_fraction','wall_time_s']
    with (root/'comparison.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=cols,extrasaction='ignore');writer.writeheader();writer.writerows(summaries)
    results['summaries']=summaries
    failures=root/'velocity_feedback_failure_study.json'
    if failures.exists():results['rejected_velocity_feedback']=json.loads(failures.read_text())
    for name,key in [('full_biot_savart_tube_constrained_n32_h10us','sampled_coil_constraints'),('full_biot_savart_tube_constrained_ramped_n32_h10us','continuous_slew_coil_constraints')]:
        path=root/name/'workspace_constraint_audit.json'
        if path.exists():results[key]=json.loads(path.read_text())
    if (root/'womersley_position_feedback_n32_h10us'/'summary.json').exists():
        results['flow_closure_difference']=trajectory_difference(root,'position_feedback_n32_h10us','womersley_position_feedback_n32_h10us')
        results['flow_closure_difference']['scope']='difference between prescribed-flow closures at matched mesh, step size and times; not a refinement error estimate'
        results['womersley_profile']=json.loads((root/'womersley_profile_verification.json').read_text())
    (root/'analysis.json').write_text(json.dumps(results,indent=2))
    plots(root,results)
    print(json.dumps({k:v for k,v in results.items() if k!='summaries'},indent=2))


if __name__=='__main__':main()
