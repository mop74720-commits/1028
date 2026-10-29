"""A computable first-order transported one-form on the actual 24D rod ROM.

This is a local approximation from ONE fixed time origin. It is not reset at
each step. The damping Gamma P is a declared smooth test load. The exact chart
below exists because Gamma is constant diagonal, not because the rod mass is
constant. No physical exact flow or fitted conjugacy is used.
"""
from __future__ import annotations
import numpy as np
import torch
from rom_bridge import ROMBridge


class LocalBirkhoffROM:
    def __init__(self, bridge=None, rates=None):
        self.bridge = bridge or ROMBridge()
        self.n = self.bridge.n
        self.rates = np.linspace(.1, .3, self.n) if rates is None else np.asarray(rates)
        self.rate_tensor = torch.tensor(self.rates)
        self.J = self.bridge.J
        self.K0 = self.bridge.K0

    def a0_tensor(self, z):
        return torch.cat((z[self.n:], torch.zeros_like(z[:self.n])))

    def F_tensor(self, z):
        qzero = torch.cat((z[:self.n], torch.zeros_like(z[self.n:])))
        return 2*self.bridge.hamiltonian_tensor(qzero)-self.bridge.hamiltonian_tensor(z)

    def oneform_tensor(self, z, t):
        a0 = self.a0_tensor(z)
        gradient = torch.func.grad(self.F_tensor)(z)
        gamma_a0 = torch.cat((self.rate_tensor*z[self.n:], torch.zeros_like(z[:self.n])))
        return a0+t*(gradient+gamma_a0)

    def original_field(self, z):
        f = self.bridge.field(z)
        f[self.n:] -= self.rates*np.asarray(z)[self.n:]
        return f

    def original_jacobian(self, z):
        jac = self.bridge.jacobian(z)
        jac[self.n:, self.n:] -= np.diag(self.rates)
        return jac

    def weights(self, t):
        weights = 1+t*self.rates
        if np.min(weights) <= 0:
            raise ValueError('The local Birkhoff chart has left its positive nondegenerate domain')
        return weights

    def K(self, t):
        w = np.diag(self.weights(t)); zero = np.zeros_like(w)
        return np.block([[zero, -w], [w, zero]])

    def chart(self, z, t):
        return np.r_[z[:self.n], self.weights(t)*z[self.n:]]

    def inverse_chart(self, y, t):
        return np.r_[y[:self.n], y[self.n:]/self.weights(t)]

    def chart_jacobian(self, t):
        return np.diag(np.r_[np.ones(self.n), self.weights(t)])

    def gauge_hamiltonian(self, z, t):
        """B'=a.f+F=H+2t(V_Q+Gamma P).H_P, after a'=a-t*dF.

        Native AD retains all derivatives needed for the variable-mass field.
        z must require gradients when differentiating this scalar.
        """
        h = self.bridge.hamiltonian_tensor(z)
        dh = torch.autograd.grad(h, z, create_graph=True)[0]
        qzero = torch.cat((z[:self.n], torch.zeros_like(z[self.n:])))
        v = self.bridge.hamiltonian_tensor(qzero)
        dv = torch.autograd.grad(v, z, create_graph=True)[0]
        return h+2*t*torch.dot(dv[:self.n]+self.rate_tensor*z[self.n:], dh[self.n:])

    def gauge_gradient(self, z, t):
        x = torch.tensor(z, requires_grad=True)
        scalar = self.gauge_hamiltonian(x, t)
        return torch.autograd.grad(scalar, x)[0].detach().numpy()

    def approximate_field(self, t, z):
        g = self.gauge_gradient(z, t)
        w = self.weights(t)
        return np.r_[g[self.n:]/w, -(g[:self.n]+self.rates*z[self.n:])/w]

    def chart_field(self, t, y):
        z = self.inverse_chart(y, t)
        g = self.gauge_gradient(z, t)
        return np.r_[g[self.n:]/self.weights(t), -g[:self.n]]

    def diagnostics(self, z, t, differentiate_oneform=False):
        f = self.original_field(z)
        jac = self.original_jacobian(z)
        K = self.K(t); D = self.chart_jacobian(t)
        g = self.gauge_gradient(z, t)
        at = np.r_[self.rates*z[self.n:], np.zeros(self.n)]
        residual = K@f-g-at
        error = self.approximate_field(t, z)-f
        G = np.diag(self.rates); zero = np.zeros_like(G)
        Kt = np.block([[zero, -G], [G, zero]])
        out = dict(time=t, representation_residual_2=float(np.linalg.norm(residual)),
                   original_field_error_2=float(np.linalg.norm(error)),
                   inverse_K_residual_bound=float(np.linalg.norm(np.linalg.inv(K), 2)*np.linalg.norm(residual)),
                   original_transport_compatibility_2=float(np.linalg.norm(Kt+jac.T@K+K@jac, 2)),
                   chart_matching_2=float(np.linalg.norm(D.T@self.K0@D-K, 2)),
                   K_min_singular=float(np.linalg.svd(K, compute_uv=False)[-1]),
                   K_condition=float(np.linalg.cond(K)), chart_condition=float(np.linalg.cond(D)),
                   chart_inverse_error=float(np.linalg.norm(self.inverse_chart(self.chart(z,t),t)-z)),
                   closure='exact: K depends on t only, all spatial derivatives vanish',
                   interpretation='structure and original-field errors are independent; fixed expansion origin')
        if differentiate_oneform:
            x=torch.tensor(z)
            Da=torch.func.jacrev(lambda v:self.oneform_tensor(v,t))(x).detach().numpy()
            out['oneform_exterior_derivative_error_2']=float(np.linalg.norm(Da.T-Da-K,2))
            a=self.oneform_tensor(x,t).detach().numpy()
            a1=(self.oneform_tensor(x,1.)-self.oneform_tensor(x,0.)).detach().numpy()
            out['oneform_transport_PDE_residual_2']=float(np.linalg.norm(a1+Da@f+jac.T@a))
            out['PDE_vs_representation_residual_identity']=float(np.linalg.norm(a1+Da@f+jac.T@a+residual))
        return out
