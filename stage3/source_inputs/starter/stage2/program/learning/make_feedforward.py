"""Full 12-DOF model compensation mapped to the shared physical magnetic port.

This is a trajectory feedforward experiment, not invariant-torus tracking or a
proof of learned-model stability. Known geometric M(q) defines reference momenta.
All 12 equations enter the least-squares actuation, whose residual is reported.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import torch
from rod_rom import RodROM
from run_learning import ComplexResidual, polynomial_design, network_prediction


def field_potential_features(model,q):
    _,_,_,R,c=model.mechanics(q,return_geometry=True)
    mu=model.segment_moment[None,:,None]*R[:,:,:,2]
    d=c-model.field_origin
    x,y,z=d.unbind(-1);a,b,c=mu.unbind(-1)
    return torch.stack([a.sum(1),b.sum(1),c.sum(1),(a*x-c*z).sum(1),
                         (b*y-c*z).sum(1),(a*y+b*x).sum(1),
                         (a*z+c*x).sum(1),(b*z+c*y).sum(1)],-1)


def reference(t,cfg):
    c=cfg['controller'];T=c['target_ramp_s'];w=2*np.pi*c['target_frequency_Hz']
    s=np.clip(t/T,0,1);ramp=s*s*(3-2*s)
    x,y=c['target_base_xy_m'];ax,ay=c['target_amplitude_xy_m']
    return np.stack([ramp*(x+ax*np.sin(w*t)),ramp*(y+ay*np.sin(w*t+np.pi/3)),np.full(len(t),cfg['rod']['length_m'])],1)


def main():
    torch.set_num_threads(1)
    root=Path(__file__).resolve().parents[2]
    out=root/'results'/'learning'/'feedforward';out.mkdir(parents=True,exist_ok=True)
    model=RodROM();cfg=model.config;n=model.n
    t=np.linspace(0,2,1001);target=reference(t,cfg)
    zero=torch.zeros(n,requires_grad=True)
    tipjac=torch.autograd.functional.jacobian(lambda q:model.mechanics(q[None,:],return_geometry=True)[2][0,-1,:2],zero).detach().numpy()
    a=np.linalg.solve(model.K0,tipjac.T)
    lift=a@np.linalg.inv(tipjac@a)
    q=target[:,:2]@lift.T
    # Small nonlinear inverse-kinematics correction in the full curvature family.
    with torch.no_grad():
        for _ in range(4):
            _,_,rr,_,_=model.mechanics(torch.tensor(q),return_geometry=True)
            q+=(target[:,:2]-rr[:,-1,:2].numpy())@lift.T
        mass,_,rr,_,_=model.mechanics(torch.tensor(q),return_geometry=True)
    qdot=np.gradient(q,t,axis=0,edge_order=2)
    Q=np.linalg.solve(model.Sq.numpy(),q.T).T
    praw=np.einsum('bij,bj->bi',mass.numpy(),qdot)
    P=(model.omega0/model.E0)*(praw@model.Sq.numpy())
    Pprime=np.gradient(P,t,axis=0,edge_order=2)/model.omega0
    z=np.c_[Q,P]
    hz,gz=model.gradient(torch.tensor(z));true_g=gz.numpy()
    qvar=torch.tensor(q,requires_grad=True)
    phi=field_potential_features(model,qvar)
    ports=[]
    for j in range(8):
        grad=torch.autograd.grad(phi[:,j].sum(),qvar,retain_graph=True)[0]
        ports.append((grad@model.Sq/model.E0).detach().numpy())
    port=np.stack(ports,-1)
    summary=json.loads((out.parent/'learning_summary.json').read_text())
    # Select by validation only, never by the unseen test or physical tracking error.
    best_seed=None;best_loss=float('inf')
    for entry in summary['complex_network']:
        train=json.loads((out.parent/f"training_seed{entry['seed']}.json").read_text())
        loss=min(h['validation']['residual_gradient_relative_l2'] for h in train['history'])
        if loss<best_loss:best_loss=loss;best_seed=entry['seed']
    checkpoint=torch.load(out.parent/f'complex_seed{best_seed}.pt',weights_only=False)
    net=ComplexResidual(n,checkpoint['width'],checkpoint['output_scale']);net.load_state_dict(checkpoint['state_dict'])
    amp=checkpoint['amplitude'];scale=np.sqrt(np.r_[model.nu.numpy(),model.nu.numpy()])/amp
    x=z*scale
    _,g_nn=network_prediction(net,x)
    _,design=polynomial_design(x,n);coef=np.load(out.parent/'analytic_coefficients.npy')
    g_poly=np.einsum('bdf,f->bd',design,coef)
    g0=np.r_[model.nu.numpy(),model.nu.numpy()]*z
    choices=dict(linear=g0,analytic=g0+g_poly*scale,complex=g0+g_nn*scale,truth=true_g)
    # Bz is held at the same 0.5 mT used in learning. All other local source-free
    # field/gradient coordinates can participate. Underdetermined forces remain.
    active=np.array([0,1,3,4,5,6,7]);usc=np.array([.001,.001,.03,.03,.03,.03,.03])
    weights=1/np.sqrt(model.nu.numpy());reg=1e-5
    damping=cfg['rod']['mass_proportional_damping_rate_s_inv']/model.omega0*P
    records={}
    for name,grad in choices.items():
        required=Pprime+grad[:,:n]+damping
        u=np.zeros((len(t),8));u[:,2]=cfg['magnet']['bias_z_T']
        defects=[];clip=0
        for k in range(len(t)):
            A=port[k][:,active]*usc[None,:]*weights[:,None]
            b=required[k]*weights
            sol=np.linalg.solve(A.T@A+reg*np.eye(len(active)),A.T@b)
            u[k,active]=sol*usc
            G=np.array([[u[k,3],u[k,5],u[k,6]],[u[k,5],u[k,4],u[k,7]],[u[k,6],u[k,7],-u[k,3]-u[k,4]]])
            norm=np.linalg.norm(G)
            if norm>cfg['magnet']['gradient_frobenius_bound_T_per_m']:
                u[k,3:]*=cfg['magnet']['gradient_frobenius_bound_T_per_m']/norm;clip+=1
                G*=cfg['magnet']['gradient_frobenius_bound_T_per_m']/norm
            bound=np.linalg.norm(u[k,:3])+cfg['magnet']['workspace_radius_m']*np.linalg.norm(G)
            if bound>cfg['magnet']['B_workspace_bound_T']:
                # Preserve the bias exactly; scale the remaining coordinates by
                # a conservative triangle bound, the same limit used by the rod.
                fraction=(cfg['magnet']['B_workspace_bound_T']-u[k,2])/(bound-u[k,2])
                u[k,active]*=max(0.,fraction);clip+=1
            delta=u[k].copy();delta[2]-=cfg['magnet']['bias_z_T']
            defects.append(np.linalg.norm((port[k]@delta-required[k])*weights))
        metadata=dict(model=name,source='12-DOF Kirchhoff trajectory feedforward',includes_Bz_bias=True,
                      input_order=cfg['controller']['input_order'],bias_Bz_T=cfg['magnet']['bias_z_T'],
                      config_sha256=hashlib.sha256((Path(__file__).resolve().parents[1]/'rod3d'/'config.json').read_bytes()).hexdigest(),
                      target='identical cubic-ramp XY target as full rod; constant z goal L, shortened reference z from inextensibility',
                      known_components='geometric M(q), q-to-position embedding, mass-proportional damping, exact dipole field port',
                      unknown_compensated_component='H_Q evaluated by linear / analytic-residual / trainable-complex / exact-ROM model',
                      excluded='flow and contact feedforward; invariant tori; stability certificate; feedback velocity inversion',
                      training_seed=best_seed if name=='complex' else None,
                      allocation_regularization=reg,allocation_row_weights='1/sqrt(nu)',
                      max_reference_normalized_coordinate=float(np.max(abs(x))),
                      weighted_force_residual_rms=float(np.sqrt(np.mean(np.square(defects)))),
                      relative_force_residual_l2=float(np.linalg.norm(defects)/np.linalg.norm(required*weights)),
                      clipped_count=clip,max_abs_u=np.max(abs(u),axis=0).tolist(),
                      q_active_component_max_abs=np.max(abs(q),axis=0).tolist(),
                      max_reference_tip_xy_error_m=float(np.max(np.linalg.norm(rr[:,-1,:2].numpy()-target[:,:2],axis=1))))
        np.savez_compressed(out/f'{name}.npz',time_s=t,u_ff=u,target=target,Q_ref=Q,P_ref=P,q_raw_ref=q,
                            tip_reference=rr[:,-1,:].numpy(),force_required=required,force_residual_norm=np.array(defects),
                            metadata_json=np.array(json.dumps(metadata)))
        records[name]=metadata
    (out/'summary.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))


if __name__=='__main__':main()
