"""Differentiable full Biot--Savart magnetic energy on the inherited 3D ROM.

Every magnetic input is a TOTAL current in amperes. There is no extra ideal
axial-bias term in the Hamiltonian. Q,P,tau and the full M(Q) are unchanged.
Partial Hamiltonian derivatives hold current fixed; feedback is composed only
after constructing that physical vector field, so its Jacobian includes Di/Dz.
"""
from __future__ import annotations
from pathlib import Path
import sys
import copy
import numpy as np
import torch
from scipy.optimize import lsq_linear

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'stage3/program'))
from rom_bridge import ROMBridge
sys.path.insert(0, str(ROOT/'stage3/source_inputs/starter/stage2/program'))
from coil_field import make_array


class CoilROM(ROMBridge):
    def __init__(self, *, elements=20, wire_points=256, config_path=None, coil_config=None):
        super().__init__(elements=elements, config_path=config_path)
        self.coil_config = copy.deepcopy(make_array() if coil_config is None else coil_config)
        self.coil_config['quadrature_points'] = wire_points
        cfg = self.coil_config
        angle = (np.arange(wire_points)+.5)*2*np.pi/wire_points
        wire, dl = [], []
        # Same circle orientation and midpoint quadrature as stage2's
        # run_biot_savart.wire_quadrature, translated to torch for higher AD.
        for center, normal in zip(cfg['centers_m'], cfg['normals']):
            normal = np.asarray(normal)
            e1 = np.cross(normal, np.eye(3)[np.argmin(abs(normal))])
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(normal,e1)
            wire.append(np.asarray(center)+cfg['radius_m']*(np.cos(angle)[:,None]*e1+np.sin(angle)[:,None]*e2))
            dl.append(cfg['radius_m']*2*np.pi/wire_points*(-np.sin(angle)[:,None]*e1+np.cos(angle)[:,None]*e2))
        self.wire = torch.tensor(np.asarray(wire))
        self.dl = torch.tensor(np.asarray(dl))
        self.prefactor = 1e-7*cfg['turns']
        self.current_channels = len(wire)
        self.active = torch.nonzero(self.rom.segment_moment>0).flatten()
        self.origin = torch.tensor(cfg['origin_m'])
        self.zero_field = torch.zeros(8)
        b,g = self.field_basis_tensor(self.origin[None,:],gradient=True)
        self.origin_basis = b[0].detach()
        self.origin_gradient_basis = g[0].detach()
        self.local_mapping = torch.cat((b[0],g[0,0,0][None,:],g[0,1,1][None,:],g[0,0,1][None,:],g[0,0,2][None,:],g[0,1,2][None,:])).detach().numpy()
        scales = np.array([.001]*3+[.03]*5)
        a = np.vstack((self.local_mapping/scales[:,None],1e-3*np.eye(self.current_channels)))
        target = np.r_[self.bias.numpy()/scales,np.zeros(self.current_channels)]
        allocation = lsq_linear(a,target,bounds=(-cfg['current_bound_A'],cfg['current_bound_A']),tol=1e-12,lsmr_tol=1e-13,max_iter=200)
        if not allocation.success:
            raise RuntimeError(allocation.message)
        self.bias_currents = allocation.x
        self.bias_currents_tensor = torch.tensor(self.bias_currents)
        g0 = self.current_port(self.initial_state()[:self.n])
        self.collocated_gain = .2/np.linalg.norm(g0,2)**2

    def field_basis_tensor(self, points, gradient=False):
        """B[p,component,coil], optionally dB[p,component,axis,coil]. SI.

        Domain excludes ideal line conductors. This smooth function deliberately
        has no clamping/softening that would change Maxwell or the energy law.
        Analytic derivative is exactly stage2's Biot--Savart derivative formula.
        """
        distance = points[:,None,None,:]-self.wire[None,:,:,:]
        r = torch.linalg.vector_norm(distance,dim=-1)
        cross = torch.linalg.cross(self.dl[None,:,:,:].expand_as(distance),distance,dim=-1)
        values = self.prefactor*torch.sum(cross/r[...,None]**3,dim=2)
        b = values.permute(0,2,1)
        if not gradient:
            return b
        deriv = []
        for j in range(3):
            ej = torch.eye(3)[j].expand_as(self.dl)
            first = torch.linalg.cross(self.dl,ej,dim=-1)[None,:,:,:]/r[...,None]**3
            second = 3*cross*distance[...,j,None]/r[...,None]**5
            deriv.append((self.prefactor*torch.sum(first-second,dim=2)).permute(0,2,1))
        return b,torch.stack(deriv,dim=2)

    def magnetic_geometry_tensor(self,Q):
        rawq = self.rom.Sq@Q
        _,_,_,frames,centers = self.rom.mechanics(rawq[None,:],field=self.zero_field,return_geometry=True)
        return centers[0,self.active],frames[0,self.active,:,2]*self.rom.segment_moment[self.active,None]

    def magnetic_features_from_geometry(self,centers,moments,model='full'):
        if model=='full':
            b = self.field_basis_tensor(centers)
        elif model=='affine':
            b = self.origin_basis[None,:,:]+torch.einsum('abj,pb->paj',self.origin_gradient_basis,centers-self.origin)
        else:
            raise ValueError("model must be full or affine")
        return -torch.einsum('pa,paj->j',moments,b)/self.rom.E0

    def magnetic_features_tensor(self,Q,model='full'):
        return self.magnetic_features_from_geometry(*self.magnetic_geometry_tensor(Q),model=model)

    def coil_potential_tensor(self,Q,currents,model='full'):
        """Total magnetic potential V_coil/E0, linear in amperes."""
        return self.magnetic_features_tensor(Q,model)@currents

    def current_port_tensor(self,Q,model='full'):
        """G_coil(Q)=-d_Q d_i(V_coil/E0), shape (12,12), per ampere."""
        return -torch.func.jacrev(lambda x:self.magnetic_features_tensor(x,model))(Q).T

    def current_port(self,Q,model='full'):
        return self.current_port_tensor(self.tensor(Q),model).detach().numpy()

    def hamiltonian_tensor(self,z,currents=None,model='full'):
        if currents is None:
            currents=self.bias_currents_tensor
        q = self.rom.Sq@z[:self.n]
        mass,elastic,_,frames,centers = self.rom.mechanics(q[None,:],field=self.zero_field,return_geometry=True)
        scaled = (self.rom.omega0**2/self.rom.E0)*(self.rom.Sq.T@mass[0]@self.rom.Sq)
        p=z[self.n:]
        moments=frames[0,self.active,:,2]*self.rom.segment_moment[self.active,None]
        magnetic = self.magnetic_features_from_geometry(centers[0,self.active],moments,model)@currents
        return .5*p@torch.linalg.solve(scaled,p)+elastic[0]/self.rom.E0+magnetic

    def hamiltonian(self,z,currents=None,model='full'):
        return float(self.hamiltonian_tensor(self.tensor(z),None if currents is None else self.tensor(currents),model).detach())

    def field_tensor(self,z,currents=None,gamma=0.,model='full'):
        if currents is None:
            currents=self.bias_currents_tensor
        # argnums=0 makes this a physical PARTIAL derivative at fixed current.
        grad=torch.func.grad(lambda zz,ii:self.hamiltonian_tensor(zz,ii,model),argnums=0)(z,currents)
        return self.J_tensor@grad-torch.cat((torch.zeros_like(z[:self.n]),gamma*z[self.n:]))

    def field(self,z,currents=None,gamma=0.,model='full'):
        return self.field_tensor(self.tensor(z),None if currents is None else self.tensor(currents),gamma,model).detach().numpy()

    def jacobian(self,z,currents=None,gamma=0.,model='full'):
        current=self.bias_currents_tensor if currents is None else self.tensor(currents)
        return torch.func.jacrev(lambda x:self.field_tensor(x,current,gamma,model))(self.tensor(z)).detach().numpy()

    def collocated_current_tensor(self,z,gain=None,model='full'):
        gain=self.collocated_gain if gain is None else gain
        velocity=torch.linalg.solve(self.mass_tensor(z[:self.n]),z[self.n:])
        return self.bias_currents_tensor-gain*self.current_port_tensor(z[:self.n],model).T@velocity

    def feedback_field_tensor(self,z,gain=None,gamma=0.,model='full'):
        current=self.collocated_current_tensor(z,gain,model)
        return self.field_tensor(z,current,gamma,model)

    def feedback_field(self,z,gain=None,gamma=0.,model='full'):
        return self.feedback_field_tensor(self.tensor(z),gain,gamma,model).detach().numpy()

    def feedback_jacobian(self,z,gain=None,gamma=0.,model='full'):
        return torch.func.jacrev(lambda x:self.feedback_field_tensor(x,gain,gamma,model))(self.tensor(z)).detach().numpy()

    def physical_samples(self,Q,currents):
        """Actual magnet integration-point B/G; no continuum maximum claim."""
        centers,_=self.magnetic_geometry_tensor(self.tensor(Q))
        b,g=self.field_basis_tensor(centers,gradient=True)
        current=self.tensor(currents)
        field=(b@current).detach().numpy()
        gradient=(g@current).detach().numpy()
        points=centers.detach().numpy()
        # Exact distance to each circular wire, not just sampled conductor nodes.
        centers_coil=np.asarray(self.coil_config['centers_m']);normals=np.asarray(self.coil_config['normals'])
        offset=points[:,None,:]-centers_coil[None,:,:]
        axial=np.einsum('pcj,cj->pc',offset,normals)
        radius=np.sqrt(np.maximum(0.,np.sum(offset**2,axis=2)-axial**2))
        distance=np.sqrt(axial**2+(radius-self.coil_config['radius_m'])**2)
        return dict(points_m=points,field_T=field,gradient_T_per_m=gradient,
                    maximum_B_T=float(np.max(np.linalg.norm(field,axis=1))),
                    maximum_G_T_per_m=float(np.max(np.linalg.norm(gradient,axis=(1,2)))),
                    minimum_distance_exact_wire_m=float(distance.min()))

    def metadata(self):
        return {**super().metadata(),'magnetism':'Full circular-coil Biot-Savart energy; no additional ideal bias',
                'input':'12 total coil currents in A; no separate 8-field increment input or extra ideal bias',
                'coil_config':self.coil_config,'current_channels':self.current_channels,
                'current_units':'A; total currents, not increments',
                'bias_currents_A':self.bias_currents.tolist(),
                'bias_origin_field_gradient_residual':(self.local_mapping@self.bias_currents-self.bias.numpy()).tolist(),
                'bias_initialization':'Pre-energized fixed local axial-bias fit; not a zero-current startup',
                'collocated_gain_dimensionless':self.collocated_gain,
                'collocated_gain_A2_per_W':self.collocated_gain/(self.rom.E0*self.rom.omega0),
                'feedback_derivative':'Hamiltonian partial z derivative first; compose i(z) afterwards; total field Jacobian contains Di/Dz',
                'magnetic_domain':'Away from ideal circular wires; physical_samples evaluates actual magnet quadrature points only',
                'constraints':'Smooth feedback not automatically bounded; coil_control handles explicit constrained current ramps.'}
