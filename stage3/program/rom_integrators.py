"""Implicit methods for the actual nonseparable 12-coordinate rod Hamiltonian.

No mass freezing is used in any residual.  The Central4 chord matrix is only a
nonlinear-solver preconditioner; the solved residual is the full AD scalar
generating-function residual.  Tangents describe the ideal implicit map.
"""
from __future__ import annotations
import time
import numpy as np
import torch

TOLERANCE = 2e-13


def central_scalar(model, z, h):
    """S_h = h H + h^3/24 f^T H'' f, evaluated without an explicit AD3 tensor."""
    H = model.hamiltonian_tensor(z)
    grad = torch.autograd.grad(H, z, create_graph=True)[0]
    J = torch.as_tensor(model.J, dtype=z.dtype, device=z.device)
    f = J @ grad
    Hf = torch.autograd.grad(grad, z, grad_outputs=f, create_graph=True)[0]
    return h * H + h**3 / 24 * torch.dot(f, Hf)


def central_increment_tensor(model, z, h, create_graph=False):
    S = central_scalar(model, z, h)
    g = torch.autograd.grad(S, z, create_graph=create_graph)[0]
    return torch.as_tensor(model.J, dtype=z.dtype, device=z.device) @ g


def central_increment(model, z, h):
    x = torch.tensor(z, dtype=torch.float64, requires_grad=True)
    return central_increment_tensor(model, x, h).detach().numpy()


def central_increment_jacobian(model, z, h):
    x = torch.tensor(z, dtype=torch.float64, requires_grad=True)
    return torch.autograd.functional.jacobian(
        lambda y: central_increment_tensor(model, y, h, create_graph=True),
        x, vectorize=True).detach().numpy()


def solve_chord(residual, initial, matrix, tolerance=TOLERANCE, max_iterations=20):
    """Fixed matrix Newton iteration; termination always uses the true residual."""
    from scipy.linalg import lu_factor, lu_solve
    factor = lu_factor(matrix)
    x = np.asarray(initial, dtype=float).copy()
    for iteration in range(max_iterations + 1):
        r = residual(x)
        norm = float(np.linalg.norm(r, np.inf))
        if not np.isfinite(norm):
            raise FloatingPointError('Nonfinite implicit increment residual')
        if norm <= tolerance:
            return x, dict(increment_residual_inf=norm,
                           nonlinear_corrections=iteration,
                           solver_matrix_condition=float(np.linalg.cond(matrix)),
                           solver_matrix_minimum_singular_value=float(np.linalg.svd(matrix, compute_uv=False)[-1]))
        x -= lu_solve(factor, r)
    raise RuntimeError(f'Chord solver failed: residual={norm:g}, tolerance={tolerance:g}')


def midpoint(model, z, h, gamma=0., diagnostics=False):
    before = time.perf_counter()
    f0 = model.field(z, gamma=gamma)
    A = model.jacobian(z, gamma=gamma)
    eye = np.eye(len(z))
    matrix = eye - .5*h*A
    result, stats = solve_chord(
        lambda y: y-z-h*model.field((z+y)/2, gamma=gamma), z+h*f0, matrix)
    tangent = None
    if diagnostics:
        B = .5*h*model.jacobian((z+result)/2, gamma=gamma)
        tangent = np.linalg.solve(eye-B, eye+B)
        stats['ideal_implicit_matrix_condition'] = float(np.linalg.cond(eye-B))
        stats['ideal_implicit_matrix_minimum_singular_value'] = float(np.linalg.svd(eye-B, compute_uv=False)[-1])
    stats['seconds'] = time.perf_counter()-before
    return result, tangent, stats


def weighted_midpoint(model, z, h, gamma, diagnostics=False):
    """S_(h/2) MP_H S_(h/2), with S(q,p)=(q,exp(-gamma*h/2)p).

    Uniform canonical momentum drag -gamma*p is essential.  In the centered
    time-dependent chart Pi=exp(gamma*t)*p this is canonical midpoint. It
    remains valid for the actual q-dependent mass and full nonseparable H.
    It must not be used to assign a conformal structure to general fluid drag.
    """
    diagonal = np.r_[np.ones(model.n), np.full(model.n, np.exp(-gamma*h/2))]
    inner, tangent, stats = midpoint(model, diagonal*z, h, diagnostics=diagnostics)
    if tangent is not None:
        tangent = diagonal[:, None]*tangent*diagonal[None, :]
    return diagonal*inner, tangent, stats


def central4(model, z, h, diagnostics=False):
    before = time.perf_counter()
    A = model.jacobian(z)
    eye = np.eye(len(z))
    # Exact for a quadratic H; a chord preconditioner for the real nonlinear H.
    preconditioner = eye - .5*(h*A-h**3*(A@A@A)/12)
    increment = lambda y: central_increment(model, y, h)
    result, stats = solve_chord(lambda y: y-z-increment((z+y)/2),
                               z+increment(z), preconditioner)
    tangent = None
    if diagnostics:
        B = central_increment_jacobian(model, (z+result)/2, h)/2
        tangent = np.linalg.solve(eye-B, eye+B)
        stats['ideal_implicit_matrix_condition'] = float(np.linalg.cond(eye-B))
        stats['ideal_implicit_matrix_minimum_singular_value'] = float(np.linalg.svd(eye-B, compute_uv=False)[-1])
        stats['increment_Hamiltonian_Jacobian_defect'] = float(np.linalg.norm(B.T@model.K0+model.K0@B, 2))
    stats['seconds'] = time.perf_counter()-before
    return result, tangent, stats


def integrate(model, z0, T, h, method, gamma=0., diagnose_first=True):
    count = round(T/h)
    if abs(count*h-T) > 1e-14:
        raise ValueError('T must be an integer multiple of h')
    if method == 'central4' and gamma != 0:
        raise ValueError('Autonomous conservative Central4 cannot be used with damping')
    states = [np.asarray(z0, dtype=float).copy()]
    records = []
    start = time.perf_counter()
    for k in range(count):
        diagnostic = diagnose_first and k == 0
        if method == 'midpoint':
            new, tangent, stats = midpoint(model, states[-1], h, gamma, diagnostic)
        elif method == 'weighted_midpoint':
            new, tangent, stats = weighted_midpoint(model, states[-1], h, gamma, diagnostic)
        elif method == 'central4':
            new, tangent, stats = central4(model, states[-1], h, diagnostic)
        else:
            raise ValueError(method)
        if tangent is not None:
            stats['standard_two_form_defect_spectral2'] = float(np.linalg.norm(tangent.T@model.K0@tangent-model.K0, 2))
            stats['conformal_two_form_defect_spectral2'] = float(np.linalg.norm(tangent.T@model.K0@tangent-np.exp(-gamma*h)*model.K0, 2))
        states.append(new)
        records.append(stats)
    elapsed = time.perf_counter()-start
    return np.asarray(states), dict(seconds=elapsed, steps=count,
        max_increment_residual_inf=max(s['increment_residual_inf'] for s in records),
        total_nonlinear_corrections=sum(s['nonlinear_corrections'] for s in records),
        max_solver_matrix_condition=max(s['solver_matrix_condition'] for s in records),
        minimum_solver_matrix_singular_value=min(s['solver_matrix_minimum_singular_value'] for s in records),
        first_step_diagnostics=records[0],
        structure_sampling='first step only; ideal implicit tangent, not differentiated finite iteration')
