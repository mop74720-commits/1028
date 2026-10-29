"""Independent algebraic checks for the 1025 inheritance audit.

These are counterexamples to specific original claims and checks of corrected
formulas. They do not replace the separate 24-dimensional ROM reproductions.
No frozen source or evidence is modified. All tolerances are explicit below.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.linalg import expm
import sympy as sp

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "results/birkhoff_counterexamples.json"


def central_generator_coefficients(hamiltonian, coordinates, time_symbol, order):
    """Fixed-w HJ recurrence, initial endpoint time 0 and phi(0,w)=0.

    hatw=J(zplus-zminus)=grad(phi), w=(zplus+zminus)/2.
    phi_t=-H(w-J grad(phi)/2,t), with gauge phi(t,0) NOT imposed.
    Polynomial examples are used so coefficient extraction is exact algebra.
    This is executable finite-order recurrence, not a convergence certificate.
    """
    n = len(coordinates) // 2
    J = sp.zeros(2*n)
    J[:n, n:] = sp.eye(n)
    J[n:, :n] = -sp.eye(n)
    series = sp.Integer(0)
    coefficients = []
    for r in range(order):
        grad = sp.Matrix([sp.diff(series, x) for x in coordinates])
        shifted = sp.Matrix(coordinates) - J*grad/2
        rhs = -hamiltonian.subs(dict(zip(coordinates, shifted)), simultaneous=True)
        # Truncation before expanding avoids recursively expanding unused terms.
        coeff = sp.expand(sp.series(rhs, time_symbol, 0, r+1).removeO()).coeff(time_symbol, r)/(r+1)
        coeff = sp.factor(coeff)
        coefficients.append(coeff)
        series += time_symbol**(r+1)*coeff
    return coefficients


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-rom", action="store_true", help="also compute native 24D ROM conservative-limit diagnostics")
    args = parser.parse_args()
    started = time.perf_counter()
    records = []

    def record(name, source, values, status="corrected_formula_verified_and_original_claim_refuted"):
        records.append(dict(name=name, original_location=source, status=status, **values))

    q, p, t, gamma = sp.symbols("q p t gamma", real=True)
    z = sp.Matrix([q, p]); J = sp.Matrix([[0, 1], [-1, 0]]); K0 = -J
    H = (q*q+p*p)/2
    f = sp.Matrix([p, -q-gamma*p])
    a = sp.Matrix([(1+t*gamma)*p, 0])
    Ka = a.jacobian(z).T-a.jacobian(z)
    residual = sp.simplify(Ka*f-sp.Matrix([sp.diff(H,x) for x in z])-sp.diff(a,t))
    assert sp.simplify(sp.diff(a[0],p)-(1+t*gamma)) == 0
    assert residual != sp.zeros(2,1)
    record("incompatible_original_Pfaff_ansatz", "original1025-p0846..p0851", {
        "d_aq_d_p": str(sp.diff(a[0],p)), "representation_residual": str(residual),
        "correction": "Use a=(exp(gamma*t)*p,0), B=exp(gamma*t)*H, or a genuinely transported one-form; cannot independently fix B=H and d_pa_q=1."})

    Q, P = sp.symbols("Q P", real=True)
    candidate = sp.Matrix([-Q+gamma*P, -P])
    antisymmetric = candidate.jacobian([Q,P])-candidate.jacobian([Q,P]).T
    assert antisymmetric == sp.Matrix([[0,gamma],[-gamma,0]])
    record("original33_not_a_scalar_gradient_with_drag", "original1025-p0957/p0960/m0427; corrected drag sign alone is insufficient", {
        "gradient_Jacobian_antisymmetry": str(antisymmetric),
        "correction": "Construct a compatible chart and scalar generator before differentiating; physical midpoint need not be symplectic."})

    eye = np.eye(2); j = np.asarray(J,dtype=float)
    h = .3; rotation = expm(h*j)
    projection = (rotation+eye)/2
    incompatible_N = (rotation-eye)@np.linalg.inv(projection)
    compatible_N = j@incompatible_N
    bad_norm = float(np.linalg.norm(incompatible_N-incompatible_N.T,2))
    assert bad_norm > .1
    assert np.linalg.norm(compatible_N-compatible_N.T,2) < 2e-14
    record("TheoremA_requires_endpoint_compatibility_not_only_invertibility", "original1025-p0862..p0879, p1184..p1206", {
        "bad_endpoint_hatw": "zplus-zminus", "w": "(zplus+zminus)/2",
        "projection_min_singular": float(np.linalg.svd(projection,compute_uv=False)[-1]),
        "bad_gradient_antisymmetry_2": bad_norm,
        "compatible_hatw": "J@(zplus-zminus)",
        "compatible_gradient_antisymmetry_2": float(np.linalg.norm(compatible_N-compatible_N.T,2)),
        "identity_map_gradient_N": [[0,0],[0,0]], "identity_map_projection": eye.tolist(),
        "tolerance": 2e-14})

    # A nonlinear nonseparable Hamiltonian has M(q)=1/(1+q^2)>0.
    Hnon = (1+q*q)*p*p/2+q*q/2+q**4/4
    c = central_generator_coefficients(Hnon, [q,p], t, 4)
    fH = J*sp.Matrix([sp.diff(Hnon,x) for x in z])
    correction = (fH.T*sp.hessian(Hnon,z)*fH)[0]
    assert sp.simplify(c[0]+Hnon) == 0
    assert c[1] == 0 and c[3] == 0
    assert sp.simplify(c[2]+correction/24) == 0
    cn = central_generator_coefficients(Hnon+t*q*q/2, [q,p], t, 2)
    assert sp.simplify(cn[1]+q*q/4) == 0
    record("TheoremB_fixed_coordinate_recurrence", "original1025-p0888/m0399 versus corrected p1213/m0565", {
        "hamiltonian": str(Hnon), "mass": "1/(1+q^2)",
        "central_phi_coefficients_1_to_4": [str(v) for v in c],
        "nonautonomous_phi2_for_Hplus_t_q2_over2": str(cn[1]),
        "recurrence": "phi_(r+1)=-[tau^r] H(w-J*grad(sum_(j<=r)tau^j phi_j)/2,s+tau)/(r+1)",
        "checks": "c1=-H; c2=c4=0 autonomous; c3=-f.T*Hessian(H)*f/24; explicit time derivative retained",
        "proof_scope": "exact symbolic finite recurrence and endpoint HJ identity; no uniform 24D analytic-radius certificate"}, "corrected_finite_recurrence_executed")

    M = np.array([[2.,.3],[.3,1.]])
    Ks = np.array([[3.,.7],[.7,2.]])
    C = np.array([[.3,.04],[.04,.6]])
    Mi = np.linalg.solve(M,eye); x0 = np.array([.2,-.1,.04,.07]); h = .2
    A = np.block([[np.zeros((2,2)),Mi],[-Ks,-C@Mi]])
    full = np.linalg.solve(np.eye(4)-h*A/2,(np.eye(4)+h*A/2)@x0)
    E = h*h*Ks@Mi/4+h*C@Mi/2
    pp = np.linalg.solve(eye+E,(eye-E)@x0[2:]-h*Ks@x0[:2])
    corrected = np.r_[x0[:2]+h*Mi@(pp+x0[2:])/2,pp]
    Ewrong = h*h*Mi@Ks/4+h*Mi@C/2
    wrongp = np.linalg.solve(eye+Ewrong,(eye-Ewrong)@x0[2:]-h*Ks@x0[:2])
    wrong = np.r_[x0[:2]+h*Mi@(wrongp+x0[2:])/2,wrongp]
    assert np.linalg.norm(corrected-full) < 2e-14
    assert np.linalg.norm(wrong-full) > 1e-5
    record("original36_noncommuting_matrix_elimination", "original1025-p0993..p1003/m0442", {
        "mass": M.tolist(), "stiffness": Ks.tolist(), "damping": C.tolist(), "h":h,
        "corrected_full_residual_difference_2":float(np.linalg.norm(corrected-full)),
        "wrong_order_difference_2":float(np.linalg.norm(wrong-full)), "tolerance":2e-14})

    g = .7; h = .4; Ad = np.array([[0.,1.],[-1.,-g]])
    midpoint = np.linalg.solve(eye-h*Ad/2,eye+h*Ad/2)
    split = np.diag([1.,np.exp(-g*h/2)])
    weighted = split@np.linalg.solve(eye-h*j/2,eye+h*j/2)@split
    assert abs(np.linalg.det(midpoint)-1) > .1
    assert abs(np.linalg.det(midpoint)-np.exp(-g*h)) > 1e-3
    assert np.linalg.norm(weighted.T@j@weighted-np.exp(-g*h)*j) < 2e-14
    record("damped36_is_not_canonical_or_exact_exponential_symplectic", "original1025-p1073; p1167 Euclidean-volume overclaim", {
        "h":h,"gamma":g,"midpoint_determinant":float(np.linalg.det(midpoint)),
        "exact_flow_determinant":float(np.exp(-g*h)), "weighted_determinant":float(np.linalg.det(weighted)),
        "weighted_conformal_defect_2":float(np.linalg.norm(weighted.T@j@weighted-np.exp(-g*h)*j,2)), "tolerance":2e-14})

    steps=[.1,.05,.025,.0125]; errors={"midpoint":[],"central4_positive":[],"wrong_negative":[]}
    x0=np.array([.2,.1]); T=1.
    exact=expm(T*j)@x0
    for h in steps:
        for name,increment in [("midpoint",h*j),("central4_positive",(h+h**3/12)*j),("wrong_negative",(h-h**3/12)*j)]:
            advance=np.linalg.solve(eye-increment/2,eye+increment/2)
            result=np.linalg.matrix_power(advance,round(T/h))@x0
            errors[name].append(float(np.linalg.norm(result-exact)))
    orders={k:float(np.log2(v[-2]/v[-1])) for k,v in errors.items()}
    assert 3.98 < orders["central4_positive"] < 4.02
    assert 1.98 < orders["wrong_negative"] < 2.02
    record("Central4_positive_pre_correction_not_negative_modified_energy", "original1025-p1040..p1057; v10/supp_structure.tex:147-181", {
        "steps":steps,"errors":errors,"last_orders":orders,
        "scope":"independent harmonic sign/order check plus exact nonlinear variable-mass coefficient check above",
        "order_tolerance":.02}, "corrected_formula_verified")

    # Lie derivative transport jets without any exact-flow input.
    gammaq=sp.Rational(1,5)+q*q/10
    field=fH+sp.Matrix([0,-gammaq*p])
    a0=sp.Matrix([p,0])
    lie=lambda v: v.jacobian(z)*field+field.jacobian(z).T*v
    a1=-lie(a0); a2=-lie(a1)/2
    one=a0+t*a1; two=one+t*t*a2
    def eB(oneform):
        K=oneform.jacobian(z).T-oneform.jacobian(z)
        B=(oneform.T*field)[0]
        return sp.simplify(K*field-sp.diff(oneform,t)-sp.Matrix([sp.diff(B,x) for x in z]))
    e1=eB(one); e2=eB(two)
    assert sp.simplify(e1+t*lie(a1)) == sp.zeros(2,1)
    assert sp.simplify(e2+t*t*lie(a2)) == sp.zeros(2,1)
    sigma=t*q*p+t*t*q
    B=(two.T*field)[0]; ag=two+sp.Matrix([sp.diff(sigma,x) for x in z]); Bg=B-sp.diff(sigma,t)
    Kg=ag.jacobian(z).T-ag.jacobian(z)
    eg=sp.simplify(Kg*field-sp.diff(ag,t)-sp.Matrix([sp.diff(Bg,x) for x in z]))
    assert sp.simplify(eg-e2) == sp.zeros(2,1)
    sample={q:sp.Rational(1,5),p:sp.Rational(1,10)}
    times=[.2,.1,.05,.025]
    norms1=[float(sp.sqrt((e1.T*e1)[0]).subs(sample).subs(t,tt)) for tt in times]
    norms2=[float(sp.sqrt((e2.T*e2)[0]).subs(sample).subs(t,tt)) for tt in times]
    assert abs(np.log2(norms1[-2]/norms1[-1])-1) < 2e-13
    assert abs(np.log2(norms2[-2]/norms2[-1])-2) < 2e-13
    record("general_transport_jet_and_gauge_residual", "generalBirkhoff theory analytic recurrence; stage2 transport_moser_check.py:21-64", {
        "field":"variable mass H above, nonlinear drag -(1/5+q^2/10)*p",
        "a1":[str(v) for v in a1],"a2":[str(sp.factor(v)) for v in a2],
        "times":times,"first_jet_residuals":norms1,"second_jet_residuals":norms2,
        "gauge_residual_change":"identically zero (symbolic)",
        "scope":"finite transport recurrence check; 2D closure alone is vacuous and is not used as a high-dimensional closure certificate"}, "corrected_general_recurrence_executed")

    # A form-preserving map on an annulus can fail exactness.
    cflux=.03
    record("symplectic_does_not_imply_exact_symplectic_on_angle_annulus", "v10/supp_structure.tex:123-145 must be inherited before map KAM", {
        "map":"(theta,I)->(theta,I+c)","c":cflux,
        "two_form_defect":"identically zero", "period_integral_of_Psi_pullback_lambda_minus_lambda":2*np.pi*cflux,
        "conclusion":"c*dtheta is closed but not exact; a periodic single-valued primitive is essential"}, "analytic_counterexample")
    assert 2*np.pi*cflux != 0

    if args.with_rom:
        sys.path.insert(0,str(ROOT/"stage3/program"))
        import torch
        from birkhoff_rom import LocalBirkhoffROM
        torch.set_num_threads(1)
        native=LocalBirkhoffROM(rates=np.zeros(12))
        z0=native.bridge.initial_state()
        diag=native.diagnostics(z0,.0005,differentiate_oneform=True)
        assert diag["chart_matching_2"] < 2e-13
        assert diag["original_field_error_2"] > 1e-4
        assert diag["original_transport_compatibility_2"] < 2e-10
        record("native_24D_conservative_limit_bad_oneform_truncation", "stage3/program/birkhoff_rom.py:30-34,65-86", {
            "rates":"all zero; the original field is exactly canonical Hamiltonian",
            "initial_state_source":"ROMBridge.initial_state(amplitude=.01); nondimensional (Q,P)",
            "initial_state":z0.tolist(),
            "time_tau":.0005,
            "error_definition":"Euclidean norm of approximate_field(t,z0)-original_field(z0) at one fixed state; not a trajectory error",
            "diagnostics":diag,
            "conclusion":"Even with exact K0 and its exact transport, truncating the chosen advected one-form/B pair changes H. Use canonical a0,B=H for this known branch. This does not invalidate general Birkhoff existence."}, "native_ROM_limitation_verified")

    payload=dict(status="all assertions passed", command=" ".join(sys.argv),
                 python=sys.version, executable=sys.executable,
                 versions=dict(numpy=np.__version__,scipy=scipy.__version__,sympy=sp.__version__),
                 platform=platform.platform(), elapsed_seconds=time.perf_counter()-started,
                 source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 frozen_inputs_modified=False, tests=records)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(payload,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
