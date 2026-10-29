"""Reproducible 12-DOF spatial-rod learning comparison, not a KAM proof."""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import scipy
import torch
from torch import nn
from rod_rom import RodROM, rotation_and_right_jacobian


class ComplexResidual(nn.Module):
    def __init__(self,n,width=48,output_scale=1.):
        super().__init__();self.n=n;self.output_scale=float(output_scale)
        self.l1=nn.Linear(2*n,width,bias=False,dtype=torch.complex128)
        self.l2=nn.Linear(width,width,dtype=torch.complex128)
        self.l3=nn.Linear(width,1,bias=False,dtype=torch.complex128)
        with torch.no_grad():
            for layer in [self.l1,self.l2,self.l3]:
                layer.weight.mul_(.5)
                if layer.bias is not None:layer.bias.mul_(.2)

    @staticmethod
    def activation(z):
        # A real-analytic function of (z, zbar). This is deliberately not
        # holomorphic tanh(z), whose poles caused observed real-data spikes.
        return torch.complex(torch.tanh(z.real),torch.tanh(z.imag))

    def network(self,x):
        xi=torch.complex(x[:,:self.n],x[:,self.n:])/np.sqrt(2)
        both=torch.cat([xi,xi.conj()],dim=1)
        a=self.l1(both)
        coefficients=self.activation(self.l2(self.activation(a)))
        # Cubic zero-bias gate fixes the complete 0th, 1st, and 2nd energy jet.
        # It allows mixed momentum and position terms, unlike a potential-only fit.
        return self.l3(a**3*coefficients).real[:,0]

    def forward(self,x):
        mirrored=torch.cat([x[:,:self.n],-x[:,self.n:]],dim=1)
        return self.output_scale*.5*(self.network(x)+self.network(mirrored))


def polynomial_features(x,n):
    q=x[:,:n];p=x[:,n:]
    return torch.cat([q**3,q**4,q*q*p*p,q*q*torch.roll(q,1,1)**2],dim=1)


def polynomial_design(x,n):
    batch=x.shape[0];a=np.zeros((batch,2*n,4*n));values=np.zeros((batch,4*n))
    q=x[:,:n];p=x[:,n:]
    for j in range(n):
        values[:,j]=q[:,j]**3;a[:,j,j]=3*q[:,j]**2
        values[:,n+j]=q[:,j]**4;a[:,j,n+j]=4*q[:,j]**3
        values[:,2*n+j]=q[:,j]**2*p[:,j]**2
        a[:,j,2*n+j]=2*q[:,j]*p[:,j]**2;a[:,n+j,2*n+j]=2*q[:,j]**2*p[:,j]
        k=(j-1)%n;values[:,3*n+j]=q[:,j]**2*q[:,k]**2
        a[:,j,3*n+j]=2*q[:,j]*q[:,k]**2;a[:,k,3*n+j]=2*q[:,j]**2*q[:,k]
    return values,a


def labels(model,x,amplitude,batch_size=128):
    scale=torch.cat([torch.sqrt(model.nu),torch.sqrt(model.nu)])/amplitude
    hlist=[];glist=[];qlist=[];tips=[]
    for start in range(0,len(x),batch_size):
        xb=torch.tensor(x[start:start+batch_size],requires_grad=True)
        z=xb/scale
        h=model.hamiltonian(z)
        g=torch.autograd.grad(h.sum(),xb)[0]
        h0=.5*amplitude**2*(xb**2).sum(-1)
        g0=amplitude**2*xb
        hlist.append((h-h0).detach().numpy());glist.append((g-g0).detach().numpy())
        with torch.no_grad():
            rawq=z[:,:model.n]@model.Sq.T
            _,_,positions,_,_=model.mechanics(rawq,return_geometry=True)
            qlist.append(rawq.numpy());tips.append(positions[:,-1,:].numpy())
    return dict(x=x,h_res=np.concatenate(hlist),g_res=np.concatenate(glist),q_raw=np.concatenate(qlist),tip_m=np.concatenate(tips))


def scores(pred_h,pred_g,data,amplitude):
    true_g=data['g_res']+amplitude**2*data['x']
    error=pred_g-data['g_res']
    residual_norm=max(np.linalg.norm(data['g_res']),1e-30)
    return dict(gradient_relative_l2=float(np.linalg.norm(error)/np.linalg.norm(true_g)),
                residual_gradient_relative_l2=float(np.linalg.norm(error)/residual_norm),
                gradient_rmse=float(np.sqrt(np.mean(error**2))),
                energy_rmse=float(np.sqrt(np.mean((pred_h-data['h_res'])**2))),
                max_sample_gradient_error=float(np.max(np.linalg.norm(error,axis=1))))


