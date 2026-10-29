"""Compute a first transport coefficient and numerical Moser chart for generic f.

This is a controlled approximation study, NOT an exact integrator for f.
R_a=R0+t R1 and B_a=R_a.f define a different field f_a. The script reports
that representation error explicitly. No exact physical flow is used in
R1, K_a, the auxiliary Moser integration, or its inverse.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",PYTHONDONTWRITEBYTECODE="1")
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from scipy.integrate import solve_ivp
from models import MechanicalTest,complex_jac

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"stage2/results/route_a"

def tensors(model,z):
    n=model.n; d=2*n
    R0=np.r_[z[n:],np.zeros(n)]
    DR0=np.block([[np.zeros((n,n)),np.eye(n)],[np.zeros((n,n)),np.zeros((n,n))]])
    f=model.field(z); Df=model.jac(z)
    R1=-DR0@f-Df.T@R0
    K1=-Df.T@model.K0-model.K0@Df
    return R0,DR0,R1,K1

def auxiliary_map(model,x,t,inverse=False,settings=None):
    # rho : lambda=0->1; chi=rho^{-1} : lambda=1->0.
    counts=[0]; sigma=[]
    def aux(lam,z):
        counts[0]+=1
        _,_,R1,K1=tensors(model,z)
        K=model.K0+lam*t*K1
        if not np.iscomplexobj(z) and not np.iscomplexobj(t):
            sigma.append(float(np.linalg.svd(K,compute_uv=False)[-1]))
        return np.linalg.solve(K,t*R1)
    initial=np.asarray(x,dtype=complex if np.iscomplexobj(x) or np.iscomplexobj(t) else float)
    opt=settings or dict(rtol=2e-12,atol=2e-14,max_step=.2)
    interval=(0.,1.) if inverse else (1.,0.)
    sol=solve_ivp(aux,interval,initial,method="DOP853",**opt)
    if not sol.success: raise RuntimeError(sol.message)
    return sol.y[:,-1],{"auxiliary_nfev":counts[0],"minimum_sampled_Klambda_singular_value":min(sigma) if sigma else None}

def one_case(n):
    m=MechanicalTest(n,"generic_nonproportional"); z=m.z0; d=2*n
    R0,DR0,R1,K1=tensors(m,z)
    DR1=complex_jac(lambda x:tensors(m,x)[2],z)
    f=m.field(z); Df=m.jac(z)
    coefficient_check=float(np.linalg.norm(DR1.T-DR1-K1,2))
    # Independently differentiate K1 to inspect closure (not to define K).
    DK=np.array([np.imag(tensors(m,z.astype(complex)+1e-25j*np.eye(d)[k])[3])/1e-25 for k in range(d)])
    closure=max(abs(DK[k,i,j]+DK[i,j,k]+DK[j,k,i]) for i in range(d) for j in range(d) for k in range(d))
    rows=[]
    for t in [.2,.1,.05,.025]:
        start=time.perf_counter()
        Ra=R0+t*R1; DRa=DR0+t*DR1
        Ka=modelK=m.K0+t*K1
        gradBa=DRa.T@f+Df.T@Ra
        residual=Ka@f-R1-gradBa
        predicted=-t*(DR1@f+Df.T@R1)
        fa=np.linalg.solve(Ka,R1+gradBa)
        u,work=auxiliary_map(m,z,t)
        eps=1e-25
        Dchi=np.column_stack([np.imag(auxiliary_map(m,z.astype(complex)+1j*eps*np.eye(d)[j],t)[0])/eps for j in range(d)])
        dchi_dt=np.imag(auxiliary_map(m,z,t+1j*eps)[0])/eps
        restored,backwork=auxiliary_map(m,u,t,True)
        congruence=float(np.linalg.norm(Dchi.T@m.K0@Dchi-Ka,2))
        map_refined,_=auxiliary_map(m,z,t,settings=dict(rtol=5e-14,atol=5e-16,max_step=.1))
        row={"time_from_fixed_expansion_origin":t,"representation_residual_2":float(np.linalg.norm(residual)),
             "representation_residual_formula_discrepancy_2":float(np.linalg.norm(residual-predicted)),
             "field_fa_minus_f_2":float(np.linalg.norm(fa-f)),
             "inverse_Ka_spectral2":float(np.linalg.norm(np.linalg.inv(Ka),2)),
             "bound_inverse_K_times_residual":float(np.linalg.norm(np.linalg.inv(Ka),2)*np.linalg.norm(residual)),
             "Moser_numerical_chart_congruence_spectral2":congruence,
             "Moser_inverse_composition_error_2":float(np.linalg.norm(restored-z)),
             "Moser_tolerance_refinement_difference_2":float(np.linalg.norm(u-map_refined)),
             "chart_transformed_fa_field_norm_2":float(np.linalg.norm(dchi_dt+Dchi@fa)),
             "single_point_construction_and_Jacobian_seconds":time.perf_counter()-start,
             "one_auxiliary_map_work":work,"inverse_auxiliary_map_work":backwork,
             "Jacobian_protocol":f"{d} additional complex-step auxiliary solves plus one time-sensitivity auxiliary solve; floating-point diagnostic"}
        assert row["representation_residual_formula_discrepancy_2"]<2e-12
        assert row["field_fa_minus_f_2"]<=row["bound_inverse_K_times_residual"]*(1+1e-10)
        assert congruence<2e-9
        assert row["Moser_inverse_composition_error_2"]<2e-10
        rows.append(row)
        print(n,t,"representation",row["representation_residual_2"],"chart",congruence,"seconds",row["single_point_construction_and_Jacobian_seconds"],flush=True)
    return {"n_coordinates":n,"phase_dimension":d,"field":"Same generic nonproportional nonlinear magnetic-potential model as run_extended.py",
            "R1_exterior_derivative_identity_spectral2":coefficient_check,"K1_closure_max_component":closure,
            "rows":rows,"exact_statement":"For exact arithmetic and exact auxiliary solves, Ka=dRa is closed and the Moser pullback is symplectic for Ka. Ra=R0+tR1 represents fa, not f, except at t=0.",
            "limitation":"First transport truncation leaves O(t) representation residual on this fixed-origin domain. This run computes charts at points, not a completed generic Birkhoff time integrator or a uniform domain-error bound. No full true-flow oracle is used."}

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    start=time.perf_counter(); results=[one_case(n) for n in [8,16]]
    payload={"cases":results,"elapsed_seconds":time.perf_counter()-start,"source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "status":"all stated residual, closure and numerical-chart checks passed",
             "purpose":"Make the general transport/Moser construction concrete and expose approximation error and actual derivative cost; do not relabel existence as an exact cheap physical solver."}
    (OUT/"transport_moser_results.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":payload["status"],"elapsed_seconds":payload["elapsed_seconds"]}),flush=True)

if __name__=="__main__": main()
