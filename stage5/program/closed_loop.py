"""One physical full-coil field per branch, including feedback chain rules.

The magnetic force is the partial configuration derivative at fixed current.
It is evaluated at a state-dependent current only *after* that derivative;
grad(H(z, i(z))) would describe a different and generally incorrect plant.
"""
from pathlib import Path
import sys
import numpy as np
import torch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'stage3/program'))
from rom_integrators import central4 as inherited_central4

TOLERANCE = 2e-13


class FixedCurrentHamiltonian:
    """Adapter that reuses the frozen, nonseparable Central4 implementation."""
    def __init__(self, model, currents):
        self.model = model
        self.currents = np.asarray(currents, dtype=float).copy()
        self.current_tensor = torch.as_tensor(self.currents, dtype=torch.float64)
        self.n, self.J, self.K0 = model.n, model.J, model.K0

    def hamiltonian_tensor(self, z):
        return self.model.hamiltonian_tensor(z, currents=self.current_tensor)

    def field(self, z, gamma=0.):
        return self.model.field(z, currents=self.currents, gamma=gamma)

    def jacobian(self, z, gamma=0.):
        return self.model.jacobian(z, currents=self.currents, gamma=gamma)


class ClosedLoop:
    """Actual ROM field; no post-step phase-space control increment."""
    def __init__(self, model, kind='conservative', gamma=.2, gain=None):
        if kind not in ('conservative', 'proportional', 'collocated'):
            raise ValueError(kind)
        self.model, self.kind = model, kind
        self.n, self.J, self.K0 = model.n, model.J, model.K0
        self.gamma = float(gamma) if kind == 'proportional' else 0.
        self.gain = model.collocated_gain if gain is None else float(gain)
        self.currents = np.asarray(model.bias_currents, dtype=float).copy()
        self.current_tensor = torch.as_tensor(self.currents, dtype=torch.float64)
        self.fixed = FixedCurrentHamiltonian(model, self.currents)

    def field_tensor(self, z):
        if self.kind == 'collocated':
            return self.model.feedback_field_tensor(z, gain=self.gain)
        return self.model.field_tensor(z, currents=self.current_tensor, gamma=self.gamma)

    def field(self, t, z):
        if self.kind != 'collocated':
            return self.model.field(z, currents=self.currents, gamma=self.gamma)
        x = torch.as_tensor(z, dtype=torch.float64)
        return self.field_tensor(x).detach().numpy()

    def jacobian(self, z):
        if self.kind != 'collocated':
            return self.model.jacobian(z, currents=self.currents, gamma=self.gamma)
        # This is deliberately the whole closed-loop Jacobian. Holding the
        # command fixed here would omit D(G_i^T H_P) and change Newton's matrix.
        return torch.func.jacrev(self.field_tensor)(torch.as_tensor(z)).detach().numpy()

    def current_command(self, z):
        if self.kind == 'collocated':
            return self.model.collocated_current_tensor(torch.as_tensor(z), gain=self.gain).detach().numpy()
        return self.currents.copy()

    def energy_and_power(self, z):
        """Both fixed-bias energy and mechanical energy balances, same field."""
        x = torch.as_tensor(z, dtype=torch.float64)
        current = self.current_command(z)
        fixed_grad = torch.func.grad(self.fixed.hamiltonian_tensor)(x).detach().numpy()
        velocity = fixed_grad[self.n:]
        port = self.model.current_port(z[:self.n])
        magnetic_power = float(velocity @ port @ current)
        incremental_power = float(velocity @ port @ (current-self.currents))
        drag_power = float(-self.gamma*velocity @ np.asarray(z[self.n:]))
        zero = torch.zeros_like(self.current_tensor)
        mechanical_H = lambda y: self.model.hamiltonian_tensor(y, currents=zero)
        mechanical_grad = torch.func.grad(mechanical_H)(x).detach().numpy()
        f = self.field(0., z)
        return dict(fixed_bias_energy=float(self.fixed.hamiltonian_tensor(x).detach()),
                    mechanical_energy=float(mechanical_H(x).detach()),
                    fixed_bias_power=incremental_power+drag_power,
                    mechanical_power=magnetic_power+drag_power,
                    magnetic_power=magnetic_power, incremental_magnetic_power=incremental_power,
                    drag_power=drag_power,
                    fixed_bias_power_identity_residual=float(fixed_grad@f-incremental_power-drag_power),
                    mechanical_power_identity_residual=float(mechanical_grad@f-magnetic_power-drag_power),
                    current=current.tolist(),
                    collocated_expected_power=float(-self.gain*np.linalg.norm(port.T@velocity)**2)
                        if self.kind == 'collocated' else None)

    def structure(self, z):
        A = self.jacobian(z)
        defect = A.T@self.K0+self.K0@A
        return dict(original_canonical_transport_defect_2=float(np.linalg.norm(defect, 2)),
                    proportional_transport_defect_2=float(np.linalg.norm(defect+self.gamma*self.K0, 2)),
                    jacobian_condition=float(np.linalg.cond(A)),
                    jacobian_spectral_norm=float(np.linalg.norm(A, 2)),
                    original_form_preserved=self.kind == 'conservative',
                    weighted_form_available=self.kind == 'proportional',
                    new_Ku_required_for_Birkhoff_claim=self.kind == 'collocated',
                    statement='Pointwise diagnostics; no uniform domain or KAM certificate.')


