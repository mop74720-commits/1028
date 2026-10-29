"""A 3-D Kirchhoff strain Ritz family with a configuration-dependent mass.

The fixed-base kinematic embedding is reduced; it is not a replacement for
the independently discretized Cosserat rod. All quantities before scaling use SI.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from numpy.polynomial.legendre import legval
import torch

torch.set_default_dtype(torch.float64)


def hat(v):
    zero=torch.zeros_like(v[...,0]);x,y,z=v.unbind(-1)
    return torch.stack([zero,-z,y,z,zero,-x,-y,x,zero],dim=-1).reshape(*v.shape[:-1],3,3)


def rotation_and_right_jacobian(theta):
    t2=(theta*theta).sum(-1)
    t=torch.sqrt(torch.clamp(t2,min=1e-12))
    small=t2<1e-5
    a=torch.where(small,1-t2/6+t2*t2/120-t2**3/5040,torch.sin(t)/t)
    b=torch.where(small,.5-t2/24+t2*t2/720-t2**3/40320,(1-torch.cos(t))/t2.clamp_min(1e-12))
    c=torch.where(small,1/6-t2/120+t2*t2/5040-t2**3/362880,(t-torch.sin(t))/(t*t2).clamp_min(1e-18))
    k=hat(theta);k2=k@k;eye=torch.eye(3,dtype=theta.dtype,device=theta.device)
    return eye+a[...,None,None]*k+b[...,None,None]*k2, eye-b[...,None,None]*k+c[...,None,None]*k2


class RodROM:
    def __init__(self, config_path=None, per_axis=4, elements=20):
        if config_path is None:config_path=Path(__file__).resolve().parents[1]/'rod3d'/'config.json'
        self.config=json.loads(Path(config_path).read_text())
        c=self.config['rod'];mag=self.config['magnet']
        self.L=c['length_m'];self.radius=c['radius_m'];self.rho=c['density_kg_m3']
        self.area=np.pi*self.radius**2;self.second_moment=np.pi*self.radius**4/4
        self.n=3*per_axis;self.elements=elements;self.ds=self.L/elements
        self.bending=torch.tensor([c['young_modulus_Pa']*self.second_moment]*2+[2*c['shear_modulus_Pa']*self.second_moment])
        self.rotary=torch.diag(torch.tensor([self.rho*self.second_moment]*2+[2*self.rho*self.second_moment]))
        self.B0=torch.tensor([0.,0.,mag['bias_z_T']])
        self.field_origin=torch.tensor(mag['field_origin_m'])
        mid=(np.arange(elements)+.5)/elements
        strain=np.zeros((elements,3,self.n))
        for axis in range(3):
            for j in range(per_axis):
                coefficients=np.zeros(j+1);coefficients[-1]=1
                strain[:,axis,axis*per_axis+j]=np.sqrt(2*j+1)*legval(2*mid-1,coefficients)/self.L
        self.strain=torch.tensor(strain)
        edges=np.linspace(0,self.L,elements+1)
        overlap=np.maximum(0,edges[1:]-np.maximum(edges[:-1],self.L-mag['distal_length_m']))
        self.segment_moment=torch.tensor(mag['line_dipole_A_m']*overlap)
        self.E0=mag['derived_total_dipole_A_m2']*mag['bias_z_T']
        q0=torch.zeros(1,self.n)
        self.M0,self.V0=self.mechanics(q0)
        self.M0=self.M0[0].detach();self.V0=float(self.V0[0])
        k0=torch.autograd.functional.hessian(lambda x:self.mechanics(x[None,:])[1][0],q0[0]).detach().numpy()
        evals,phi=eigh(k0,self.M0.numpy())
        if evals.min()<=0:raise ValueError('The selected equilibrium does not have positive linear stiffness')
        self.omega=np.sqrt(evals);self.omega0=float(self.omega[0]);self.nu=torch.tensor(self.omega/self.omega0)
        d=np.sqrt(self.E0/(self.omega0*self.omega))
        self.Sq=torch.tensor(phi*d[None,:])
        self.Sp=self.M0@torch.tensor(phi*(self.E0/self.omega0/d)[None,:])
        self.K0=k0

    def mechanics(self,q,field=None,return_geometry=False):
        batch=q.shape[0];dtype=q.dtype;device=q.device
        eye=torch.eye(3,dtype=dtype,device=device)
        rot=eye.expand(batch,3,3)
        omega_jac=torch.zeros(batch,3,self.n,dtype=dtype,device=device)
        position=torch.zeros(batch,3,dtype=dtype,device=device)
        position_jac=torch.zeros_like(omega_jac)
        mass=torch.zeros(batch,self.n,self.n,dtype=dtype,device=device)
        elastic=torch.zeros(batch,dtype=dtype,device=device)
        magnetic=torch.zeros_like(elastic)
        e3=torch.tensor([0.,0.,1.],dtype=dtype,device=device)
        e3hat=hat(e3)
        positions=[position];frames=[];centers=[]
        if field is None:
            b=self.B0.to(device).expand(batch,3);gradient=torch.zeros(batch,3,3,dtype=dtype,device=device)
        else:
            if field.ndim==1:field=field.expand(batch,8)
            b=field[:,:3]
            gradient=torch.stack([field[:,3],field[:,5],field[:,6],field[:,5],field[:,4],field[:,7],field[:,6],field[:,7],-field[:,3]-field[:,4]],-1).reshape(batch,3,3)
        for i in range(self.elements):
            strain=self.strain[i].to(device)
            curvature=q@strain.T
            theta=self.ds*curvature
            re,jr=rotation_and_right_jacobian(theta)
            half,jrh=rotation_and_right_jacobian(theta/2)
            rm=rot@half
            wm=half.transpose(-1,-2)@omega_jac+jrh@(self.ds/2*strain)
            delta=self.ds*rm[:,:,2]
            jdelta=-self.ds*(rm@e3hat)@wm
            center=position+.5*delta
            jc=position_jac+.5*jdelta
            mass=mass+self.rho*self.area*self.ds*(jc.transpose(-1,-2)@jc)
            mass=mass+self.ds*(wm.transpose(-1,-2)@self.rotary.to(device)@wm)
            elastic=elastic+.5*self.ds*(curvature**2*self.bending.to(device)).sum(-1)
            local_b=b+torch.einsum('bij,bj->bi',gradient,center-self.field_origin.to(device))
            magnetic=magnetic-self.segment_moment[i]*(rm[:,:,2]*local_b).sum(-1)
            position=position+delta;position_jac=position_jac+jdelta
            omega_jac=re.transpose(-1,-2)@omega_jac+jr@(self.ds*strain)
            rot=rot@re
            if return_geometry:
                positions.append(position);frames.append(rm);centers.append(center)
        if return_geometry:
            return mass,elastic+magnetic,torch.stack(positions,1),torch.stack(frames,1),torch.stack(centers,1)
        return mass,elastic+magnetic

    def hamiltonian(self,z):
        q=z[:,:self.n]@self.Sq.T;p=z[:,self.n:]
        mass,potential=self.mechanics(q)
        scaled_mass=(self.omega0**2/self.E0)*(self.Sq.T@mass@self.Sq)
        velocity=torch.linalg.solve(scaled_mass,p[...,None])[...,0]
        return .5*(p*velocity).sum(-1)+(potential-self.V0)/self.E0

    def gradient(self,z,create_graph=False):
        z=z.detach().clone().requires_grad_(True)
        h=self.hamiltonian(z)
        grad=torch.autograd.grad(h.sum(),z,create_graph=create_graph)[0]
        return h,grad

    def linear_energy(self,z):
        return .5*(self.nu*(z[:,:self.n]**2+z[:,self.n:]**2)).sum(-1)

    def metadata(self):
        q=np.zeros(self.n)
        defect=self.Sq.T.numpy()@self.Sp.numpy()-(self.E0/self.omega0)*np.eye(self.n)
        pairs=[]
        for i in range(self.n):
            for j in range(i+1,self.n):
                relative=abs(self.omega[i]-self.omega[j])/max(self.omega[i],self.omega[j])
                if relative<1e-7:pairs.append(dict(i=i,j=j,relative_difference=float(relative)))
        return dict(model='3D inextensible unshearable Kirchhoff strain Ritz; exact SO(3) frame updates and midpoint centerline embedding',
                    q_dof=self.n,phase_dimension=2*self.n,quadrature_elements=self.elements,
                    configuration='four Legendre curvature coefficients in each of two bending axes and torsion by default; all are dynamical',
                    mass='configuration dependent; includes translational and rotary inertia from embedding Jacobians',
                    E0_J=self.E0,omega0_rad_s=self.omega0,omega_rad_s=self.omega.tolist(),nu=self.nu.tolist(),
                    canonical_scaling_defect=float(np.linalg.norm(defect)),mass0_condition=float(np.linalg.cond(self.M0)),
                    repeated_frequency_pairs=pairs,
                    KAM_status='Standard nonresonant elliptic KAM is not certified; circular isotropic rod with axial bias has paired bending frequencies.',
                    relation_to_full_model='Shares material, distal magnet and field interface with the Cosserat model; shear/stretch omitted in this analytical ROM; modal truncation and fluid/contact closure errors are not yet bounded.')


if __name__=='__main__':
    torch.set_num_threads(1)
    model=RodROM();print(json.dumps(model.metadata(),indent=2))
    z=torch.zeros(1,2*model.n)
    h,g=model.gradient(z);print('origin H/gradient',h.tolist(),g.abs().max().item())