def network_prediction(net,x,batch_size=256):
    hs=[];gs=[]
    for start in range(0,len(x),batch_size):
        xx=torch.tensor(x[start:start+batch_size],requires_grad=True)
        hh=net(xx);gg=torch.autograd.grad(hh.sum(),xx)[0]
        hs.append(hh.detach().numpy());gs.append(gg.detach().numpy())
    return np.concatenate(hs),np.concatenate(gs)


def model_checks(model,amplitude,output):
    rng=np.random.default_rng(102529)
    z=torch.tensor(rng.normal(size=(8,2*model.n)))*.08/torch.cat([torch.sqrt(model.nu)]*2)
    q=z[:,:model.n]@model.Sq.T
    m,v,r,frames,_=model.mechanics(q,return_geometry=True)
    so3=float(torch.max(torch.abs(frames.transpose(-1,-2)@frames-torch.eye(3))))
    lengths=torch.linalg.vector_norm(r[:,1:]-r[:,:-1],dim=-1)
    stretch=float(torch.max(torch.abs(lengths/model.ds-1)))
    eig=torch.linalg.eigvalsh(m)
    direction=torch.tensor(rng.normal(size=z.shape));direction/=torch.linalg.vector_norm(direction,dim=1)[:,None]
    _,g=model.gradient(z)
    eps=2e-6
    with torch.no_grad():fd=(model.hamiltonian(z+eps*direction)-model.hamiltonian(z-eps*direction))/(2*eps)
    derivative=float(torch.max(torch.abs(fd-(g*direction).sum(-1))))
    lin_hess=torch.autograd.functional.hessian(lambda a:model.hamiltonian(a[None,:])[0],torch.zeros(2*model.n))
    linear_defect=float(torch.linalg.norm(lin_hess-torch.diag(torch.cat([model.nu]*2)))/torch.linalg.norm(lin_hess))
    mesh=[]
    for cells in [20,40,80]:
        alt=RodROM(per_axis=model.n//3,elements=cells)
        with torch.no_grad():mm,vv=alt.mechanics(q)
        mesh.append(dict(elements=cells,mass=mm.numpy(),potential=vv.numpy()))
    mesh_result=[]
    for row in mesh[:-1]:
        mesh_result.append(dict(elements=row['elements'],mass_relative_l2=float(np.linalg.norm(row['mass']-mesh[-1]['mass'])/np.linalg.norm(mesh[-1]['mass'])),
                                potential_abs_max_J=float(np.max(np.abs(row['potential']-mesh[-1]['potential'])))))
    report=dict(SO3_defect=so3,segment_length_relative_defect=stretch,min_raw_mass_eigenvalue=float(eig.min()),
                directional_energy_gradient_max_abs_error=derivative,linear_modal_hessian_relative_defect=linear_defect,
                spatial_quadrature_comparison_to_80=mesh_result,
                warning='These are finite numerical checks, not a proof of continuum convergence or uniform error bounds.')
    (output/'rom_checks.json').write_text(json.dumps(report,indent=2))
    return report


def train_one(model,train,valid,test,ood,args,seed,output):
    torch.manual_seed(seed);rng=np.random.default_rng(seed)
    hscale=max(float(np.std(train['h_res'])),1e-7)
    gscale=max(float(np.sqrt(np.mean(train['g_res']**2))),1e-7)
    net=ComplexResidual(model.n,args.width,hscale)
    optimizer=torch.optim.Adam(net.parameters(),lr=args.lr)
    tx=torch.tensor(train['x']);th=torch.tensor(train['h_res']);tg=torch.tensor(train['g_res'])
    history=[];best=float('inf');best_state=None;start=time.perf_counter()
    for step in range(args.steps+1):
        idx=rng.integers(0,len(tx),size=args.batch)
        x=tx[idx].clone().requires_grad_(True)
        h=net(x);g=torch.autograd.grad(h.sum(),x,create_graph=True)[0]
        loss=((g-tg[idx])/gscale).square().mean()+.15*((h-th[idx])/hscale).square().mean()
        optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),10.);optimizer.step()
        if step%200==0 or step==args.steps:
            vh,vg=network_prediction(net,valid['x']);metric=scores(vh,vg,valid,args.amplitude)
            history.append(dict(step=step,training_loss=float(loss),validation=metric,wall_s=time.perf_counter()-start))
            if metric['residual_gradient_relative_l2']<best:
                best=metric['residual_gradient_relative_l2'];best_state={k:v.detach().clone() for k,v in net.state_dict().items()}
            print(json.dumps(dict(seed=seed,step=step,val_residual=metric['residual_gradient_relative_l2'],elapsed_s=time.perf_counter()-start)),flush=True)
    net.load_state_dict(best_state)
    result=dict(seed=seed,steps=args.steps,complex_trainable_parameters=sum(p.numel() for p in net.parameters()),
                real_parameter_count=sum(p.numel()*2 for p in net.parameters()),width=args.width,
                output_scale=hscale,gradient_loss_scale=gscale,training_seconds=time.perf_counter()-start,
                training_loss='derivative matching + 0.15 energy matching; real H; explicit conjugate inputs; p-even symmetrization; fixed linear Hamiltonian prior; cubic gate fixes equilibrium and linearization',
                activation='split real/imaginary tanh; real analytic in (z,zbar), not holomorphic tanh(z)')
    for name,data in [('test',test),('out_of_domain',ood)]:
        ph,pg=network_prediction(net,data['x']);result[name]=scores(ph,pg,data,args.amplitude)
    xx=torch.zeros(1,2*model.n,requires_grad=True);hh=net(xx);gg=torch.autograd.grad(hh.sum(),xx)[0]
    result['equilibrium_gradient_defect_x']=float(torch.linalg.norm(gg))
    hess=torch.autograd.functional.hessian(lambda a:net(a[None,:])[0],torch.zeros(2*model.n))
    result['linearization_hessian_defect_x']=float(torch.linalg.norm(hess))
    result['not_certified']=['uniform complex-domain error','positive mass representation of learned H','KAM existence','64-element closed-loop performance']
    torch.save(dict(state_dict=best_state,n=model.n,width=args.width,output_scale=hscale,amplitude=args.amplitude),output/f'complex_seed{seed}.pt')
    (output/f'training_seed{seed}.json').write_text(json.dumps(dict(result=result,history=history),indent=2))
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('stage2/results/learning'))
    p.add_argument('--steps',type=int,default=2400);p.add_argument('--width',type=int,default=48);p.add_argument('--batch',type=int,default=256)
    p.add_argument('--lr',type=float,default=.003);p.add_argument('--train',type=int,default=4096);p.add_argument('--amplitude',type=float,default=.35)
    p.add_argument('--seeds',type=int,nargs='+',default=[1025,1026,1027]);p.add_argument('--reuse-data',action='store_true')
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    model=RodROM();(out/'rom_metadata.json').write_text(json.dumps(model.metadata(),indent=2))
    np.savez(out/'rom_matrices.npz',M0=model.M0.numpy(),K0=model.K0,Sq=model.Sq.numpy(),Sp=model.Sp.numpy(),omega=model.omega,nu=model.nu.numpy())
    model_checks(model,args.amplitude,out)
    data_path=out/'learning_data.npz'
    sets={}
    if args.reuse_data and data_path.exists():
        raw=np.load(data_path)
        for name in ['train','validation','test','ood']:
            sets[name]={k:raw[name+'_'+k] for k in ['x','h_res','g_res','q_raw','tip_m']}
    else:
        rng=np.random.default_rng(20261029);start=time.perf_counter()
        for name,count,scale in [('train',args.train,1.),('validation',512,1.),('test',1024,1.),('ood',512,1.5)]:
            sets[name]=labels(model,rng.uniform(-scale,scale,size=(count,2*model.n)),args.amplitude)
            print(name,'labels done',round(time.perf_counter()-start,2),flush=True)
        np.savez_compressed(data_path,**{name+'_'+k:v for name,data in sets.items() for k,v in data.items()})
    values,design=polynomial_design(sets['train']['x'],model.n)
    coeff=np.linalg.lstsq(design.reshape(-1,4*model.n),sets['train']['g_res'].ravel(),rcond=1e-10)[0]
    np.save(out/'analytic_coefficients.npy',coeff)
    result=dict(environment=dict(python=__import__('sys').version,torch=torch.__version__,numpy=np.__version__,scipy=scipy.__version__,threads=1),
                data_sha256=hashlib.sha256(data_path.read_bytes()).hexdigest(),
                data_source='Independent full-phase samples labeled by the same 12-DOF variable-mass 3D Kirchhoff ROM, not patient observations or full-Cosserat truth',
                n_train=len(sets['train']['x']),n_test=len(sets['test']['x']),phase_dimension=2*model.n,
                canonical_state_box='x_j=sqrt(nu_j)*z_j/amplitude; train/test |x_j|<=1, OOD |x_j|<=1.5',amplitude=args.amplitude,
                baseline={},analytic_residual=dict(feature_count=len(coeff),definition='q_i^3, q_i^4, q_i^2*p_i^2, q_i^2*q_(i-1)^2; fixed features, linear least squares'),complex_network=[])
    for name in ['test','ood']:
        data=sets[name];v,d=polynomial_design(data['x'],model.n)
        result['baseline'][name]=scores(np.zeros(len(v)),np.zeros_like(data['g_res']),data,args.amplitude)
        result['analytic_residual'][name]=scores(v@coeff,np.einsum('bdf,f->bd',d,coeff),data,args.amplitude)
    for seed in args.seeds:
        result['complex_network'].append(train_one(model,sets['train'],sets['validation'],sets['test'],sets['ood'],args,seed,out))
        (out/'learning_summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
