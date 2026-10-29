"""Independent 8/16-coordinate route-A verification and cost comparison.

Run with one BLAS thread. This does not read or overwrite supplied outputs.
Transported K in the generic nonlinear case is an expensive independent
diagnostic obtained by integrating the inverse flow and its variational ODE;
it is never used to construct or advance any tested numerical method.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",PYTHONDONTWRITEBYTECODE="1")
from pathlib import Path
import argparse
import hashlib
import json
import platform
import time
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from models import MechanicalTest,complex_jac
from integrators import prepare,step,TOLERANCE

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"stage2/results/route_a"
STEPS=[.2,.1,.05,.025]
DURATION=2.
FAMILIES={
    "conservative":["ordinary_midpoint_eq36","canonical_chart_midpoint","canonical_chart_central4"],
    "block_weighted":["ordinary_midpoint_eq36","weighted_chart_midpoint","weighted_chart_gauss4","frozen_current_weighted"],
    "generic_nonproportional":["ordinary_midpoint_eq36","canonical_chart_midpoint","damping_split_midpoint","gauss4_chart"],
    "linear_known_chart":["ordinary_midpoint_eq36","matrix_chart_midpoint"],
}

def clean(x):
    if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,np.generic): return x.item()
    return x

def save_json(path,obj):
    path.write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2,allow_nan=False)+"\n")

def structural_matrix(model,t,z,refine=False):
    _,E=model.chart(z,True)
    if model.family=="conservative":
        return model.K0,{"inverse_flow_nfev":0}
    if model.family=="block_weighted":
        W=np.diag(np.exp(model.rates*t)); zero=np.zeros_like(W)
        K=np.block([[zero,-W],[W,zero]])
        return E.T@K@E,{"inverse_flow_nfev":0}
    if model.family=="linear_known_chart":
        S=expm(-model.A*t); K=S.T@model.K0@S
        return E.T@K@E,{"inverse_flow_nfev":0}
    y=model.chart(z); d=len(y)
    if t==0:
        return model.K0,{"inverse_flow_nfev":0}
    def augmented(s,x):
        u=x[:d]; B=x[d:].reshape(d,d)
        return np.r_[model.latent_field(u),(model.latent_jac(u)@B).reshape(-1)]
    options=dict(rtol=5e-14,atol=5e-16,max_step=.025) if refine else dict(rtol=2e-13,atol=2e-15,max_step=.05)
    sol=solve_ivp(augmented,(t,0.),np.r_[y,np.eye(d).reshape(-1)],method="DOP853",**options)
    if not sol.success: raise RuntimeError(sol.message)
    B=sol.y[d:,-1].reshape(d,d)
    return E.T@B.T@model.K0@B@E,{"inverse_flow_nfev":sol.nfev}

def integrate(model,method,h,data,diagnostics=False):
    count=round(DURATION/h); states=np.empty((count+1,2*model.n)); states[0]=model.z0
    maxima={}; minima={}; total_newton=0; sampled=[]; diagnostic_nfev=0
    generic=model.family=="generic_nonproportional"
    sample_indices=sorted(set([0,count//2,count-1]))
    balance=0.; max_balance=0.; initial_H=model.energy(model.z0)
    for k in range(count):
        old=states[k]
        new,D,stats=step(model,method,old,k,h,data,diagnostics)
        states[k+1]=new
        if diagnostics:
            for name,val in stats.items():
                if val is None: continue
                if name.startswith("minimum_"):
                    minima[name]=min(minima.get(name,np.inf),val)
                else:
                    maxima[name]=max(maxima.get(name,0.),val)
            total_newton+=int(stats.get("Newton_corrections") or 0)
            defect=float(np.linalg.norm(D.T@model.J@D-model.J,2))
            maxima["canonical_symplectic_defect_spectral2"]=max(maxima.get("canonical_symplectic_defect_spectral2",0.),defect)
            if not generic or k in sample_indices:
                K0,work0=structural_matrix(model,k*h,old)
                K1,work1=structural_matrix(model,(k+1)*h,new)
                residual=float(np.linalg.norm(D.T@K1@D-K0,2))
                key="sampled_transport_K_defect_spectral2" if generic else "K_defect_spectral2"
                maxima[key]=max(maxima.get(key,0.),residual)
                if generic:
                    sampled.append({"index":k,"time":k*h,"transport_K_defect_spectral2":residual})
                    diagnostic_nfev+=work0["inverse_flow_nfev"]+work1["inverse_flow_nfev"]
            mid=(old+new)/2; M=model.mass(mid[:model.n]); C=model.damping(mid[:model.n])
            vm=np.linalg.solve(M,mid[model.n:])
            balance += model.energy(new)-model.energy(old)+h*vm@C@vm
            max_balance=max(max_balance,abs(balance))
            maxima["closed_H_drift_abs"]=max(maxima.get("closed_H_drift_abs",0.),abs(model.energy(new)-initial_H))
    result={"max_"+k:float(v) for k,v in maxima.items()}
    result.update({k:float(v) for k,v in minima.items()})
    if diagnostics:
        result.update(total_Newton_corrections=total_newton,failed_steps=0,
                      maximum_accumulated_midpoint_power_quadrature_residual=float(max_balance),
                      power_residual_scope="Nonquadratic H: diagnostic includes quadrature defect; it is not an asserted exact balance.",
                      structure_scope="Three independently transported-K step samples" if generic else "Every step, specified analytical K",
                      transported_K_samples=sampled,inverse_flow_diagnostic_nfev=diagnostic_nfev)
    return states,result

def timing(model,method,h,repetitions):
    warm=prepare(model,method,h,DURATION)
    integrate(model,method,h,warm,False)
    cold=[]; setup=[]; advances=[]; cached=[]
    for _ in range(repetitions):
        t0=time.perf_counter(); data=prepare(model,method,h,DURATION)
        t1=time.perf_counter(); integrate(model,method,h,data,False)
        t2=time.perf_counter(); integrate(model,method,h,data,False)
        t3=time.perf_counter()
        cold.append(t2-t0); setup.append(t1-t0); advances.append(t2-t1); cached.append(t3-t2)
    return {"repetitions":repetitions,"cold_total_seconds":cold,"setup_seconds":setup,
            "cold_advance_seconds":advances,"cached_advance_seconds":cached,
            "median_cold_seconds":float(np.median(cold)),"median_setup_seconds":float(np.median(setup)),
            "median_cached_seconds":float(np.median(cached)),
            "scope":"Single-thread same-process wall time; one dispatch warmup; cold includes ALL required chart/matrix preparation; reference and diagnostic tangents/K excluded consistently."}

def algebraic_checks(model):
    rng=np.random.default_rng(51025+model.n)
    points=model.z0+.025*rng.standard_normal((3,2*model.n))
    errors={"physical_Jacobian_vs_complex_step":0.,"point_chart_canonical":0.,"field_conjugacy":0.,
            "energy_gradient_geometric_inertia":0.,"closed_magnetic_gradient_identity":0.,"central4_Jacobian_vs_complex_step":None}
    for z in points:
        y,E=model.chart(z,True)
        errors["physical_Jacobian_vs_complex_step"]=max(errors["physical_Jacobian_vs_complex_step"],float(np.max(np.abs(model.jac(z)-complex_jac(model.field,z)))))
        errors["point_chart_canonical"]=max(errors["point_chart_canonical"],float(np.linalg.norm(E.T@model.J@E-model.J,2)))
        errors["field_conjugacy"]=max(errors["field_conjugacy"],float(np.linalg.norm(E@model.field(z)-model.latent_field(y))))
        hgrad=complex_jac(lambda x:np.atleast_1d(model.energy(x)),z).reshape(-1)
        v=model.field(z)[:model.n]
        expected=model.J@hgrad-np.r_[np.zeros(model.n),model.damping(z[:model.n])@v]
        errors["energy_gradient_geometric_inertia"]=max(errors["energy_gradient_geometric_inertia"],float(np.linalg.norm(expected-model.field(z))))
        potential_grad=model.potential(y[:model.n])[1]-model.Ks@y[:model.n]-model.quartic*y[:model.n]**3
        mag_force=model.port_force(y[:model.n])@model.currents(y[:model.n])
        errors["closed_magnetic_gradient_identity"]=max(errors["closed_magnetic_gradient_identity"],float(np.linalg.norm(potential_grad+mag_force)))
        if model.family=="conservative":
            e=float(np.max(np.abs(model.central4(y,.1,True)-complex_jac(lambda u:model.central4(u,.1),y))))
            errors["central4_Jacobian_vs_complex_step"]=max(errors["central4_Jacobian_vs_complex_step"] or 0.,e)
    assert max(v for v in errors.values() if v is not None)<2e-11
    return errors

def tangent_check(model,method):
    h=.1; data=prepare(model,method,h,DURATION,True); k=4
    z=model.z0+.003*np.arange(2*model.n)/(2*model.n)
    zn,D,_=step(model,method,z,k,h,data,True)
    eps=1e-5; eye=np.eye(len(z))
    fd=np.column_stack([(step(model,method,z+eps*e,k,h,data,False)[0]-step(model,method,z-eps*e,k,h,data,False)[0])/(2*eps) for e in eye])
    discrepancy=float(np.linalg.norm(fd-D,2))
    assert discrepancy<3e-8,(model.family,method,discrepancy)
    return {"h":h,"time":k*h,"difference_step":eps,"finite_difference_vs_ideal_tangent_spectral2":discrepancy,
            "scope":"One representative point/step; actual feedback dependence included; diagnostic, not a full-domain derivative certificate."}

def references(model):
    settings=[dict(rtol=1e-11,atol=1e-13,max_step=.05),dict(rtol=2e-13,atol=2e-15,max_step=.025)]
    start=time.perf_counter()
    sols=[solve_ivp(lambda t,z:model.field(z),(0.,DURATION),model.z0,method="DOP853",dense_output=True,**s) for s in settings]
    if not all(s.success for s in sols): raise RuntimeError("Reference solve failed")
    times=np.arange(round(DURATION/min(STEPS))+1)*min(STEPS)
    gap=float(np.max(np.linalg.norm(sols[0].sol(times).T-sols[1].sol(times).T,axis=1)))
    detail={"method":"Independent DOP853 in original variable-mass coordinates","settings":settings,
            "maximum_refinement_difference":gap,"wall_seconds":time.perf_counter()-start,"interval_enclosure":False}
    if model.family=="linear_known_chart":
        exact=np.array([model.inverse_chart(expm(model.A*t)@model.chart(model.z0))[0] for t in times])
        detail["known_exact_conjugacy_DOP853_difference"]=float(np.max(np.linalg.norm(exact-sols[1].sol(times).T,axis=1)))
    return sols[1],detail

def one_case(n,family,repetitions):
    print("START",n,family,flush=True)
    model=MechanicalTest(n,family); check=algebraic_checks(model); ref,refmeta=references(model)
    methods={}; trace={}
    for method in FAMILIES[family]:
        rows=[]
        grids=STEPS
        if method=="frozen_current_weighted":
            # This is an identified pre-asymptotic risk, not a reason to label
            # a state-frozen input as a continuous-feedback second-order map.
            # Keep all original grids and disclose the additional refinement.
            grids=STEPS+([.0125,.00625] if n==8 else [.0125,.00625,.003125,.0015625,.00078125])
        for h in grids:
            data=prepare(model,method,h,DURATION,True)
            tdiag=time.perf_counter(); states,diag=integrate(model,method,h,data,True)
            diag_seconds=time.perf_counter()-tdiag
            ts=np.arange(len(states))*h
            e=np.linalg.norm(states-ref.sol(ts).T,axis=1)
            row={"h":h,"endpoint_error":float(e[-1]),"maximum_grid_error":float(e.max()),"RMS_grid_error":float(np.sqrt(np.mean(e*e))),
                 "endpoint_order":None if not rows else float(np.log2(rows[-1]["endpoint_error"]/e[-1])),
                 "maximum_grid_order":None if not rows else float(np.log2(rows[-1]["maximum_grid_error"]/e.max())),
                 "diagnostics":diag,"diagnostic_trajectory_wall_seconds":diag_seconds,
                 "required_preparation_operations":data["required_operations"],"chart_checks":data.get("chart_checks"),
                 "cost":timing(model,method,h,repetitions)}
            row["residual_coordinate"]=("Two canonical Gauss-stage increment equations; conversion to output-state error uses stage and field derivative bounds" if method in ["gauss4_chart","weighted_chart_gauss4"] else "Linear chart midpoint and inverse point chart, separately measured" if method=="matrix_chart_midpoint" else "Original phase increment" if method=="ordinary_midpoint_eq36" else "Canonical inner increment plus inverse point-coordinate residual")
            row["Newton_unknown_dimension"]=(4*n if method in ["gauss4_chart","weighted_chart_gauss4"] else None if method=="matrix_chart_midpoint" else 2*n)
            rows.append(row)
            print(n,family,method,h,"err",row["maximum_grid_error"],"order",row["maximum_grid_order"],flush=True)
            if h==min(STEPS):
                trace[method]=states
        expected=4 if method in ["canonical_chart_central4","gauss4_chart","weighted_chart_gauss4"] else 1 if method=="frozen_current_weighted" else 2
        assert abs(rows[-1]["maximum_grid_order"]-expected)<.18,(n,family,method,rows[-1]["maximum_grid_order"])
        assert refmeta["maximum_refinement_difference"]<rows[-1]["maximum_grid_error"]*.02
        if family=="conservative" or method in ["weighted_chart_midpoint","weighted_chart_gauss4","matrix_chart_midpoint"]:
            assert max(r["diagnostics"]["max_K_defect_spectral2"] for r in rows)<2e-10
        methods[method]={"rows":rows,"steps":grids,"representative_tangent_check":tangent_check(model,method)}
    physicalG=[]; mass=[]; C=[]; current_peak=0.
    for z in trace[FAMILIES[family][0]]:
        y=model.chart(z); G=model.point_D(z[:n]).T@model.port_force(y[:n])
        physicalG.append(np.linalg.svd(G,compute_uv=False))
        mass.append(np.linalg.eigvalsh(model.mass(z[:n]))[0]); C.append(np.linalg.eigvalsh(model.damping(z[:n]))[0])
        current_peak=max(current_peak,float(np.max(np.abs(model.currents(y[:n])))))
    detail={"minimum_sampled_mass_eigenvalue":min(mass),"minimum_sampled_damping_eigenvalue":min(C),
            "magnetic_input_count":2,"maximum_input_rank":int(max(np.count_nonzero(s>1e-12) for s in physicalG)),
            "minimum_sampled_second_port_singular_value":float(min(s[-1] for s in physicalG)),
            "maximum_abs_dimensionless_current":current_peak,
            "control_scope":"Two smooth cosine ports with i_a=i0_a-k_a(Phi_a-Phi_ref_a); exactly integrable closed potential, no arbitrary modal-force compensation or calibrated current limit."}
    if family=="generic_nonproportional":
        z=trace["ordinary_midpoint_eq36"][len(trace["ordinary_midpoint_eq36"])//2]
        K,work=structural_matrix(model,1.,z); Kr,workr=structural_matrix(model,1.,z,True)
        detail["transport_K_refinement_spectral2"]=float(np.linalg.norm(K-Kr,2))
        detail["transport_K_scope"]="K at (z,t) is defined before discretization by exact inverse-flow pullback of K0 and approximated independently by DOP853; this costly diagnostic is NOT an algorithmic ingredient. Only three step samples per grid are claimed."
        detail["transport_K_refinement_nfev"]=[work["inverse_flow_nfev"],workr["inverse_flow_nfev"]]
    filename=f"extended_{family}_{n}dof.json"
    result={"parameters":model.parameters(),"T":DURATION,"initial_state":model.z0,"steps":STEPS,
            "algebraic_derivative_checks":check,"reference":refmeta,"methods":methods,"domain_and_input_diagnostics":detail,
            "Newton_increment_tolerance_inf":TOLERANCE,"interpretation":"Finite-dimensional synthetic method verification; no 3D rod/FSI/contact, learned-model or KAM claim."}
    save_json(OUT/filename,result)
    np.savez_compressed(OUT/f"extended_{family}_{n}dof_traces.npz",time=np.arange(round(DURATION/min(STEPS))+1)*min(STEPS),**trace)
    return result

def original36_linear_checks():
    cases=[]
    for n in [8,16]:
        m=MechanicalTest(n,"linear_known_chart"); M,C,K,Mi=m.M0,m.C0,m.Ks,m.Mi
        eye=np.eye(n); eye2=np.eye(2*n); rows=[]
        for h in STEPS:
            E=h/2*C@Mi+h*h/4*K@Mi
            P=np.linalg.solve(eye+E,np.hstack([-h*K,eye-E]))
            Q=np.hstack([eye,np.zeros((n,n))])+h/2*Mi@(P+np.hstack([np.zeros((n,n)),eye]))
            eliminated=np.vstack([Q,P])
            midpoint=np.linalg.solve(eye2-h*m.A/2,eye2+h*m.A/2)
            difference=float(np.linalg.norm(eliminated-midpoint,2))
            SPD=M+h*C/2+h*h*K/4
            rows.append({"h":h,"eq36_midpoint_matrix_difference_spectral2":difference,"minimum_SPD_elimination_eigenvalue":float(np.linalg.eigvalsh(SPD)[0])})
            assert difference<3e-14
        cases.append({"n":n,"commutator_MK_spectral2":float(np.linalg.norm(M@K-K@M,2)),"commutator_MC_spectral2":float(np.linalg.norm(M@C-C@M,2)),"rows":rows})
    h=.1;c=.2;A=np.array([[0.,1.],[-1.,-c]])
    R=np.linalg.solve(np.eye(2)-h*A/2,np.eye(2)+h*A/2)
    one={"m":1,"k":1,"c":c,"h":h,"det_midpoint":float(np.linalg.det(R)),"det_exact":float(np.exp(-c*h)),
         "weighted_factor_residual":float(np.exp(c*h)*np.linalg.det(R)-1.)}
    result={"scope":"Exact matrix formula36 and ordinary midpoint are the same method for constant matrices; no distinct efficiency/error claim from renaming.","cases":cases,"one_dof_counterexample":one}
    save_json(OUT/"original36_linear_identity.json",result)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--dimensions",nargs="+",type=int,default=[8,16]);parser.add_argument("--family",choices=list(FAMILIES)+["all"],default="all");parser.add_argument("--timing-repetitions",type=int,default=3)
    args=parser.parse_args()
    if args.timing_repetitions<3: parser.error("At least three timing repetitions required")
    OUT.mkdir(parents=True,exist_ok=True); start=time.perf_counter(); results=[]
    algebra=original36_linear_checks()
    for n in args.dimensions:
        for family in FAMILIES:
            if args.family in [family,"all"]: results.append(one_case(n,family,args.timing_repetitions))
    manifest={"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"platform":platform.platform(),
              "source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))},
              "elapsed_seconds":time.perf_counter()-start,"dimensions":args.dimensions,"family":args.family,
              "case_count":len(results),"status":"all scoped numerical assertions passed",
              "source_policy":"All new outputs are independent; no supplied source edited."}
    save_json(OUT/f"extended_run_manifest_{args.family}.json",manifest)
    print(json.dumps(manifest,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
