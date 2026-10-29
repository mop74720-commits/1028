"""Run small, separately recorded P1/P3 framework verification experiments.

Usage: python reproduction/framework_experiments/run_all.py
       python reproduction/framework_experiments/run_all.py --experiment matrix
No existing baseline, training or control record is overwritten.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from framework_common import (
    ROOT, REP, R, NU, N, D, J, INITIAL, CONTROL, write_result,
    model_field, model_jacobian, central4_increment, central4_increment_jacobian,
    integrate, independent_references, errors_and_order,
)


def matrix_midpoint(a, step):
    identity = np.eye(len(a))
    return np.linalg.solve(identity-step*a/2, identity+step*a/2)


def matrix_central4(a, step):
    inc = step*a-step**3*(a@a@a)/12
    identity = np.eye(len(a))
    return np.linalg.solve(identity-inc/2, identity+inc/2)


def matrix_experiment():
    steps = [.08, .04, .02, .01]
    duration, gamma = 4., .2
    initials = {1: [.1, 0.], 2: [.1, .06, 0., .02], 4: [.1, .06, .04, .025, 0., .02, -.01, .005]}
    cases = []
    for n in [1, 2, 4]:
        m = np.diag(1+np.arange(n)/5)+.12*np.ones((n, n))
        k = np.diag(1+np.arange(n))+.05*np.ones((n, n))
        c = gamma*m
        mi, eye, zero = np.linalg.solve(m, np.eye(n)), np.eye(n), np.zeros((n, n))
        j = np.block([[zero, eye], [-eye, zero]])
        ks = np.diag(.05*(1+np.arange(n)))
        a0 = np.block([[zero, mi], [-k, zero]])
        ad = np.block([[zero, mi], [-k, -c@mi]])
        ac = np.block([[zero, mi], [-(k+ks), zero]])
        initial = np.asarray(initials[n])
        fine_times = np.arange(401)*.01
        damped_exact = np.array([expm(t*ad)@initial for t in fine_times])
        conservative_exact = np.array([expm(t*ac)@initial for t in fine_times])
        groups = {name: [] for name in ["ordinary_midpoint", "weighted_midpoint", "conservative_midpoint", "conservative_central4"]}
        equivalence = []
        for step in steps:
            count = round(duration/step)
            ordinary = matrix_midpoint(ad, step)
            scale = np.diag(np.r_[np.ones(n), np.full(n, np.exp(-gamma*step/2))])
            weighted = scale@matrix_midpoint(a0, step)@scale
            e = step**2/4*k@mi+step/2*c@mi
            direct, eliminated = initial.copy(), initial.copy()
            max_equivalence = 0.
            for _ in range(count):
                q, p = eliminated[:n], eliminated[n:]
                new_p = np.linalg.solve(eye+e, (eye-e)@p-step*k@q)
                eliminated = np.r_[q+step/2*mi@(p+new_p), new_p]
                direct = ordinary@direct
                max_equivalence = max(max_equivalence, float(np.linalg.norm(direct-eliminated)))
            assert max_equivalence < 1e-12
            equivalence.append({"step": step, "maximum_trajectory_equivalence_error": max_equivalence,
                                "minimum_singular_I_plus_E": float(np.linalg.svd(eye+e, compute_uv=False)[-1])})
            for name, update, exact in [
                ("ordinary_midpoint", ordinary, damped_exact),
                ("weighted_midpoint", weighted, damped_exact),
                ("conservative_midpoint", matrix_midpoint(ac, step), conservative_exact),
                ("conservative_central4", matrix_central4(ac, step), conservative_exact),
            ]:
                states = np.empty((count+1, 2*n)); states[0] = initial
                for it in range(count):
                    states[it+1] = update@states[it]
                row = errors_and_order(states, exact[::round(step/.01)], step, groups[name][-1] if groups[name] else None)
                row["standard_symplectic_defect_spectral2"] = float(np.linalg.norm(update.T@j@update-j, 2))
                row["exponential_weighted_defect_spectral2"] = float(np.linalg.norm(update.T@j@update-np.exp(-gamma*step)*j, 2))
                groups[name].append(row)
            assert groups["weighted_midpoint"][-1]["exponential_weighted_defect_spectral2"] < 1e-12
            assert max(groups[name][-1]["standard_symplectic_defect_spectral2"] for name in ["conservative_midpoint", "conservative_central4"]) < 1e-12
        for name, rows in groups.items():
            assert abs(rows[-1]["observed_order"]-(4 if name.endswith("central4") else 2)) < .1

        # A second algebraic case checks the CM^{-1} ordering too. For n=2,4
        # C is nonproportional; n=1 is necessarily a scalar comparison. No
        # common exponential-weighted claim is assigned to this extra family.
        vv = np.arange(1, n+1, dtype=float)
        c_general = c+.03*np.outer(vv, vv)/(vv@vv)
        ag = np.block([[zero, mi], [-k, -c_general@mi]])
        general_rows = []
        for step in steps:
            e = step**2/4*k@mi+step/2*c_general@mi
            direct, eliminated = initial.copy(), initial.copy()
            maximum = 0.
            update = matrix_midpoint(ag, step)
            for _ in range(round(duration/step)):
                q, p = eliminated[:n], eliminated[n:]
                pp = np.linalg.solve(eye+e, (eye-e)@p-step*k@q)
                eliminated = np.r_[q+step/2*mi@(p+pp), pp]
                direct = update@direct
                maximum = max(maximum, float(np.linalg.norm(direct-eliminated)))
            assert maximum < 1e-12
            general_rows.append({"step": step, "maximum_trajectory_equivalence_error": maximum})
        cases.append({"n": n, "M": m, "K": k, "C_proportional": c, "Ks": ks, "initial_state": initial,
                      "commutator_MK_spectral2": np.linalg.norm(m@k-k@m, 2),
                      "equivalence": equivalence, "methods": groups,
                      "general_drag_algebra_only": {"C": c_general, "commutator_MC_spectral2": np.linalg.norm(m@c_general-c_general@m, 2), "equivalence": general_rows}})
    result = {"scope": "Dimensionless synthetic matrix verification, not a beam-modal validation", "dimensions": [1, 2, 4],
              "duration": duration, "steps": steps, "gamma": gamma,
              "reference": "scipy.linalg.expm(A*t), evaluated independently at every point of the finest common grid",
              "error": "maximum Euclidean state error over all common grid times; endpoint error also retained",
              "conservative_control": "U=0.2*p-Ks*q on the proportional-damping plant, yielding stiffness K+Ks",
              "central4_scope": "Only the resulting conservative quadratic Hamiltonian; not a generic damped Central4 scheme",
              "cases": cases, "status": "all assertions passed"}
    write_result("matrix_structure_results.json", result)
    print("matrix: n=1,2,4, full-grid equivalence/order/structure passed", flush=True)


def closed_experiment():
    duration, db, dg = 20., .02, .01
    steps = [.04, .02, .01, .005, .0025]
    bhat, ghat = CONTROL.BETA-db, CONTROL.GAMMA-dg
    field = lambda z: CONTROL.closed_field(z, bhat, ghat)
    jac = lambda z: CONTROL.closed_jacobian(z, bhat, ghat)
    independent_field = lambda z: model_field(z, db, dg)
    refs, protocol = independent_references(independent_field, INITIAL, duration)
    nominal_refs, nominal_protocol = independent_references(lambda z: model_field(z), INITIAL, duration)
    rows, traces = [], {}
    refinement, physical_identity = 0., 0.
    for step in steps:
        states, diagnostics = integrate(field, jac, INITIAL, duration, step, gamma=dg)
        times = np.arange(len(states))*step
        actual = refs[1].sol(times).T
        nominal = nominal_refs[1].sol(times).T
        refinement = max(refinement, float(np.max(np.linalg.norm(actual-refs[0].sol(times).T, axis=1))))
        row = errors_and_order(states, actual, step, rows[-1] if rows else None)
        target_errors = np.linalg.norm(states-nominal, axis=1)
        row.update({"maximum_error_to_nominal_h0": float(np.max(target_errors)),
                    "RMS_error_to_nominal_h0": float(np.sqrt(np.mean(target_errors**2))), **diagnostics})
        physical_identity = max(physical_identity, max(float(np.linalg.norm(field(z)-independent_field(z))) for z in states))
        rows.append(row)
        tag = str(step).replace(".", "p")
        traces["time_"+tag], traces["state_"+tag] = times, states
        traces["actual_reference_"+tag], traces["nominal_reference_"+tag] = actual, nominal
    final_times = np.arange(round(duration/min(steps))+1)*min(steps)
    exact_target_gap = float(np.max(np.linalg.norm(refs[1].sol(final_times).T-nominal_refs[1].sol(final_times).T, axis=1)))
    assert abs(rows[-1]["observed_order"]-2) < .05
    assert physical_identity < 1e-12
    assert rows[-1]["maximum_error_to_nominal_h0"] > 20*rows[-1]["maximum_state_error"]
    assert refinement < rows[-1]["maximum_state_error"]*1e-4

    # Optional same-potential fourth-order verification. No imperfect damping
    # cancellation is silently removed: this is the declared h0 oracle branch.
    jacobian_checks = []
    for point in [INITIAL, np.array([-.07, .04, .03, -.02])]:
        step = .04
        numerical = np.column_stack([np.imag(central4_increment(point.astype(complex)+1e-25j*np.eye(4)[i], step))/1e-25 for i in range(4)])
        difference = float(np.max(np.abs(numerical-central4_increment_jacobian(point, step))))
        assert difference < 1e-11
        jacobian_checks.append(difference)
    central_rows = []
    nominal_refinement = 0.
    for step in steps[:-1]:
        states, diagnostics = integrate(lambda z: model_field(z), lambda z: model_jacobian(z), INITIAL, duration, step, method="central4")
        times = np.arange(len(states))*step
        exact = nominal_refs[1].sol(times).T
        nominal_refinement = max(nominal_refinement, float(np.max(np.linalg.norm(exact-nominal_refs[0].sol(times).T, axis=1))))
        row = errors_and_order(states, exact, step, central_rows[-1] if central_rows else None)
        row.update(diagnostics)
        row["maximum_nominal_energy_drift"] = float(np.max(np.abs(CONTROL.h0(states)-CONTROL.h0(states[0]))))
        central_rows.append(row)
    assert abs(central_rows[-1]["observed_order"]-4) < .1
    assert nominal_refinement < central_rows[-1]["maximum_state_error"]*1e-3
    assert max(r["maximum_ideal_standard_symplectic_defect_spectral2"] for r in central_rows) < 1e-12
    np.savez_compressed(ROOT / "closed_loop_convergence_traces.npz", **traces)
    result = {"scope": "Frozen, explicitly manufactured identification error, not refitting or measured parameter uncertainty",
              "duration_tau": duration, "initial_state": INITIAL, "delta_beta": db, "delta_gamma": dg,
              "true_beta": CONTROL.BETA, "true_gamma": CONTROL.GAMMA, "controller_beta": bhat, "controller_gamma": ghat,
              "closed_field": "X'=NY; Y'=-NX-(1+delta_beta)d(sin(d^T X)-d^T X)-delta_gamma Y",
              "physical_ports_used_inside_midpoint": True,
              "maximum_physical_vs_explicit_closed_field_difference": physical_identity,
              "independent_actual_reference": protocol, "maximum_actual_reference_refinement_difference": refinement,
              "independent_nominal_reference": nominal_protocol,
              "continuous_actual_to_nominal_maximum_on_finest_grid": exact_target_gap,
              "rows": rows,
              "conservative_nonlinear_central4": {"Hamiltonian": "h0; kappa=1, delta_gamma=0; equivalent exact compensation branch only",
                  "jacobian_complex_step_max_errors": jacobian_checks, "maximum_reference_refinement_difference": nominal_refinement, "rows": central_rows},
              "trace_file": "closed_loop_convergence_traces.npz", "status": "all assertions passed"}
    write_result("closed_loop_convergence_results.json", result)
    print("closed: frozen model-error midpoint and conservative magnetic Central4 passed", flush=True)


def defect_experiment():
    duration, coefficient = 4., .01
    steps = [.08, .04, .02, .01]
    a = np.array([[0., 1.], [-1., 0.]])
    initial, direction = np.array([.1, .02]), np.array([1., 0.])
    cases = []
    for exponent in [1, 2, 3]:
        rows = []
        for step in steps:
            count = round(duration/step); eta = coefficient*step**exponent
            update = matrix_midpoint(a, step)
            response = np.linalg.solve(np.eye(2)-step*a/2, eta*direction)
            states = np.empty((count+1, 2)); base = np.empty_like(states)
            states[0] = base[0] = initial
            residual_vectors, residual_norms, solve_errors = [], [], []
            for k in range(count):
                base[k+1] = update@base[k]
                states[k+1] = update@states[k]+response
                residual = states[k+1]-states[k]-step*a@((states[k+1]+states[k])/2)
                residual_vectors.append(residual.tolist())
                residual_norms.append(float(np.linalg.norm(residual, np.inf)))
                solve_errors.append(float(np.linalg.norm(residual-eta*direction, np.inf)))
            times = np.arange(count+1)*step
            exact = np.array([expm(t*a)@initial for t in times])
            row = errors_and_order(states, exact, step, rows[-1] if rows else None)
            extra = float(np.max(np.linalg.norm(states-base, axis=1)))
            row.update({"eta_requested": eta, "maximum_actual_residual_inf": max(residual_norms),
                        "maximum_actual_residual_2": max(np.linalg.norm(v) for v in residual_vectors),
                        "maximum_residual_target_discrepancy_inf": max(solve_errors),
                        "unperturbed_midpoint_maximum_error": float(np.max(np.linalg.norm(base-exact, axis=1))),
                        "maximum_added_error_vs_unperturbed_midpoint": extra,
                        "added_error_over_eta_divided_by_step": extra/(eta/step),
                        "error_over_step_squared_plus_actual_residual_over_step": row["maximum_state_error"]/(step**2+max(residual_norms)/step),
                        "added_error_observed_order": None if not rows else float(np.log2(rows[-1]["maximum_added_error_vs_unperturbed_midpoint"]/extra)),
                        "per_step_actual_residual_vectors": residual_vectors,
                        "per_step_actual_residual_infinity_norm": residual_norms})
            assert max(solve_errors) < 1e-14
            rows.append(row)
        assert abs(rows[-1]["added_error_observed_order"]-(exponent-1)) < .02
        if exponent == 3:
            assert abs(rows[-1]["observed_order"]-2) < .05
        cases.append({"q": exponent, "rows": rows})
    result = {"scope": "Manufactured algebraic-defect budget check, not measured Newton error or floating-point symplecticity",
              "A": a, "initial_state": initial, "duration": duration, "defect_direction": direction,
              "coefficient_c": coefficient, "defect_law": "r_k=c*Delta^q*(1,0), q=1,2,3, in the increment equation",
              "construction": "Solve the deliberately perturbed linear midpoint equation algebraically; record its actual original-equation residual at every step",
              "reference": "scipy.linalg.expm(A*t) at every saved time", "cases": cases, "status": "all assertions passed"}
    write_result("algebraic_defect_results.json", result)
    print("defect: actual per-step residuals and eta/Delta scaling passed", flush=True)


def weighted_experiment():
    duration, steps = 4., [.04, .02, .01, .005]
    cases = []
    for name, db, dg in [("uncompensated_true_plant", .2, .05), ("known_model_error_diagnostic", .02, .01)]:
        field = lambda z: model_field(z, db, dg)
        jac = lambda z: model_jacobian(z, db, dg)
        refs, protocol = independent_references(field, INITIAL, duration)
        methods = {}
        refinement = 0.
        for method in ["midpoint", "weighted_midpoint"]:
            rows = []
            for step in steps:
                states, diagnostics = integrate(field, jac, INITIAL, duration, step, method=method, gamma=dg, kappa=1+db)
                times = np.arange(len(states))*step
                exact = refs[1].sol(times).T
                refinement = max(refinement, float(np.max(np.linalg.norm(exact-refs[0].sol(times).T, axis=1))))
                row = errors_and_order(states, exact, step, rows[-1] if rows else None)
                row.update(diagnostics); rows.append(row)
            assert abs(rows[-1]["observed_order"]-2) < .05
            methods[method] = rows
        assert max(r["maximum_ideal_exponential_weighted_defect_spectral2"] for r in methods["weighted_midpoint"]) < 1e-12
        assert methods["midpoint"][0]["maximum_ideal_exponential_weighted_defect_spectral2"] > 1e-10
        cases.append({"name": name, "delta_beta": db, "delta_gamma": dg, "independent_reference": protocol,
                      "maximum_reference_refinement_difference": refinement, "methods": methods})
    result = {"scope": "Known-model nonlinear weighted-structure comparison; does not give the learning controller access to unknown errors",
              "duration_tau": duration, "initial_state": INITIAL, "steps": steps,
              "weighted_update": "S_half * conservative implicit midpoint(V_kappa) * S_half, S_half=diag(I,exp(-gamma*Delta/2)I)",
              "structure_factor": "exp(-gamma*Delta)", "cases": cases, "status": "all assertions passed"}
    write_result("nonlinear_weighted_results.json", result)
    print("weighted: nonlinear second order and exact exponential-weighted ideal tangent passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", choices=["all", "matrix", "closed", "defect", "weighted"], default="all")
    chosen = parser.parse_args().experiment
    stages = {"matrix": matrix_experiment, "closed": closed_experiment, "defect": defect_experiment, "weighted": weighted_experiment}
    for name, stage in stages.items():
        if chosen in ["all", name]:
            print("Running framework experiment", name, flush=True)
            stage()
