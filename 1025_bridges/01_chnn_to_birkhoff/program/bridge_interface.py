"""Minimal bridge: unchanged frozen real CHNN Hamiltonian -> Birkhoff pair.

The only transport correction is removing the mechanical P-quadratic shortcut.
Existing coefficient, cache, represented-field algorithms are imported intact.
"""
from pathlib import Path
import sys
import time
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
for folder in ('stage3/program','stage5/program','stage6/fusion_reconciliation/program'):
    sys.path.insert(0,str(ROOT/folder))
from rom_bridge import ROMBridge
from learned_reference_tracking import LearnedReference
from transport_native import NativeTransport
from transport_cache import OneFormCache, CachedRepresentedField


class LearnedIdealBase:
    """Adapter to S6's frozen network loader, on S5's actual H_ideal coordinates.

    Deliberately exposes NO mass_tensor: a general learned H is not reconstructible
    from the physical mass and its P=0 slice. The physical ROM remains separate.
    """
    def __init__(self,physical=None):
        self.physical=ROMBridge() if physical is None else physical
        self.reference=LearnedReference(self.physical)
        self.n=self.physical.n
        self.J=self.physical.J
        self.K0=-self.J
        self.J_tensor=self.physical.J_tensor
        self.hamiltonian_tensor=self.reference.hamiltonian_tensor
        self._gradient=torch.func.grad(self.hamiltonian_tensor)

    def field_tensor(self,z):
        return self.J_tensor@self._gradient(z)

    def field(self,z):
        return self.field_tensor(torch.as_tensor(z,dtype=torch.float64)).detach().numpy()

    def jacobian(self,z):
        return torch.func.jacrev(self.field_tensor,chunk_size=1)(torch.as_tensor(z,dtype=torch.float64)).detach().numpy()

    def metadata(self):
        checkpoint={**self.reference.metadata,
            'plant':'H_ideal physical reference in bridge01; no full-coil plant is used',
            'loader_source':'S6 LearnedReference reused unchanged; its old coil-plant label is overridden here'}
        return dict(n=self.n,phase_dimension=2*self.n,checkpoint=checkpoint,
            physical_reference='H_ideal, actual 12-coordinate 20-cell variable-mass Kirchhoff ROM',
            learned_H='H0+full frozen complex-hidden residual, seed51001',
            mass_reconstruction=False,training_performed=False,
            canonical_time='tau=omega0*t_seconds',normalization=self.reference.scale.tolist())


class GeneralHamiltonianTransport(NativeTransport):
    def __init__(self,base,kind='state_dependent',force=None):
        # Crucial for a general learned H, even if another base exposes a mass.
        super().__init__(base=base,kind=kind,force=force,ad_backend='original')

    def legendre_difference(self,z):
        """H-P.H_P, valid without Legendre inversion or positive H_PP."""
        H=self.high_order_hamiltonian(z)
        gradient=torch.func.grad(self.high_order_hamiltonian)(z)
        return H-torch.dot(z[self.n:],gradient[self.n:])

    def metadata(self):
        return {**super().metadata(),
            'high_order_ad_identity':'Direct frozen real CHNN Hamiltonian; no mechanical reconstruction',
            'load':'Unchanged S5 smooth state-dependent canonical momentum load; not guaranteed to dissipate both H_ideal and Hhat, not blood/contact calibration',
            'first_homogeneous_coefficient':'grad(H-P.H_P)-(R,0)=-Lie_f(P,0)',
            'source_gauge':'a=(P,0)+b; B=H+b.f; b_t+Lie_f b=-(R,0)',
            'shortcut_scope':'2H(Q,0)-H is valid only for H=T_quadratic_in_P+V'}


def fit_network_cache(native,center,progress=None):
    """Same S5 Taylor cache, only its derivative evaluator changes.

    Torch2.5.1 vmap cannot differentiate complex conjugate negative views.
    Sequential reverse Jacobian rows preserve the exact network and formulas.
    Like S5's full-coil r2 cache: b1 quadratic, b2 linear, no field caching.
    """
    x=torch.as_tensor(center,dtype=torch.float64)
    values=[];jacobians=[];hessians=[];raw_hessians=[];costs=[]
    for k in (1,2):
        fun=native.source_coefficient_function(k);start=time.perf_counter()
        values.append(fun(x).detach().numpy())
        jacobians.append(torch.func.jacrev(fun,chunk_size=1)(x).detach().numpy())
        if k==1:
            hess=torch.func.jacrev(torch.func.jacrev(fun,chunk_size=1),chunk_size=1)(x).detach().numpy()
            antisym=float(np.linalg.norm(hess-hess.swapaxes(-1,-2)))
            assert antisym<1e-9
        else:
            hess=np.zeros((native.d,native.d,native.d));antisym=0.
        raw_hessians.append(hess.copy())
        # Same checked roundoff symmetrization as S5 OneFormCache.fit. It makes
        # coefficient_data exactly the derivative of the stored polynomial.
        hess=(hess+hess.swapaxes(-1,-2))/2
        hessians.append(hess)
        costs.append(dict(order=k,seconds=time.perf_counter()-start,spatial_degree=2 if k==1 else 1,
                          raw_hessian_antisymmetry_norm=antisym))
        if progress:progress(costs[-1])
    result=OneFormCache(center,values,jacobians,hessians,dict(spatial_degree=[2,1],costs=costs,
        source='New coefficients of the unchanged frozen Hhat and unchanged S5 R; no old H_ideal b2 reused',
        derivative='sequential reverse AD; same cache formulas; Torch2.5.1 complex vmap limitation',
        physical_field_cached=False,trained=False))
    result.raw_hessians=np.asarray(raw_hessians)
    return result


