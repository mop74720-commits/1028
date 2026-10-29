#!/usr/bin/env python3
"""Reproduce a clamped Euler--Bernoulli beam with a distal rigid magnetic core.

This is a declared numerical benchmark, not an experimentally identified device.
All quantities are SI. The core centre of mass coincides with the beam endpoint.
The mass of coating/adhesive, fluid loads, shear deformation and distributed beam
rotary inertia are not included in this particular Euler--Bernoulli benchmark.

Run: python reproduce_baseline.py
Dependencies: numpy, scipy. No remote resources or manuscript edits are used.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.linalg import cholesky, eigh, solve_triangular
from scipy.optimize import brentq


MU0 = 4.0 * np.pi * 1e-7


@dataclass(frozen=True)
class Parameters:
    L_m: float = 0.08
    r_m: float = 0.0006
    E_Pa: float = 2.1e6
    rho_kg_m3: float = 1028.0
    magnet_side_m: float = 0.00025
    Br_T: float = 1.425
    magnet_rho_kg_m3: float = 7500.0
    B0_T: float = 0.03
    tip_mass_factor: float = 1.0
    # Only used for reproducing the prior example, whose moment was prescribed.
    mu_override_A_m2: float | None = None

    def properties(self) -> dict:
        A = np.pi * self.r_m**2
        I = np.pi * self.r_m**4 / 4.0
        volume = self.magnet_side_m**3
        mu = self.Br_T * volume / MU0
        if self.mu_override_A_m2 is not None:
            mu = self.mu_override_A_m2
        mass = self.magnet_rho_kg_m3 * volume * self.tip_mass_factor
        rotary = mass * self.magnet_side_m**2 / 6.0
        EI = self.E_Pa * I
        return {
            "A_m2": A,
            "I_m4": I,
            "EI_N_m2": EI,
            "beam_mass_kg": self.rho_kg_m3 * A * self.L_m,
            "magnet_volume_m3": volume,
            "mu_A_m2": mu,
            "tip_mass_kg": mass,
            "tip_rotary_inertia_kg_m2": rotary,
            "E0_J": mu * self.B0_T,
            "tip_rotational_stiffness_N_m": mu * self.B0_T,
            "dimensionless_tip_mass": mass / (self.rho_kg_m3 * A * self.L_m),
            "dimensionless_tip_rotary_inertia": rotary / (self.rho_kg_m3 * A * self.L_m**3),
            "dimensionless_tip_rotational_stiffness": mu * self.B0_T * self.L_m / EI,
            "Ec_at_4mm_J": 3.0 * EI * 0.004**2 / (2.0 * self.L_m**3),
        }


def assemble(p: Parameters, n_elements: int, include_tip_mass: bool = True,
             include_tip_rotary: bool = True, include_bias: bool = True):
    """Physical DOF order [w0, theta0, w1, theta1, ...]; theta = dw/dx."""
    z = p.properties()
    h = p.L_m / n_elements
    k = z["EI_N_m2"] / h**3 * np.array([
        [12, 6*h, -12, 6*h],
        [6*h, 4*h*h, -6*h, 2*h*h],
        [-12, -6*h, 12, -6*h],
        [6*h, 2*h*h, -6*h, 4*h*h],
    ], dtype=float)
    m = p.rho_kg_m3 * z["A_m2"] * h / 420.0 * np.array([
        [156, 22*h, 54, -13*h],
        [22*h, 4*h*h, 13*h, -3*h*h],
        [54, 13*h, 156, -22*h],
        [-13*h, -3*h*h, -22*h, 4*h*h],
    ], dtype=float)
    ndof = 2 * (n_elements + 1)
    Kbeam = np.zeros((ndof, ndof))
    Mbeam = np.zeros_like(Kbeam)
    for e in range(n_elements):
        ids = np.arange(2*e, 2*e+4)
        Kbeam[np.ix_(ids, ids)] += k
        Mbeam[np.ix_(ids, ids)] += m
    M = Mbeam.copy()
    if include_tip_mass:
        M[-2, -2] += z["tip_mass_kg"]
    if include_tip_rotary:
        M[-1, -1] += z["tip_rotary_inertia_kg_m2"]
    K = Kbeam.copy()
    if include_bias:
        K[-1, -1] += z["E0_J"]
    # Enforce the clamp by eliminating w0 and theta0.
    return K[2:, 2:], M[2:, 2:], Kbeam[2:, 2:], Mbeam[2:, 2:]


def modes(p: Parameters, n_elements: int, **options) -> dict:
    K, M, Kbeam, Mbeam = assemble(p, n_elements, **options)
    # Scale displacement relative to L before factoring, then solve the inverse
    # symmetric problem. Its largest eigenvalues give the lowest frequencies,
    # avoiding subtraction of small eigenvalues from a very large spectral end.
    scale = np.tile([p.L_m, 1.0], n_elements)
    Ks = scale[:, None] * K * scale[None, :]
    Ms = scale[:, None] * M * scale[None, :]
    Lk = cholesky(Ks, lower=True)
    temp = solve_triangular(Lk, Ms, lower=True)
    C = solve_triangular(Lk, temp.T, lower=True).T
    C = (C + C.T) / 2.0
    inverse_values, vectors = eigh(C, subset_by_index=[C.shape[0]-4, C.shape[0]-1],
                                    driver="evr")
    order = np.argsort(inverse_values)[::-1]
    inverse_values = inverse_values[order]
    vectors = vectors[:, order]
    transformed = solve_triangular(Lk.T, vectors, lower=False)
    Phi = scale[:, None] * transformed / np.sqrt(inverse_values)[None, :]
    # Eigensolver already M-normalizes; explicitly remove rounding in the norm.
    Phi /= np.sqrt(np.diag(Phi.T @ M @ Phi))[None, :]
    for j in range(Phi.shape[1]):
        if Phi[-2, j] < 0:
            Phi[:, j] *= -1.0
    values = np.array([float(Phi[:, j] @ K @ Phi[:, j]) for j in range(4)])
    omega = np.sqrt(values)
    Mgram = Phi.T @ M @ Phi
    Kgram = Phi.T @ K @ Phi
    residuals = [np.linalg.norm(K @ Phi[:, j] - omega[j]**2 * M @ Phi[:, j]) /
                 (np.linalg.norm(K @ Phi[:, j]) + omega[j]**2*np.linalg.norm(M @ Phi[:, j]))
                 for j in range(4)]
    return {"n_elements": n_elements, "omega": omega, "Phi": Phi,
            "M": M, "K": K, "Kbeam": Kbeam, "Mbeam": Mbeam,
            "mass_orthonormality_max_error": float(np.max(np.abs(Mgram-np.eye(4)))),
            "stiffness_orthogonality_relative_error": float(np.max(np.abs(
                Kgram / (omega[:, None]*omega[None, :]) - np.eye(4)))),
            "eigen_equation_relative_residuals": residuals}


def exact_boundary_frequencies(p: Parameters, n_modes: int = 4,
                               include_tip_mass: bool = True,
                               include_tip_rotary: bool = True,
                               include_bias: bool = True) -> dict:
    """Independent continuum root check for the same ideal endpoint model.

    EI*w'''' = rho*A*omega^2*w, with w(0)=w'(0)=0,
    EI*w'''(L)+m*omega^2*w(L)=0,
    EI*w''(L)+(mu*B0-J*omega^2)*w'(L)=0.
    Use w=a(cosh(kx)-cos(kx))+b(sinh(kx)-sin(kx)).
    """
    z = p.properties()
    eta = z["dimensionless_tip_mass"] if include_tip_mass else 0.0
    iota = z["dimensionless_tip_rotary_inertia"] if include_tip_rotary else 0.0
    kappa = z["dimensionless_tip_rotational_stiffness"] if include_bias else 0.0

    def determinant(lam):
        sh, ch, si, co = np.sinh(lam), np.cosh(lam), np.sin(lam), np.cos(lam)
        f, g, cp, sp = ch-co, sh-si, ch+co, sh+si
        h = kappa/lam - iota*lam**3
        return (g+eta*lam*f)*(sp+h*f) - (cp+eta*lam*g)*(cp+h*sp)

    roots = []
    xprev, yprev = 0.1, determinant(0.1)
    for x in np.arange(0.11, 20.0, 0.01):
        y = determinant(x)
        if y*yprev < 0:
            r = brentq(determinant, xprev, x, xtol=2e-13)
            if not roots or abs(r-roots[-1]) > 1e-5:
                roots.append(r)
            if len(roots) == n_modes:
                break
        xprev, yprev = x, y
    if len(roots) != n_modes:
        raise RuntimeError("Could not bracket the requested continuum modes")
    omega = np.array(roots)**2 * np.sqrt(z["EI_N_m2"] /
                (p.rho_kg_m3*z["A_m2"]*p.L_m**4))
    return {"lambda": roots, "omega_rad_s": omega.tolist()}


def reduce(p: Parameters, solution: dict) -> dict:
    z = p.properties()
    omega = solution["omega"][:2]
    omega0 = float(omega[0])
    nu = omega/omega0
    Ds = np.sqrt(z["E0_J"]/(omega0*omega))
    Phi = solution["Phi"][:, :2]
    b = Phi[-2, :]
    t = Phi[-1, :]
    d = t*Ds
    ell = b*Ds
    AMAG = np.column_stack((b, t))
    AMAG_columns = AMAG/np.linalg.norm(AMAG, axis=0)
    return {
        "omega_rad_s": omega.tolist(), "omega0_rad_s": omega0,
        "frequency_Hz": (omega/(2*np.pi)).tolist(), "nu": nu.tolist(),
        "Ds": Ds.tolist(), "Ds_units": "sqrt(kg) m",
        "d": d.tolist(), "ell_m": ell.tolist(),
        "tip_displacement_mass_normalized": b.tolist(),
        "tip_slope_mass_normalized": t.tolist(),
        "E0_J": z["E0_J"], "mu_A_m2": z["mu_A_m2"], "B0_T": p.B0_T,
        "alpha_s_inv": .05*omega0, "gamma": .05,
        "zeta": (.025/nu).tolist(),
        "damping_statement": "Declared C=alpha*Mtotal, alpha=0.05*omega0; not measured damping. alpha is a damping force coefficient, while amplitude decay rate is alpha/2.",
        "dimensionless_mass_matrix": np.diag(1/nu).tolist(),
        "AMAG": AMAG.tolist(),
        "AMAG_determinant": float(np.linalg.det(AMAG)),
        "AMAG_column_normalized_condition_number": float(np.linalg.cond(AMAG_columns)),
        "Lambda_generalized_force_scale": (z["E0_J"]/Ds).tolist(),
        "tip_angle_mapping": "theta_tip = dot(d, X)",
        "tip_displacement_mapping": "w_tip = dot(ell_m, X)",
        "physical_modal_coordinates": "a=diag(Ds)*X; pi_j=sqrt(E0*omega_j/omega0)*Y_j",
        "physical_generalized_force_relation": "AMAG @ [F_y, tau_z] = diag(E0/Ds) @ U",
    }


def sample_modes(p: Parameters, solution: dict, reduced: dict,
                 subdivisions: int = 8) -> dict:
    ne = solution["n_elements"]
    h = p.L_m/ne
    physical = np.vstack((np.zeros((2, 2)), solution["Phi"][:, :2]))
    balanced = physical*np.asarray(reduced["Ds"])[None, :]
    xs, ell, slopes = [], [], []
    for i in range(ne*subdivisions+1):
        e = min(i//subdivisions, ne-1)
        xi = (i-e*subdivisions)/subdivisions
        N = np.array([1-3*xi**2+2*xi**3, h*(xi-2*xi**2+xi**3),
                      3*xi**2-2*xi**3, h*(-xi**2+xi**3)])
        Nx = np.array([(-6*xi+6*xi**2)/h, 1-4*xi+3*xi**2,
                       (6*xi-6*xi**2)/h, -2*xi+3*xi**2])
        local = balanced[2*e:2*e+4]
        xs.append(i*h/subdivisions)
        ell.append((N@local).tolist())
        slopes.append((Nx@local).tolist())
    return {"x_m": xs, "ell_x_m": ell, "d_x": slopes,
            "element_length_m": h,
            "nodal_balanced_shapes_w_theta": balanced.tolist(),
            "sampling_note": "Eight equal subdivisions per Hermite element; exact Hermite interpolation. d_x is the physical slope dw/dx, and terminal d_x equals reduced.d.",
            "exact_slope_extrema_note": "At any X, each element slope is quadratic in local xi. Evaluate both endpoints and any interior zero of its xi derivative for an exact spatial maximum; the nodal balanced shapes are supplied for this purpose."}


def plain_solution(solution: dict) -> dict:
    return {key: (value.tolist() if isinstance(value, np.ndarray) else value)
            for key, value in solution.items()
            if key not in {"Phi", "M", "K", "Kbeam", "Mbeam"}}


def main() -> None:
    p = Parameters()
    props = p.properties()
    computed = {ne: modes(p, ne) for ne in [16, 32, 64]}
    base = computed[32]
    reduced = reduce(p, base)
    exact = exact_boundary_frequencies(p)
    exact_w = np.array(exact["omega_rad_s"])
    convergence = []
    for ne, solution in computed.items():
        row = plain_solution(solution)
        row["relative_error_vs_continuum"] = (solution["omega"]/exact_w-1).tolist()
        row["relative_difference_vs_64_elements"] = (solution["omega"]/computed[64]["omega"]-1).tolist()
        convergence.append(row)

    # Reproduce the original numerical example (no attached end inertia).
    old = Parameters(E_Pa=5e6, rho_kg_m3=1100.0,
                     tip_mass_factor=0.0, mu_override_A_m2=2e-5)
    oldsol = modes(old, 32)
    oldred = reduce(old, oldsol)
    # The legacy damping convention predates the new biased-frequency convention.
    # Preserve its upstream alpha; the self-check below concerns FE modes only.
    oldalpha = 0.5555852368222173
    oldred["alpha_s_inv"] = oldalpha
    oldred["gamma"] = oldalpha / oldred["omega0_rad_s"]
    oldred["zeta"] = (oldalpha / (2.0 * oldsol["omega"][:2])).tolist()
    oldred["damping_statement"] = (
        "Legacy upstream alpha=0.5555852368222173 s^-1 is based on the unbiased "
        "beam frequency, not the new alpha=0.05*biased_omega1 convention. "
        "gamma=alpha/biased_omega1 and zeta_j=alpha/(2*biased_omega_j). "
        "The legacy reproduction self-check verifies FE modal quantities only; "
        "it does not claim reproduction of legacy damping under the new convention."
    )
    oldref = {"omega0_rad_s": 11.417287283,
              "nu": [1.0, 6.15211751],
              "d": [0.225670773, 0.321798806],
              "ell_m": [0.01350605377, 0.00547092647]}
    legacy_error = {key: float(np.max(np.abs(np.atleast_1d(oldred[key]) /
                          np.atleast_1d(value)-1))) for key, value in oldref.items()}

    variants = {
        "beam_only_no_bias_no_tip": {"include_tip_mass": False, "include_tip_rotary": False, "include_bias": False},
        "biased_beam_without_tip_inertia": {"include_tip_mass": False, "include_tip_rotary": False},
        "biased_beam_with_tip_translation_only": {"include_tip_mass": True, "include_tip_rotary": False},
        "biased_beam_with_full_tip_inertia": {},
    }
    effects = {}
    for name, options in variants.items():
        sol = modes(p, 32, **options)
        effects[name] = {"omega_rad_s": sol["omega"].tolist()}
    no_tip = np.array(effects["biased_beam_without_tip_inertia"]["omega_rad_s"])
    effects["tip_inertia_change_relative_to_biased_massless_tip"] = (base["omega"]/no_tip-1).tolist()

    specifications = [
        ("Br_lower_1p40_T", replace(p, Br_T=1.40), "Stated N50 grade interval endpoint; not a hardware measurement uncertainty."),
        ("Br_upper_1p45_T", replace(p, Br_T=1.45), "Stated N50 grade interval endpoint; not a hardware measurement uncertainty."),
        ("tip_inertia_minus10pct", replace(p, tip_mass_factor=.9), "Declared design sensitivity; m and J both scaled at fixed a; mu fixed."),
        ("tip_inertia_plus10pct", replace(p, tip_mass_factor=1.1), "Declared design sensitivity; m and J both scaled at fixed a; mu fixed."),
        ("E_minus20pct", replace(p, E_Pa=.8*p.E_Pa), "Declared design sensitivity; not a measured confidence interval."),
        ("E_plus20pct", replace(p, E_Pa=1.2*p.E_Pa), "Declared design sensitivity; not a measured confidence interval."),
    ]
    for Br in [1.40, 1.45]:
        for factor in [.9, 1.1]:
            specifications.append((f"Br_{Br:.2f}_tip_factor_{factor:.1f}",
                                   replace(p, Br_T=Br, tip_mass_factor=factor),
                                   "Combined design corner; no probability or confidence interpretation."))
    sensitivity = []
    for name, varied, label in specifications:
        sol = modes(varied, 32)
        red = reduce(varied, sol)
        sensitivity.append({"case": name, "interpretation": label,
            "parameters": asdict(varied), "omega_rad_s": sol["omega"].tolist(),
            "relative_omega_change_from_nominal": (sol["omega"]/base["omega"]-1).tolist(),
            "mu_A_m2": varied.properties()["mu_A_m2"],
            "tip_mass_kg": varied.properties()["tip_mass_kg"],
            "tip_rotary_inertia_kg_m2": varied.properties()["tip_rotary_inertia_kg_m2"],
            "nu": red["nu"], "d": red["d"], "ell_m": red["ell_m"],
            "zeta1_with_nominal_alpha_held_fixed": reduced["alpha_s_inv"]/(2*red["omega0_rad_s"]),
            "alpha_note": "Nominal alpha held fixed for this reported damping ratio; no re-identification claimed."})

    sampled = sample_modes(p, base, reduced)
    # Independent checks target exactly the possible discretization/scaling mistakes.
    assert max(legacy_error.values()) < 2e-7, legacy_error
    assert base["mass_orthonormality_max_error"] < 1e-10
    assert base["stiffness_orthogonality_relative_error"] < 1e-7
    assert max(abs(base["omega"]/exact_w-1)) < 1.1e-5
    assert np.allclose(sampled["ell_x_m"][-1], reduced["ell_m"], rtol=1e-13)
    assert np.allclose(sampled["d_x"][-1], reduced["d"], rtol=1e-13)
    assert reduced["AMAG_column_normalized_condition_number"] < 20
    assert np.all(base["Phi"][-2, :] > 0)

    result = {
        "schema_version": 1,
        "scope": "Declared planar small-slope, clamped-free, no-contact Euler--Bernoulli benchmark with an idealized distal rigid cube. Not a reproduction of Tong or Francescon hardware.",
        "parameter_provenance_note": "Inputs specified by the parent source audit. Numerical reproducibility does not establish literature provenance; use the associated source register for attribution.",
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "parameters": asdict(p),
        "properties": props,
        "model_assumptions": [
            "Uniform circular beam; root displacement and slope fixed; no prescribed tip displacement or slope.",
            "Core centre of mass at beam endpoint; therefore no translation-rotation mass coupling or eccentricity term.",
            "Uniform-density cubic core J=m*a^2/6 about an in-plane bending axis through its centre.",
            "No coating, adhesive or fixture mass. Their omission is an idealization, not a zero measured mass.",
            "Permanent magnetic dipole mu=Br*a^3/mu0, body-fixed along tangent; use nominal grade midpoint.",
            "Bias field B0 is along the straight equilibrium tangent; Kbias=Kbeam+mu*B0*e_theta*e_theta^T.",
            "Consistent Hermite beam mass plus endpoint translational mass and rotary inertia.",
            "Declared mass-proportional damping C=alpha*Mtotal, alpha=0.05*omega1 of the biased beam including tip inertia.",
            "E plus/minus20% and tip inertia plus/minus10% are chosen design perturbations, not calibrated hardware uncertainty intervals.",
        ],
        "reduced": reduced,
        "sampled_modes": sampled,
        "finite_element_convergence": convergence,
        "independent_continuum_boundary_check": exact,
        "legacy_reproduction": {"computed": oldred, "reference_rounded": oldref,
                                "max_relative_errors": legacy_error},
        "tip_mass_and_bias_effects": effects,
        "design_sensitivity": sensitivity,
        "energy_scale_note": (
            "Ec=3*EI*c^2/(2*L^3), c=4 mm. For every admissible clamped beam "
            "displacement w with w(0)=w'(0)=0, Cauchy-Schwarz gives "
            "||w||_infinity^2 <= 2*L^3*E_bend/(3*EI), where "
            "E_bend=(EI/2)*integral_0^L (w'')^2 dx. Thus, if the total physical "
            "energy is a sum of nonnegative terms including E_bend and is "
            "bounded by 0.95*Ec, the entire centreline satisfies "
            "||w||_infinity <= sqrt(0.95)*c < c. The present computation does "
            "not prove that a driven or controlled trajectory stays below this "
            "energy cap, so Ec alone is not a closed-loop displacement guarantee."
        ),
    }
    dest = Path(__file__).resolve().parent / "new_baseline.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": str(dest), "properties": props, "reduced": reduced,
                      "convergence": convergence, "legacy_error": legacy_error,
                      "tip_effects": effects}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
