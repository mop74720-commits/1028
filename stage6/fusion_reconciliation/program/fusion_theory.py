"""Executable parts restored from the fusion manuscript's general theory.

This module imports the stage5 model/cache rather than replacing its mechanics.
The physical-Hamiltonian gauge below is for the documented autonomous fixed-H
source-gauge branch. It does not silently treat time-dependent f as autonomous.
"""
from pathlib import Path
import sys
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'stage5/program'))


class PhysicalHamiltonianGauge:
    """Gauge (a0+b,H+b.f) to (a0+b+grad sigma,H) at fixed spatial z.

    sigma = sum(t**(k+1)/(k+1) b_k(z).f(z)).  All b_k are the existing
    one-form coefficient cache; f retains the full nonlinear variable mass.
    The construction leaves the represented field unchanged, not its error.
    """
    def __init__(self, native, cache, order):
        if not 1 <= order <= cache.maximum_order:
            raise ValueError('Unavailable coefficient order')
        self.native, self.cache, self.order = native, cache, order

    def integrated_b_tensor(self, z, t):
        delta = z-torch.as_tensor(self.cache.center, dtype=z.dtype)
        values = torch.as_tensor(self.cache.values[:self.order], dtype=z.dtype)
        jac = torch.as_tensor(self.cache.jacobians[:self.order], dtype=z.dtype)
        hess = torch.as_tensor(self.cache.hessians[:self.order], dtype=z.dtype)
        values = values+torch.einsum('rij,j->ri', jac, delta)+.5*torch.einsum('rijk,j,k->ri', hess, delta, delta)
        k = torch.arange(1, self.order+1, dtype=z.dtype)
        return torch.einsum('r,ri->i', t**(k+1)/(k+1), values)

    def sigma_tensor(self, z, t):
        return torch.dot(self.integrated_b_tensor(z, t), self.native.field_tensor(z))

    def source_scalar_tensor(self, z, t):
        return self.native.high_order_hamiltonian(z)+torch.dot(self.cache.b_tensor(z,t,self.order), self.native.field_tensor(z))

    def gradient_sigma_tensor(self, z, t):
        return torch.func.grad(lambda x:self.sigma_tensor(x,t))(z)

    def oneform_tensor(self, z, t):
        return self.native.a0(z)+self.cache.b_tensor(z,t,self.order)+self.gradient_sigma_tensor(z,t)

    def oneform_time_tensor(self, z, t):
        # d_t grad sigma = grad(b.f), with f autonomous. This retains Df.
        derivative = torch.func.jacfwd(lambda tt:self.cache.b_tensor(z,tt,self.order))(
            torch.as_tensor(t,dtype=z.dtype))
        return derivative+torch.func.grad(
            lambda x:torch.dot(self.cache.b_tensor(x,t,self.order),self.native.field_tensor(x)))(z)

    def diagnostics(self, z, t, *, hessian=True):
        x=torch.as_tensor(z,dtype=torch.float64)
        data=self.cache.data(z,t,self.order)
        f=self.native.field_tensor(x).detach().numpy()
        gradH=torch.func.grad(self.native.high_order_hamiltonian)(x).detach().numpy()
        gradB=torch.func.grad(lambda xx:self.source_scalar_tensor(xx,t))(x).detach().numpy()
        at=self.oneform_time_tensor(x,t).detach().numpy()
        old_rhs=gradB+data['bt']
        new_rhs=gradH+at
        represented=np.linalg.solve(data['K'],new_rhs)
        original_error=data['K']@f-new_rhs
        result=dict(sigma=float(self.sigma_tensor(x,t).detach()),
                    source_scalar=float(self.source_scalar_tensor(x,t).detach()),
                    gauge_scalar_H=float(self.native.high_order_hamiltonian(x).detach()),
                    gradient_sigma=self.gradient_sigma_tensor(x,t).detach().numpy(),
                    oneform=self.oneform_tensor(x,t).detach().numpy(),
                    oneform_time=at, represented_field=represented,
                    source_rhs=old_rhs,gauged_rhs=new_rhs,
                    rhs_gauge_defect=float(np.linalg.norm(new_rhs-old_rhs)),
                    original_field_representation_residual=float(np.linalg.norm(original_error)),
                    original_field_error=float(np.linalg.norm(represented-f)),
                    original_H_rate=float(gradH@f),represented_H_rate=float(gradH@represented),
                    wrong_unchanged_oneform_field=np.linalg.solve(data['K'],gradH+data['bt']))
        if hessian:
            Hess=torch.func.jacrev(torch.func.grad(lambda xx:self.sigma_tensor(xx,t)))(x).detach().numpy()
            # Do not symmetrize it to conceal a derivative failure.
            result['gauge_hessian']=Hess
            result['raw_gauge_hessian_antisymmetry']=float(np.linalg.norm(Hess-Hess.T,2))
            result['gauged_K']=data['K']+Hess.T-Hess
        return result


def chart_defect_decomposition(K0, Kminus, Kplus, Tminus, Tplus, internal, physical=None):
    """Exact matrix identity including internal and chain-rule errors.

    T are endpoint chart derivatives; internal is the chart-map derivative.
    If physical is supplied independently, its inverse/chain mismatch is also
    retained. Setting all implementation defects to zero is not implicit here.
    """
    if physical is None:
        physical=np.linalg.solve(Tplus,internal@Tminus)
    Eminus=Tminus.T@K0@Tminus-Kminus
    Eplus=Tplus.T@K0@Tplus-Kplus
    Delta=internal.T@K0@internal-K0
    base=internal@Tminus
    chain=Tplus@physical-base
    endpoint=Eminus-physical.T@Eplus@physical
    internal_term=Tminus.T@Delta@Tminus
    chain_term=base.T@K0@chain+chain.T@K0@base+chain.T@K0@chain
    observed=physical.T@Kplus@physical-Kminus
    predicted=endpoint+internal_term+chain_term
    return dict(physical=physical,endpoint_term=endpoint,internal_term=internal_term,
                chain_term=chain_term,chain_mismatch=chain,observed=observed,predicted=predicted,
                decomposition_residual=float(np.linalg.norm(observed-predicted,2)))


def formal_self_adjoint_defect(K_time, K_state, Db, velocity):
    """L=K d/dt+C for E=K(z,t) zdot-b(z,t), at an arbitrary velocity.

    K_state[i,j,k]=partial_k K[i,j], Db[i,j]=partial_j b[i].
    L*=K d/dt+dot K+C.T when K is skew. Thus C-C.T-dot K=0
    is the zeroth-order formal self-adjointness condition, not Df=Df.T.
    """
    C=np.einsum('ikj,k->ij',K_state,velocity)-Db
    dotK=K_time+np.einsum('ijk,k->ij',K_state,velocity)
    return C-C.T-dotK
