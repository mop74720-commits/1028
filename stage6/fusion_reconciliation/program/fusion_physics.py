"""Recover the fusion manuscript's work governor on the actual 3D coil ROM.

This module reuses the inherited 20-cell variable-mass geometry, magnetic
energy/force and current allocator. It adds a power half-space in *amperes*.
Decision-point and sampled trajectory checks are not a sample-hold safety
certificate: such a certificate additionally needs power/field envelopes over
each interval. See proofs/physics_corrections.md.
"""
from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import torch
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'stage5/program'))
from coil_rom import CoilROM
from coil_control import CurrentAllocator, ramp_current


def clearance_coefficient(length_m, bending_lower_N_m2, shear_extension_lower_N=np.inf):
    """C in max |r(s)-s e3|^2 <= C E_el, with a clamped straight rest rod.

    B >= b I and S >= s I, E_el is in joules. This is a sufficient geometric
    bound, not a curved-vessel or contact certificate. The Kirchhoff limit is
    s=inf. The bound also holds for the inherited uniform midpoint polygon;
    its discrete bending kernel has a smaller squared norm.
    """
    if length_m <= 0 or bending_lower_N_m2 <= 0 or shear_extension_lower_N <= 0:
        raise ValueError('Positive length and stiffness lower bounds required')
    return 2 * (length_m**3 / (3 * bending_lower_N_m2)
                + length_m / shear_extension_lower_N)


def mechanical_energy(model, z):
    """(T+V_el)/E0, excluding signed magnetic potential at all currents."""
    return model.hamiltonian(z, np.zeros(model.current_channels))


def power_port(model, z):
    """y=G_coil(Q)^T dH_mech/dP, so dE_mech/dtau=y.i-gamma v.P."""
    velocity = np.linalg.solve(model.mass(z[:model.n]), z[model.n:])
    return model.current_port(z[:model.n]).T @ velocity, velocity


class PowerCurrentAllocator(CurrentAllocator):
    """Strictly convex current projection with inherited physical constraints.

    A finite current slew limit can exclude zero current and make the added
    power constraint infeasible. In that event we raise and preserve failure;
    we do not silently use an unreachable generalized force.
    """
    def allocate_power(self, z, requested, previous, physical_interval_s, power_upper):
        model = self.model
        previous = np.asarray(previous, dtype=float)
        requested = np.asarray(requested, dtype=float)
        seed, inherited = super().allocate(z[:model.n], requested, previous, physical_interval_s)
        y, _ = power_port(model, z)
        cap = model.coil_config['slew_bound_A_s'] * physical_interval_s
        bound = model.coil_config['current_bound_A']
        lo = np.maximum(-bound, previous-cap)
        hi = np.minimum(bound, previous+cap)
        with torch.no_grad():
            points, _ = model.magnetic_geometry_tensor(model.tensor(z[:model.n]))
            b, g = model.field_basis_tensor(points, gradient=True)
        b = b.numpy()
        g = g.numpy().reshape(len(points), 9, model.current_channels)
        # Normalize the half-space without changing it; an absolute SLSQP
        # tolerance on a ~1e-7 canonical power is otherwise misleading.
        power_scale = max(np.linalg.norm(y)*bound, abs(power_upper), 1e-14)
        def cons(i):
            return np.r_[1-np.sum((b@i/self.field_bound)**2, axis=1),
                         1-np.sum((g@i/self.gradient_bound)**2, axis=1),
                         (power_upper-y@i)/power_scale]
        def jac(i):
            return np.vstack((-2*np.einsum('pa,paj->pj',b@i,b)/self.field_bound**2,
                              -2*np.einsum('pa,paj->pj',g@i,g)/self.gradient_bound**2,
                              -y[None, :]/power_scale))
        sol = minimize(lambda i: .5*np.sum((i-requested)**2), seed,
                       jac=lambda i: i-requested, method='SLSQP',
                       bounds=list(zip(lo, hi)),
                       constraints=[dict(type='ineq', fun=cons, jac=jac)],
                       options={'ftol': 1e-13, 'maxiter': 400, 'disp': False})
        violation = max(0., float(-cons(sol.x).min()), float((lo-sol.x).max()), float((sol.x-hi).max()))
        if not sol.success or violation > 1e-9:
            raise RuntimeError(f'Power/current allocation infeasible or unresolved: {sol.message}; normalized violation={violation:.3e}')
        i = sol.x
        return i, {**inherited, 'success': True, 'iterations': int(sol.nit),
                   'message': str(sol.message), 'allocated_current_A': i.tolist(),
                   'current_request_distance_A': float(np.linalg.norm(i-requested)),
                   'generalized_force_allocation_residual': float(np.linalg.norm(model.current_port(z[:model.n])@(i-requested))),
                   'maximum_planned_slew_A_s': float(np.max(abs(i-previous)/physical_interval_s)),
                   'constraint_violation': violation, 'power_upper_dE0_dtau': float(power_upper),
                   'allocated_power_dE0_dtau': float(y@i),
                   'power_upper_W': float(power_upper*model.rom.E0*model.rom.omega0),
                   'power_constraint_scope': 'decision state only; no between-sample envelope claimed'}


def ramp_rk4(model, z, current0, current1, h, gamma, subdivisions=1):
    """Integrate full-coil dynamics and its actual mechanical-work ledger.

    Current ramps, rather than jumps, enforce the allocated physical slew.
    The ledger uses actual power along the numerical trajectory, not a claimed
    conservative sample-hold envelope. Independent energy drift is returned.
    """
    n = model.n
    state = np.r_[z, 0., 0.]
    records = []
    def rhs(t, x):
        i = ramp_current(current0, current1, t, 0., h)
        f = model.field(x[:2*n], i, gamma=gamma)
        # Fixed-current Hamiltonian field at zero current gives grad E_mech;
        # the difference is the actual magnetic generalized force, so this
        # avoids a second Jacobian of all twelve coil features at each stage.
        f0 = model.field(x[:2*n], np.zeros(model.current_channels), gamma=0.)
        grad = -model.J @ f0
        dissipation = gamma * f[:n] @ x[n:2*n]
        power = grad @ f + dissipation
        records.append(dict(tau=float(t), power=float(power),
                            dissipation=float(dissipation)))
        return np.r_[f, power, dissipation]
    dt = h/subdivisions
    for k in range(subdivisions):
        t = k*dt
        a = rhs(t, state)
        b = rhs(t+dt/2, state+dt*a/2)
        c = rhs(t+dt/2, state+dt*b/2)
        d = rhs(t+dt, state+dt*c)
        state += dt*(a+2*b+2*c+d)/6
    residual = mechanical_energy(model, state[:2*n])-mechanical_energy(model, z)-state[-2]+state[-1]
    return state[:2*n], float(state[-2]), float(state[-1]), float(residual), records

