"""Differentiable bridge to the delivered 12-coordinate 3-D Kirchhoff ROM.

Coordinates z=(Q,P) and time tau=omega0*t are dimensionless canonical variables.
Physical curvature coefficients are q=Sq@Q. The full 20-cell SO(3) embedding,
configuration-dependent mass, and its derivatives are inherited without alteration.
The ROM is inextensible/unshearable; full shear/stretch remains in the Cosserat
model. Fluid/contact closure is not silently invented for this smooth ROM.
"""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import torch

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[1] / 'source_inputs/starter/stage2/program/learning'
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))
from rod_rom import RodROM


class ROMBridge:
    """Exact differentiable Hamiltonian, derivatives and physical magnetic ports.

    ``u`` always means a physical SI field *increment* above the axial bias,
    ordered [Bx,By,Bz,Gxx,Gyy,Gxy,Gxz,Gyz]. The implied gradient is symmetric
    and trace-free. It is a local field interface, not an arbitrary modal force.
    ``gamma`` is an explicitly selected dimensionless proportional drag rate;
    it does not claim to approximate the delivered blood/contact operators.
    """

    def __init__(self, *, elements=20, config_path=None):
        torch.set_num_threads(1)
        self.rom = RodROM(config_path=config_path, per_axis=4, elements=elements)
        self.n = self.rom.n
        zero = np.zeros((self.n, self.n))
        self.J = np.block([[zero, np.eye(self.n)], [-np.eye(self.n), zero]])
        self.K0 = -self.J
        self.J_tensor = torch.tensor(self.J)
        self.bias = torch.cat((self.rom.B0, torch.zeros(5)))
        self._grad = torch.func.grad(self.hamiltonian_tensor)

    @staticmethod
    def tensor(value):
        return torch.as_tensor(value, dtype=torch.float64)

    def hamiltonian_tensor(self, z, u=None):
        """Scalar H/E0 with all geometric kinetic derivatives retained."""
        if u is None:
            return self.rom.hamiltonian(z[None, :])[0]
        q = self.rom.Sq @ z[:self.n]
        mass, potential = self.rom.mechanics(q[None, :], field=self.bias + u)
        scaled_mass = (self.rom.omega0**2/self.rom.E0) * (self.rom.Sq.T @ mass[0] @ self.rom.Sq)
        momentum = z[self.n:]
        return .5 * momentum @ torch.linalg.solve(scaled_mass, momentum) + (potential[0]-self.rom.V0)/self.rom.E0

    def hamiltonian(self, z, u=None):
        return float(self.hamiltonian_tensor(self.tensor(z), None if u is None else self.tensor(u)).detach())

    def field_tensor(self, z, gamma=0.0, u=None):
        # grad transformation keeps this method differentiable through third and
        # higher derivatives for nonseparable generating-function methods.
        grad = self._grad(z) if u is None else torch.func.grad(lambda x: self.hamiltonian_tensor(x, u))(z)
        return self.J_tensor @ grad - torch.cat((torch.zeros_like(z[:self.n]), gamma*z[self.n:]))

    def field(self, z, gamma=0.0, u=None):
        x = self.tensor(z).detach().requires_grad_(True)
        ht = self.hamiltonian_tensor(x, None if u is None else self.tensor(u))
        grad = torch.autograd.grad(ht, x)[0]
        result = self.J_tensor @ grad
        result = result - torch.cat((torch.zeros_like(x[:self.n]), gamma*x[self.n:]))
        return result.detach().numpy()

    def jacobian(self, z, gamma=0.0, u=None):
        ut = None if u is None else self.tensor(u)
        hess = torch.autograd.functional.hessian(lambda x: self.hamiltonian_tensor(x, ut), self.tensor(z), vectorize=True)
        result = self.J @ hess.detach().numpy()
        result[self.n:, self.n:] -= gamma*np.eye(self.n)
        return result

    def mass_tensor(self, Q, scaled=True):
        mass = self.rom.mechanics((self.rom.Sq @ Q)[None, :])[0][0]
        if scaled:
            return (self.rom.omega0**2/self.rom.E0)*(self.rom.Sq.T @ mass @ self.rom.Sq)
        return mass

    def mass(self, Q, scaled=True):
        return self.mass_tensor(self.tensor(Q), scaled=scaled).detach().numpy()

    def magnetic_potential_features_tensor(self, Q):
        """Eight coefficients d(V/E0)/du in physical SI field units."""
        q = self.rom.Sq @ Q
        # The zero-field elastic potential cancels. Eight simultaneous fields
        # keep the actual geometry and the documented Maxwell-compatible basis.
        qb = q[None, :].expand(9, self.n)
        fields = torch.cat((torch.eye(8), torch.zeros(1, 8)), dim=0)
        potential = self.rom.mechanics(qb, field=fields)[1]
        return (potential[:8]-potential[8])/self.rom.E0

    def magnetic_map_tensor(self, Q):
        return -torch.func.jacrev(self.magnetic_potential_features_tensor)(Q).T

    def magnetic_map(self, Q):
        """12x8 G_m(Q) such that Pdot_magnetic_increment = G_m(Q) @ u."""
        return self.magnetic_map_tensor(self.tensor(Q)).detach().numpy()

    def initial_state(self, amplitude=.01):
        indices = np.arange(self.n)
        scale = amplitude / np.sqrt(self.rom.nu.numpy())
        return np.r_[scale*np.cos(.7*indices+.2), .35*scale*np.sin(.9*indices+.3)]

    def metadata(self):
        return {**self.rom.metadata(), 'time': 'tau=omega0*t_seconds',
                'coordinates': 'z=(Q,P); q_physical=Sq Q; p_physical=Sp P',
                'input': 'SI increment above axial bias: Bx,By,Bz,Gxx,Gyy,Gxy,Gxz,Gyz',
                'drag': 'synthetic smooth gamma*P; not a blood/contact closure',
                'derivatives': 'double-precision automatic differentiation through full variable-mass SO(3) geometry'}