def implicit_midpoint(loop, z, h, *, tolerance=TOLERANCE, max_iterations=12):
    """Newton on the complete increment, with the actual feedback derivative."""
    import time
    start = time.perf_counter()
    z = np.asarray(z, dtype=float)
    y = z+h*loop.field(0., z)
    eye = np.eye(z.size)
    history = []
    for iteration in range(max_iterations+1):
        middle = (z+y)/2
        residual = y-z-h*loop.field(0., middle)
        norm = float(np.linalg.norm(residual, np.inf))
        A = loop.jacobian(middle)
        matrix = eye-.5*h*A
        history.append(dict(iteration=iteration, residual_inf=norm,
                            matrix_condition=float(np.linalg.cond(matrix))))
        if not np.isfinite(norm):
            raise FloatingPointError('Nonfinite full closed-loop midpoint residual')
        if norm <= tolerance:
            tangent = np.linalg.solve(matrix, eye+.5*h*A)
            return y, tangent, dict(increment_residual_inf=norm, nonlinear_corrections=iteration,
                final_matrix_condition=float(np.linalg.cond(matrix)),
                final_matrix_min_singular=float(np.linalg.svd(matrix, compute_uv=False)[-1]),
                newton_history=history, seconds=time.perf_counter()-start,
                derivative='Full Df of state-dependent input; ideal implicit tangent')
        if iteration == max_iterations:
            break
        correction = np.linalg.solve(matrix, residual)
        # Backtracking changes only the nonlinear solver, not its target map.
        scale = 1.
        for _ in range(8):
            candidate = y-scale*correction
            candidate_residual = candidate-z-h*loop.field(0., (z+candidate)/2)
            if np.linalg.norm(candidate_residual, np.inf) < norm:
                y = candidate
                break
            scale *= .5
        else:
            raise RuntimeError(f'Newton line search failed at residual {norm:g}')
    raise RuntimeError(f'Newton failed at residual {norm:g}; tolerance {tolerance:g}')


def step(loop, z, h, method, *, diagnostics=True):
    if method == 'midpoint':
        return implicit_midpoint(loop, z, h)
    if method == 'weighted_midpoint':
        if loop.kind != 'proportional':
            raise ValueError('Weighted method requires constant proportional momentum damping')
        inner_loop = ClosedLoop(loop.model, 'conservative')
        weights = np.r_[np.ones(loop.n), np.full(loop.n, np.exp(-loop.gamma*h/2))]
        y, tangent, info = implicit_midpoint(inner_loop, weights*z, h)
        info['residual_coordinates'] = 'Centered canonical lift; p endpoint scaled by exp(+-gamma h/2)'
        return weights*y, weights[:, None]*tangent*weights[None, :], info
    if method == 'central4':
        if loop.kind != 'conservative':
            raise ValueError('Autonomous Hamiltonian Central4 is not applied to a dissipative feedback field')
        y, tangent, info = inherited_central4(loop.fixed, z, h, diagnostics=diagnostics)
        info['residual_coordinates'] = 'Full nonseparable central-generator increment'
        info['final_matrix_condition'] = info.get('ideal_implicit_matrix_condition', info['solver_matrix_condition'])
        info['final_matrix_min_singular'] = info.get('ideal_implicit_matrix_minimum_singular_value', info['solver_matrix_minimum_singular_value'])
        info['derivative'] = 'Inherited chord solve; exact residual; ideal generator tangent when sampled'
        return y, tangent, info
    raise ValueError(method)


def integrate(loop, z0, duration, h, method):
    count = round(duration/h)
    if abs(count*h-duration) > 1e-14:
        raise ValueError('duration must be an integer multiple of h')
    states = [np.asarray(z0, dtype=float).copy()]
    records = []
    for k in range(count):
        y, tangent, info = step(loop, states[-1], h, method, diagnostics=(k == 0))
        if tangent is not None:
            info['canonical_two_form_defect_2'] = float(np.linalg.norm(tangent.T@loop.K0@tangent-loop.K0, 2))
            info['weighted_two_form_defect_2'] = float(np.linalg.norm(tangent.T@loop.K0@tangent-np.exp(-loop.gamma*h)*loop.K0, 2))
        states.append(y)
        records.append(info)
    return np.asarray(states), records