class LearnedRepresentedField(CachedRepresentedField):
    def jacobian(self,t,z):
        # Identical S5 expression, sequential reverse Hessian of the actual B.
        a=self.cache.data(z,t,self.order);fa=self(t,z)
        def B(x):
            return self.native.base.hamiltonian_tensor(x)+torch.dot(self.cache.b_tensor(x,t,self.order),self.native.field_tensor(x))
        HessB=torch.func.jacrev(torch.func.grad(B),chunk_size=1)(torch.as_tensor(z,dtype=torch.float64)).detach().numpy()
        return np.linalg.solve(a['K'],HessB+a['Dbt']-np.einsum('ijk,j->ik',a['DK'],fa))


def tensor_data(native,z,t,order):
    """Native time jet, with no spatial Taylor approximation."""
    x=torch.as_tensor(z,dtype=torch.float64)
    def b(y):
        return sum(t**k*native.source_coefficient_function(k)(y) for k in range(1,order+1))
    value=b(x);Db=torch.func.jacrev(b,chunk_size=1)(x)
    bt=sum(k*t**(k-1)*native.source_coefficient_function(k)(x) for k in range(1,order+1))
    f=native.field_tensor(x);Df=torch.func.jacrev(native.field_tensor,chunk_size=1)(x)
    force=native.force_tensor(x)
    K=native.K0+Db.T-Db
    eB=-(bt+Db@f+Df.T@value+torch.cat((force,torch.zeros_like(force))))
    return {k:v.detach().numpy() for k,v in dict(b=value,Db=Db,bt=bt,K=K,eB=eB,f=f).items()}


def independent_pair_diagnostics(native,physical,cache,z,t,order):
    """Differentiate a and B directly; compare to inherited cached evaluator.

    C = e_B + K(f_star-f_theta) is checked as a signed vector identity.
    """
    x=torch.as_tensor(z,dtype=torch.float64);n=native.n
    def alpha(y):return native.a0(y)+cache.b_tensor(y,t,order)
    def B(y):return native.base.hamiltonian_tensor(y)+torch.dot(cache.b_tensor(y,t,order),native.field_tensor(y))
    Da=torch.func.jacrev(alpha)(x).detach().numpy()
    K=Da.T-Da
    gradB=torch.func.grad(B)(x).detach().numpy()
    a=cache.data(z,t,order)
    ftheta,A,R=native.field_and_jacobian(z)
    fstar=physical.field(z)+np.r_[np.zeros(n),R]
    delta=ftheta-fstar
    eB=K@ftheta-gradB-a['bt']
    true_residual=K@fstar-gradB-a['bt']
    represented=LearnedRepresentedField(native,cache,order)
    fa,diag=represented(t,z,True)
    Dfa=represented.jacobian(t,z)
    compatibility=a['Kt']+np.einsum('ijk,k->ij',a['DK'],fa)+Dfa.T@K+K@Dfa
    closure=a['DK']+a['DK'].transpose(1,2,0)+a['DK'].transpose(2,0,1)
    gradtheta=torch.func.grad(native.base.hamiltonian_tensor)(x).detach().numpy()
    gradstar=torch.func.grad(physical.hamiltonian_tensor)(x).detach().numpy()
    force_vec=np.r_[np.zeros(n),R]
    bounds=dict(residual_bound=float(np.linalg.norm(eB)+np.linalg.norm(K,2)*np.linalg.norm(delta)),
        field_bound=float(np.linalg.norm(delta)+np.linalg.norm(np.linalg.inv(K),2)*np.linalg.norm(eB)))
    return dict(time=t,order=order,position=z.tolist(),learning_field_error=delta.tolist(),
        learning_field_error_norm=float(np.linalg.norm(delta)),e_B=eB.tolist(),e_B_norm=float(np.linalg.norm(eB)),
        true_field_pair_residual=true_residual.tolist(),true_field_pair_residual_norm=float(np.linalg.norm(true_residual)),
        split_identity_defect=float(np.linalg.norm(true_residual-(eB-K@delta))),
        direct_vs_inherited_eB=float(np.linalg.norm(eB-np.asarray(diag['e_B']))),
        represented_field_error_norm=float(np.linalg.norm(fa-ftheta)),
        represented_to_true_field_error_norm=float(np.linalg.norm(fa-fstar)),
        represented_compatibility_max=float(np.max(np.abs(compatibility))),
        closure_max=float(np.max(np.abs(closure))),K_min_singular=float(np.linalg.svd(K,compute_uv=False)[-1]),
        K_condition=float(np.linalg.cond(K)),original_learned_transport_defect=diag['original_transport_compatibility_2'],
        same_load_difference=0.,learning_gradient_field_identity=float(np.linalg.norm(delta-physical.J@(gradtheta-gradstar))),
        true_power=float(gradstar@fstar),learned_power=float(gradtheta@ftheta),
        true_power_identity=float(abs(gradstar@fstar-gradstar@force_vec)),
        learned_power_identity=float(abs(gradtheta@ftheta-gradtheta@force_vec)),
        **bounds)
