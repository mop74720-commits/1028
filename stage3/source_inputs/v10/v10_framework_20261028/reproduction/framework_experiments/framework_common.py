"""Shared, explicitly scoped numerical tools for the three framework questions.

The declared beam baseline is read from this source package. Existing control
records are not overwritten. No hardware, full-network or KAM certification
is performed by these routines.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import sys

import numpy as np
import scipy
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parent
REP = ROOT.parent
BASELINE_PATH = REP / "new_baseline.json"
BASELINE = json.loads(BASELINE_PATH.read_text())
R = BASELINE["reduced"]
NU = np.asarray(R["nu"], dtype=float)
N = np.diag(NU)
D = np.asarray(R["d"], dtype=float)
J = np.block([[np.zeros((2, 2)), np.eye(2)], [-np.eye(2), np.zeros((2, 2))]])
INITIAL = np.array([.09, .08, .015, -.01])

# Reuse the actual force/torque -> field/gradient -> force reconstruction.
# Importing this module does not execute its guarded main().
sys.path.insert(0, str(REP / "experiments"))
spec = importlib.util.spec_from_file_location("framework_original_control", REP / "experiments" / "minimal_control_loop.py")
CONTROL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CONTROL)
assert np.array_equal(CONTROL.NU, NU) and np.array_equal(CONTROL.D, D)


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_result(name, result):
    result["provenance"] = {
        "baseline_file": "../new_baseline.json",
        "baseline_sha256": hashlib.sha256(BASELINE_PATH.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256((ROOT / "run_all.py").read_bytes()).hexdigest(),
        "common_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "scope": "Synthetic numerical verification on the declared model; no interval, hardware or full-network certificate.",
    }
    (ROOT / name).write_text(json.dumps(clean(result), ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def potential_terms(z, kappa=1.):
    s = D @ z[:2]
    u = NU*z[:2] + kappa*(np.sin(s)-s)*D
    a = N + kappa*(np.cos(s)-1)*np.outer(D, D)
    return s, u, a


def model_field(z, delta_beta=0., delta_gamma=0.):
    _, u, _ = potential_terms(z, 1+delta_beta)
    return np.r_[NU*z[2:], -u-delta_gamma*z[2:]]


def model_jacobian(z, delta_beta=0., delta_gamma=0.):
    _, _, a = potential_terms(z, 1+delta_beta)
    return np.block([[np.zeros((2, 2)), N], [-a, -delta_gamma*np.eye(2)]])


def central4_increment(z, step, kappa=1.):
    s, u, a = potential_terms(z, kappa)
    v = NU*z[2:]
    b = D @ v
    correction = np.r_[2*N@a@v, kappa*np.sin(s)*b*b*D-2*a@N@u]
    return step*np.r_[v, -u] + step**3/24*correction


def central4_increment_jacobian(z, step, kappa=1.):
    s, u, a = potential_terms(z, kappa)
    v = NU*z[2:]
    b = D @ v
    nd, dd = N@D, np.outer(D, D)
    qx = -2*kappa*np.sin(s)*b*np.outer(nd, D)
    qy = 2*N@a@N
    px = kappa*(np.cos(s)*b*b+2*np.sin(s)*(D@N@u))*dd-2*a@N@a
    py = 2*kappa*np.sin(s)*b*np.outer(D, nd)
    base = np.block([[np.zeros((2, 2)), N], [-a, np.zeros((2, 2))]])
    return step*base + step**3/24*np.block([[qx, qy], [px, py]])


def implicit_increment(old, increment, derivative, tolerance=2e-14, max_corrections=12):
    new = old + increment(old)
    identity = np.eye(len(old))
    for corrections in range(max_corrections+1):
        mid = (old+new)/2
        residual = new-old-increment(mid)
        residual_norm = float(np.linalg.norm(residual, np.inf))
        if residual_norm <= tolerance:
            tangent_half = derivative(mid)/2
            tangent = np.linalg.solve(identity-tangent_half, identity+tangent_half)
            return new, mid, tangent, residual_norm, corrections
        if corrections == max_corrections:
            raise RuntimeError("Framework implicit solve did not reach its increment-residual tolerance")
        new -= np.linalg.solve(identity-derivative(mid)/2, residual)
    raise AssertionError("Unreachable")


def integrate(field, jacobian, initial, duration, step, method="midpoint", gamma=0., kappa=1.):
    count = int(round(duration/step))
    assert abs(count*step-duration) < 1e-12
    states = np.empty((count+1, len(initial)))
    states[0] = initial
    residuals, iterations, standard_defects, weighted_defects = [], [], [], []
    minimum_newton_sigma = np.inf
    scale = np.diag(np.r_[np.ones(2), np.full(2, np.exp(-gamma*step/2))])
    for k in range(count):
        old = states[k]
        if method == "weighted_midpoint":
            internal_old = scale@old
            inc = lambda z: step*model_field(z, kappa-1, 0.)
            der = lambda z: step*model_jacobian(z, kappa-1, 0.)
            internal_new, mid, tangent, residual, corrections = implicit_increment(internal_old, inc, der)
            new = scale@internal_new
            tangent = scale@tangent@scale
            rr = np.exp(gamma*step/2)
            actual_residual = np.r_[
                new[:2]-old[:2]-step/2*NU*(rr*new[2:]+old[2:]/rr),
                rr*new[2:]-old[2:]/rr+step*potential_terms((old+new)/2, kappa)[1],
            ]
            assert np.linalg.norm(actual_residual, np.inf) < 5e-13
        else:
            if method == "central4":
                assert gamma == 0., "Central4 is used here only for the conservative branch"
                inc = lambda z: central4_increment(z, step, kappa)
                der = lambda z: central4_increment_jacobian(z, step, kappa)
            else:
                inc = lambda z: step*field(z)
                der = lambda z: step*jacobian(z)
            new, mid, tangent, residual, corrections = implicit_increment(old, inc, der)
            actual_residual = new-old-inc(mid)
        states[k+1] = new
        residuals.append(float(np.linalg.norm(actual_residual, np.inf)))
        iterations.append(corrections)
        standard_defects.append(float(np.linalg.norm(tangent.T@J@tangent-J, 2)))
        weighted_defects.append(float(np.linalg.norm(tangent.T@J@tangent-np.exp(-gamma*step)*J, 2)))
        minimum_newton_sigma = min(minimum_newton_sigma, float(np.linalg.svd(np.eye(4)-der(mid)/2, compute_uv=False)[-1]))
    return states, {
        "maximum_increment_residual_inf": max(residuals),
        "maximum_Newton_corrections": max(iterations),
        "failed_steps": 0,
        "minimum_Newton_matrix_singular_value": minimum_newton_sigma,
        "maximum_ideal_standard_symplectic_defect_spectral2": max(standard_defects),
        "maximum_ideal_exponential_weighted_defect_spectral2": max(weighted_defects),
        "structure_diagnostic_scope": "Implicit ideal tangent evaluated at numerical solution points, not the derivative of a finite floating-point Newton program.",
    }


def independent_references(field, initial, duration):
    options = [dict(rtol=1e-11, atol=1e-13, max_step=.05), dict(rtol=2e-13, atol=2e-15, max_step=.025)]
    solutions = [solve_ivp(lambda t, z: field(z), (0., duration), initial, method="DOP853", dense_output=True, **opt) for opt in options]
    assert all(s.success for s in solutions)
    return solutions, {"method": "Independent explicit DOP853 with dense output", "coarse": options[0], "fine": options[1], "interval_validation": False}


def errors_and_order(states, reference, step, previous=None):
    errors = np.linalg.norm(states-reference, axis=1)
    maximum = float(np.max(errors))
    return {
        "step": step,
        "maximum_state_error": maximum,
        "endpoint_state_error": float(errors[-1]),
        "RMS_state_error": float(np.sqrt(np.mean(errors**2))),
        "observed_order": None if previous is None else float(np.log(previous["maximum_state_error"]/maximum)/np.log(previous["step"]/step)),
    }
