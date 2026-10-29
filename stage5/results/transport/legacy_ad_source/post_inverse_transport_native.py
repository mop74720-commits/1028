"""Exact local transport coefficients evaluated on the nonlinear 24D rod ROM.

The supplied conservative model must retain its full M(q). The optional force
is a generalized nonconservative load, not an unconstrained magnetic command.
No exact physical flow is used. torch.func derivatives remain differentiable.
"""
from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import torch

STAGE3 = Path(__file__).resolve().parents[2]/'stage3/program'
if str(STAGE3) not in sys.path:
    sys.path.insert(0,str(STAGE3))
from rom_bridge import ROMBridge


class NativeTransport:
    def __init__(self, base=None, force=None, kind='state_dependent',ad_backend='inverse'):
        self.base = ROMBridge() if base is None else base
        self.n = self.base.n
        self.d = 2*self.n
        self.J = torch.as_tensor(self.base.J,dtype=torch.float64)
        self.K0 = -self.J
        self.kind = kind
        self.ad_backend=ad_backend
        self.force_override = force
        self.rates = torch.linspace(.1,.3,self.n)
        cross = torch.cos(.7*torch.arange(self.n,dtype=torch.float64))
        self.cross = cross/torch.linalg.vector_norm(cross)
        self._gradH = torch.func.grad(self.high_order_hamiltonian)
        self._gradF = torch.func.grad(self.legendre_difference)
        self._coeff = [self.a0,self.a1]
        self._source_coeff = [lambda z: torch.zeros_like(z),self.b1]

    def legendre_difference(self,z):
        zero_momentum = torch.cat((z[:self.n],torch.zeros_like(z[self.n:])))
        return 2*self.high_order_hamiltonian(zero_momentum)-self.high_order_hamiltonian(z)

    def high_order_hamiltonian(self,z):
        """Algebraically identical full M(q), avoiding mixed-high-AD solve bug.

        Original numeric field/reference continues to call base.field (solve).
        The inverse is recomputed at the actual q; no constant mass is used.
        Independently validated pure reverse derivatives are required, because
        algebraic equality alone does not establish an AD implementation.
        """
        if self.ad_backend=='original' or not hasattr(self.base,'mass_tensor'):
            return self.base.hamiltonian_tensor(z)
        if self.ad_backend!='inverse':raise ValueError(self.ad_backend)
        p=z[self.n:]
        qzero=torch.cat((z[:self.n],torch.zeros_like(p)))
        inverse=torch.linalg.inv(self.base.mass_tensor(z[:self.n]))
        return .5*p@inverse@p+self.base.hamiltonian_tensor(qzero)

    def force_tensor(self,z):
        if self.force_override is not None:
            return self.force_override(z)
        p=z[self.n:]
        if self.kind=='conservative':
            return torch.zeros_like(p)
        if self.kind=='proportional':
            return -.2*p
        if self.kind!='state_dependent':
            raise ValueError(self.kind)
        # Positive but nonproportional synthetic smooth canonical drag. Its
        # state dependence is explicit and is NOT identified blood friction.
        q=z[:self.n]
        rates=self.rates*(1+.15*torch.tanh(q/.02))
        return -rates*(p+.1*p**3/.002**2)-.04*self.cross*torch.dot(self.cross,p)

    def field_tensor(self,z):
        return self.J@self._gradH(z)+torch.cat((torch.zeros_like(z[:self.n]),self.force_tensor(z)))

    def a0(self,z):
        return torch.cat((z[self.n:],torch.zeros_like(z[:self.n])))

    def a1(self,z):
        # Exact for H=T(q,p)+V(q), T homogeneous quadratic in p. This avoids
        # evaluating an unnecessary Hessian and preserves variable-mass terms.
        return self._gradF(z)-torch.cat((self.force_tensor(z),torch.zeros_like(z[:self.n])))

    def b1(self,z):
        return -torch.cat((self.force_tensor(z),torch.zeros_like(z[:self.n])))

    def source_coefficient_function(self,order):
        """a'=a0+sum(t^k b_k), B'=H+sum(t^k b_k).f.

        Its transport source is d(T-V); it is NOT a homogeneous transported
        one-form. At finite order this is a different truncation from simply
        applying a truncated gauge to a0+sum(t^k a_k).
        """
        while len(self._source_coeff)<=order:
            previous=self._source_coeff[-1]
            k=len(self._source_coeff)
            self._source_coeff.append(lambda z,previous=previous,k=k:-self.lie_oneform(previous,z)/k)
        return self._source_coeff[order]

    def lie_oneform(self,alpha,z):
        f=self.field_tensor(z)
        tangent=torch.func.jvp(alpha,(z,),(f,))[1]
        _,pullback=torch.func.vjp(self.field_tensor,z)
        return tangent+pullback(alpha(z))[0]

    def coefficient_function(self,order):
        while len(self._coeff)<=order:
            previous=self._coeff[-1]
            k=len(self._coeff)
            self._coeff.append(lambda z,previous=previous,k=k:-self.lie_oneform(previous,z)/k)
        return self._coeff[order]

    def oneform(self,z,t,order):
        return sum(t**k*self.coefficient_function(k)(z) for k in range(order+1))

    def coefficient(self,z,order):
        return self.coefficient_function(order)(torch.as_tensor(z,dtype=torch.float64)).detach().numpy()

    def field(self,z):
        z=np.asarray(z)
        force=self.force_tensor(torch.as_tensor(z)).detach().numpy()
        return self.base.field(z)+np.r_[np.zeros(self.n),force]

    def field_and_jacobian(self,z):
        z=np.asarray(z)
        x=torch.as_tensor(z,dtype=torch.float64)
        force=self.force_tensor(x).detach().numpy()
        Dforce=torch.func.jacrev(self.force_tensor)(x).detach().numpy()
        field=self.base.field(z)+np.r_[np.zeros(self.n),force]
        jacobian=self.base.jacobian(z)
        jacobian[self.n:,:]+=Dforce
        return field,jacobian,force

    def metadata(self):
        return dict(base=self.base.metadata(), kind=self.kind,
                    load='independent supplied force' if self.force_override is not None else
                    'smooth nonproportional positive canonical momentum drag with q-dependent rates, cubic p term, rank-one cross coupling; not a blood/contact calibration',
                    exact_flow_used=False, mass_frozen=False,
                    high_order_ad_backend=self.ad_backend,
                    high_order_ad_identity='0.5 p.T inv(M_full(q)) p + H_base(q,0); original numeric/reference field retains base solve implementation',
                    recurrence='a_(k+1)=-(Da_k f + Df.T a_k)/(k+1); fixed expansion origin')
