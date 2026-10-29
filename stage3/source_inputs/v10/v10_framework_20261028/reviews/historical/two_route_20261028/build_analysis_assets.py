"""Build numerical manuscript sections and figures from existing run records.

This script reads JSON only; it neither fits a model nor reruns an experiment.
Run from any directory: python reviews/build_analysis_assets.py
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import re

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "reproduction"
EXP = REP / "experiments"
REV = ROOT / "reviews"
FIG = ROOT / "english" / "figures"
SEC = ROOT / "english" / "sections"
for directory in (FIG, SEC):
    directory.mkdir(parents=True, exist_ok=True)

paths = {
    "fe": REP / "new_baseline.json",
    "a": EXP / "minimal_control_results.json",
    "b": EXP / "route_b_shared_results.json",
    "scan": EXP / "damping_sensitivity_results.json",
    "audit": EXP / "control_audit_summary.json",
}
data = {key: json.loads(path.read_text()) for key, path in paths.items()}
fe, a, b, scan, audit = (data[k] for k in ("fe", "a", "b", "scan", "audit"))
red, prop = fe["reduced"], fe["properties"]
aid, bid = a["identification"], b["shared_identification"]
ag, bg = a["comparison"]["groups"], b["tracking"]["groups"]
assert audit["all_cross_file_checks_passed"]
assert aid["beta_hat"] == bid["beta_hat"] == audit["identification"]["beta_hat"]
assert aid["gamma_hat"] == bid["gamma_hat"]
assert red["omega0_rad_s"] == a["parameters"]["omega0_rad_s"]
assert red["d"] == a["parameters"]["d"] == b["parameters"]["d"]
assert scan["fit_recomputed_for_every_scenario"]
assert len(scan["scenarios"]) == 5

def sci(value, places=3):
    if value == 0:
        return "0"
    mantissa, exponent = f"{value:.{places}e}".split("e")
    return mantissa + r"\times10^{" + str(int(exponent)) + "}"

def fixed(value, places=6):
    return f"{value:.{places}f}"

def vector(values, places=8):
    return r"\bigl(" + r",\,".join(fixed(v, places) for v in values) + r"\bigr)^{\mathsf T}"

tokens = {}
evidence = {}
def token(name, value, rendered=None, source="computed from supplied JSON"):
    tokens[name] = str(value) if rendered is None else rendered
    evidence[name] = {"value": value, "rendered": tokens[name], "source": source}

for name, value, render, source in [
    ("OMEGA0", red["omega0_rad_s"], fixed(red["omega0_rad_s"], 8), "fe.reduced.omega0_rad_s"),
    ("OMEGA2", red["omega_rad_s"][1], fixed(red["omega_rad_s"][1], 8), "fe.reduced.omega_rad_s[1]"),
    ("NU2", red["nu"][1], fixed(red["nu"][1], 8), "fe.reduced.nu[1]"),
    ("D_VECTOR", red["d"], vector(red["d"]), "fe.reduced.d"),
    ("ELL_VECTOR", red["ell_m"], vector(red["ell_m"], 10), "fe.reduced.ell_m"),
    ("DS_VECTOR", red["Ds"], r"\bigl(" + r",\,".join(sci(v, 9) for v in red["Ds"]) + r"\bigr)", "fe.reduced.Ds"),
    ("MU", prop["mu_A_m2"], sci(prop["mu_A_m2"], 8), "fe.properties.mu_A_m2"),
    ("TIP_MASS", prop["tip_mass_kg"], sci(prop["tip_mass_kg"], 6), "fe.properties.tip_mass_kg"),
    ("TIP_J", prop["tip_rotary_inertia_kg_m2"], sci(prop["tip_rotary_inertia_kg_m2"], 7), "fe.properties.tip_rotary_inertia_kg_m2"),
    ("ENERGY_SCALE", prop["E0_J"], sci(prop["E0_J"], 8), "fe.properties.E0_J"),
    ("ALPHA", red["alpha_s_inv"], fixed(red["alpha_s_inv"], 10), "fe.reduced.alpha_s_inv"),
    ("ZETA2", red["zeta"][1], fixed(red["zeta"][1], 10), "fe.reduced.zeta[1]"),
    ("BETA_HAT", aid["beta_hat"], fixed(aid["beta_hat"], 12), "a.identification.beta_hat"),
    ("GAMMA_HAT", aid["gamma_hat"], fixed(aid["gamma_hat"], 14), "a.identification.gamma_hat"),
    ("TRAIN_RMSE", aid["training_RMSE"], sci(aid["training_RMSE"], 4), "a.identification.training_RMSE"),
    ("VALID_RMSE", aid["validation_RMSE"], sci(aid["validation_RMSE"], 4), "a.identification.validation_RMSE"),
    ("GRAM_MIN", bid["lambda_min_normalized_Gram"], sci(bid["lambda_min_normalized_Gram"], 5), "b.shared_identification.lambda_min_normalized_Gram"),
    ("COND_RAW", aid["raw_design_cond2"], fixed(aid["raw_design_cond2"], 2), "a.identification.raw_design_cond2"),
    ("COND_SCALED", aid["column_scaled_design_cond2"], fixed(aid["column_scaled_design_cond2"], 8), "a.identification.column_scaled_design_cond2"),
    ("COEFF_FACTOR", bid["coefficient_bound_multiplier_1_over_sqrt_lambda_min"], sci(bid["coefficient_bound_multiplier_1_over_sqrt_lambda_min"], 5), "b.shared_identification.coefficient_bound_multiplier_1_over_sqrt_lambda_min"),
    ("EPS_TRUTH", bid["epsilonI_using_synthetic_truth_diagnostic_only"], sci(bid["epsilonI_using_synthetic_truth_diagnostic_only"], 5), "b.shared_identification.epsilonI_using_synthetic_truth_diagnostic_only"),
    ("COEFF_DIAG", bid["coefficient_bound_expression_using_truth_diagnostic_only"], sci(bid["coefficient_bound_expression_using_truth_diagnostic_only"], 5), "b.shared_identification.coefficient_bound_expression_using_truth_diagnostic_only"),
    ("COEFF_ACTUAL", bid["actual_coefficient_error_using_synthetic_truth"], sci(bid["actual_coefficient_error_using_synthetic_truth"], 5), "b.shared_identification.actual_coefficient_error_using_synthetic_truth"),
    ("TIME_S", a["comparison"]["duration_seconds"], fixed(a["comparison"]["duration_seconds"], 6), "a.comparison.duration_seconds"),
    ("SCAN_TIME_S", scan["duration_seconds"], fixed(scan["duration_seconds"], 6), "scan.duration_seconds"),
    ("A_REFINE", a["reference_validation"]["maximum_refinement_state_difference"], sci(a["reference_validation"]["maximum_refinement_state_difference"], 4), "a.reference_validation.maximum_refinement_state_difference"),
    ("B_REFINE", b["numerical_checks"]["reference_RK4_maximum_difference"], sci(b["numerical_checks"]["reference_RK4_maximum_difference"], 4), "b.numerical_checks.reference_RK4_maximum_difference"),
    ("A_VF", ag["learned"]["RMS_continuous_vectorfield_mismatch_to_V0"], sci(ag["learned"]["RMS_continuous_vectorfield_mismatch_to_V0"], 4), "a.comparison.groups.learned.RMS_continuous_vectorfield_mismatch_to_V0"),
    ("A_TIP_UM", ag["learned"]["physical_target_errors"]["RMS_tip_displacement_error_m"]*1e6, fixed(ag["learned"]["physical_target_errors"]["RMS_tip_displacement_error_m"]*1e6, 6), "a.comparison.groups.learned.physical_target_errors.RMS_tip_displacement_error_m * 1e6"),
    ("A_PASSIVE_RMS", ag["passive"]["RMS_target_state_error"], sci(ag["passive"]["RMS_target_state_error"], 5), "a.comparison.groups.passive.RMS_target_state_error"),
    ("A_DAMP_RMS", ag["damping_only"]["RMS_target_state_error"], sci(ag["damping_only"]["RMS_target_state_error"], 5), "a.comparison.groups.damping_only.RMS_target_state_error"),
    ("A_LEARNED_RMS", ag["learned"]["RMS_target_state_error"], sci(ag["learned"]["RMS_target_state_error"], 5), "a.comparison.groups.learned.RMS_target_state_error"),
    ("A_ORACLE_RMS", ag["oracle"]["RMS_target_state_error"], sci(ag["oracle"]["RMS_target_state_error"], 5), "a.comparison.groups.oracle.RMS_target_state_error"),
    ("A_CAYLEY", ag["oracle"]["maximum_ideal_Cayley_symplectic_defect_spectral2"], sci(ag["oracle"]["maximum_ideal_Cayley_symplectic_defect_spectral2"], 4), "a.comparison.groups.oracle.maximum_ideal_Cayley_symplectic_defect_spectral2"),
    ("B_PRED_NOMINAL", b["prediction"]["nominal_h0_RMS_state_error_vs_hstar"], sci(b["prediction"]["nominal_h0_RMS_state_error_vs_hstar"], 5), "b.prediction.nominal_h0_RMS_state_error_vs_hstar"),
    ("B_PRED_LEARNED", b["prediction"]["learned_hhat_RMS_state_error_vs_hstar"], sci(b["prediction"]["learned_hhat_RMS_state_error_vs_hstar"], 5), "b.prediction.learned_hhat_RMS_state_error_vs_hstar"),
    ("B_FULL_RMS", bg["learned_tracking"]["RMS_state_error_independent_reference"], sci(bg["learned_tracking"]["RMS_state_error_independent_reference"], 5), "b.tracking.groups.learned_tracking.RMS_state_error_independent_reference"),
    ("B_HALF_RMS", bg["learned_tracking"]["second_half_RMS_state_error_independent_reference"], sci(bg["learned_tracking"]["second_half_RMS_state_error_independent_reference"], 5), "b.tracking.groups.learned_tracking.second_half_RMS_state_error_independent_reference"),
    ("B_HALF_SYNC", bg["learned_tracking"]["second_half_RMS_state_error_synchronous_reference"], sci(bg["learned_tracking"]["second_half_RMS_state_error_synchronous_reference"], 5), "b.tracking.groups.learned_tracking.second_half_RMS_state_error_synchronous_reference"),
    ("B_FINAL_SYNC", bg["learned_tracking"]["final_state_error_synchronous_reference"], sci(bg["learned_tracking"]["final_state_error_synchronous_reference"], 5), "b.tracking.groups.learned_tracking.final_state_error_synchronous_reference"),
    ("B_FINAL_IND", bg["learned_tracking"]["final_state_error_independent_reference"], sci(bg["learned_tracking"]["final_state_error_independent_reference"], 5), "b.tracking.groups.learned_tracking.final_state_error_independent_reference"),
    ("B_REF_PHASE", bg["learned_tracking"]["maximum_reference_midpoint_error_vs_RK4"], sci(bg["learned_tracking"]["maximum_reference_midpoint_error_vs_RK4"], 5), "b.tracking.groups.learned_tracking.maximum_reference_midpoint_error_vs_RK4"),
    ("B_HALF_RATIO", b["numerical_checks"]["reference_midpoint_error_ratio_on_halving_step"], fixed(b["numerical_checks"]["reference_midpoint_error_ratio_on_halving_step"], 6), "b.numerical_checks.reference_midpoint_error_ratio_on_halving_step"),
    ("B_CAYLEY", b["numerical_checks"]["oracle_linear_error_Cayley_comparison_maximum"], sci(b["numerical_checks"]["oracle_linear_error_Cayley_comparison_maximum"], 4), "b.numerical_checks.oracle_linear_error_Cayley_comparison_maximum"),
    ("SCAN_ZERO_GAMMA", scan["scenarios"][0]["identification"]["gamma_hat"], sci(scan["scenarios"][0]["identification"]["gamma_hat"], 4), "scan.scenarios[0].identification.gamma_hat"),
    ("PORT_COND", a["physical_interface"]["column_normalized_condition_number"], fixed(a["physical_interface"]["column_normalized_condition_number"], 7), "a.physical_interface.column_normalized_condition_number"),
    ("ALL_ANGLE", audit["all_run_domain_maxima"]["maximum_abs_tip_angle_rad"], fixed(audit["all_run_domain_maxima"]["maximum_abs_tip_angle_rad"], 8), "audit.all_run_domain_maxima.maximum_abs_tip_angle_rad"),
    ("ALL_SLOPE", audit["all_run_domain_maxima"]["maximum_abs_beam_slope_spatial_grid"], fixed(audit["all_run_domain_maxima"]["maximum_abs_beam_slope_spatial_grid"], 8), "audit.all_run_domain_maxima.maximum_abs_beam_slope_spatial_grid"),
    ("ALL_COS", audit["all_run_domain_maxima"]["minimum_abs_cos_tip_angle"], fixed(audit["all_run_domain_maxima"]["minimum_abs_cos_tip_angle"], 8), "audit.all_run_domain_maxima.minimum_abs_cos_tip_angle"),
    ("ALL_TOTAL_MT", audit["all_run_domain_maxima"]["maximum_total_local_field_T"]*1e3, fixed(audit["all_run_domain_maxima"]["maximum_total_local_field_T"]*1e3, 6), "audit.all_run_domain_maxima.maximum_total_local_field_T * 1e3"),
    ("ALL_GRAD", audit["all_run_domain_maxima"]["maximum_local_gradient_spectral2_T_per_m"], fixed(audit["all_run_domain_maxima"]["maximum_local_gradient_spectral2_T_per_m"], 8), "audit.all_run_domain_maxima.maximum_local_gradient_spectral2_T_per_m"),
    ("ALL_PORT_ERR", audit["all_run_domain_maxima"]["maximum_input_reconstruction_error"], sci(audit["all_run_domain_maxima"]["maximum_input_reconstruction_error"], 4), "audit.all_run_domain_maxima.maximum_input_reconstruction_error"),
]:
    token(name, value, render, source)

z0 = a["comparison"]["initial_state"]
angle0 = sum(x*y for x, y in zip(red["d"], z0[:2]))
h0 = .5*sum(red["nu"][j]*(z0[j]**2+z0[j+2]**2) for j in range(2)) + 1 - math.cos(angle0) - .5*angle0**2
token("INITIAL_ENERGY_NJ", h0*prop["E0_J"]*1e9, fixed(h0*prop["E0_J"]*1e9, 6), "h0(a.comparison.initial_state) * fe.properties.E0_J * 1e9")
token("EC_NJ", prop["Ec_at_4mm_J"]*1e9, fixed(prop["Ec_at_4mm_J"]*1e9, 6), "fe.properties.Ec_at_4mm_J * 1e9")
token("BUDGET_NJ", .95*prop["Ec_at_4mm_J"]*1e9, fixed(.95*prop["Ec_at_4mm_J"]*1e9, 6), ".95 * fe.properties.Ec_at_4mm_J * 1e9")
token("MAIN_STEP_S", .001/red["omega0_rad_s"], sci(.001/red["omega0_rad_s"], 5))
token("TRAIN_TIME_S", 4/red["omega0_rad_s"], fixed(4/red["omega0_rad_s"], 6))
token("FE32_MAX", max(fe["finite_element_convergence"][1]["relative_error_vs_continuum"]), sci(max(fe["finite_element_convergence"][1]["relative_error_vs_continuum"]), 5))
token("FE64_MAX", max(fe["finite_element_convergence"][2]["relative_error_vs_continuum"]), sci(max(fe["finite_element_convergence"][2]["relative_error_vs_continuum"]), 5))
token("TIP_EFFECT_PERCENT", fe["tip_mass_and_bias_effects"]["tip_inertia_change_relative_to_biased_massless_tip"][0]*100, fixed(fe["tip_mass_and_bias_effects"]["tip_inertia_change_relative_to_biased_massless_tip"][0]*100, 5))
token("ORDER_LAST", a["oracle_midpoint_convergence"][-1]["observed_order"], fixed(a["oracle_midpoint_convergence"][-1]["observed_order"], 6), "a.oracle_midpoint_convergence[-1].observed_order")
token("PYTHON_VERSION", fe["environment"]["python"], source="fe.environment.python")
token("NUMPY_VERSION", fe["environment"]["numpy"], source="fe.environment.numpy")
token("SCIPY_VERSION", fe["environment"]["scipy"], source="fe.environment.scipy")
token("B_REFINED_DIFF", b["numerical_checks"]["maximum_actual_state_difference_at_common_times"], sci(b["numerical_checks"]["maximum_actual_state_difference_at_common_times"],5), "b.numerical_checks.maximum_actual_state_difference_at_common_times")
token("B_JAC_CHECK", b["numerical_checks"]["analytic_augmented_Jacobian_finite_difference_maximum_error"], sci(b["numerical_checks"]["analytic_augmented_Jacobian_finite_difference_maximum_error"],4), "b.numerical_checks.analytic_augmented_Jacobian_finite_difference_maximum_error")

def rows_token(name, rows, source):
    token(name, rows, "\n".join(" & ".join(row) + r" \\" for row in rows), source)

rows_token("FE_ROWS", [[str(r["n_elements"])] + [f"${v:.8f}$" for v in r["omega"]] + ["$"+sci(max(r["relative_error_vs_continuum"]),4)+"$"] for r in fe["finite_element_convergence"]], "fe.finite_element_convergence")
rows_token("ORDER_ROWS", [[f"${r['step']:g}$", "$"+sci(r["maximum_state_error"],5)+"$", "---" if r["observed_order"] is None else f"${r['observed_order']:.6f}$"] for r in a["oracle_midpoint_convergence"]], "a.oracle_midpoint_convergence")
rows_token("A_ROWS", [[label, "$"+sci(ag[key]["RMS_target_state_error"],5)+"$", f"${ag[key]['physical_target_errors']['RMS_tip_displacement_error_m']*1e6:.6f}$"] for key,label in [("passive","Passive"),("damping_only","Damping compensation"),("learned","Learned restoration"),("oracle","Oracle restoration")]], "a.comparison.groups")
rows_token("B_ROWS", [[label] + ["$"+sci(bg[key][metric],5)+"$" for metric in ["RMS_state_error_independent_reference","second_half_RMS_state_error_independent_reference","second_half_RMS_state_error_synchronous_reference"]] for key,label in [("passive","Passive"),("damping_only","Damping compensation"),("learned_tracking","Learned tracking"),("oracle_tracking","Oracle tracking")]], "b.tracking.groups")
rows_token("INITIAL_ROWS", [[f"Training {i+1}"]+[f"${v:g}$" for v in row] for i,row in enumerate(aid["train_initials"])] + [[f"Validation {i+1}"]+[f"${v:g}$" for v in row] for i,row in enumerate(aid["validation_initials"])], "a.identification.train_initials and validation_initials")
rows_token("DAMP_FIT_ROWS", [[f"${r['zeta1_scenario']:g}$",f"${r['alpha_s_inv']:.9f}$",f"${r['identification']['beta_hat']:.12f}$", "$"+sci(r["identification"]["gamma_hat"],10)+"$", "$"+sci(r["identification"]["lambda_min_normalized_Gram"],4)+"$"] for r in scan["scenarios"]], "scan.scenarios.*.identification")
rows_token("DAMP_ERROR_ROWS", [[f"${r['zeta1']:g}$"]+["$"+sci(v,5)+"$" for v in [r["route_a_RMS"]["passive"],r["route_a_RMS"]["learned"],r["route_b_second_half_RMS_independent"]["passive"],r["route_b_second_half_RMS_independent"]["learned_tracking"]]] for r in audit["damping_scenarios"]], "audit.damping_scenarios")
port_rows=[]
for label, r in [("A: learned",ag["learned"]),("B: learned",bg["learned_tracking"])]:
    pp=r["input_domain"]
    port_rows.append([label, f"${pp['maximum_abs_By_T']*1e3:.6f}$", f"${pp['maximum_total_local_field_T']*1e3:.6f}$",f"${pp['maximum_local_gradient_spectral2_T_per_m']:.8f}$",f"${pp['maximum_abs_tip_force_N']*1e6:.6f}$"])
rows_token("PORT_ROWS",port_rows,"a/b learned input_domain")
sens_rows=[]
for r in fe["design_sensitivity"]:
    labels={"Br_lower_1p40_T":r"$B_r=1.40$ T", "Br_upper_1p45_T":r"$B_r=1.45$ T", "tip_inertia_minus10pct":r"$m_t,J_t$ scaled by $0.9$", "tip_inertia_plus10pct":r"$m_t,J_t$ scaled by $1.1$", "E_minus20pct":r"$E$ scaled by $0.8$", "E_plus20pct":r"$E$ scaled by $1.2$"}
    if r["case"] in labels:
        sens_rows.append([labels[r["case"]],f"${r['omega_rad_s'][0]:.8f}$",f"${100*r['relative_omega_change_from_nominal'][0]:+.5f}$",f"${r['zeta1_with_nominal_alpha_held_fixed']:.8f}$"])
rows_token("SENS_ROWS",sens_rows,"fe.design_sensitivity; nominal alpha held fixed")
rows_token("PROPERTY_ROWS", [[label,"$"+sci(prop[key],8)+"$",unit] for label,key,unit in [
    (r"Area $A$","A_m2",r"m$^2$"), (r"Second moment $I$","I_m4",r"m$^4$"),
    (r"Flexural rigidity $EI$","EI_N_m2",r"N\,m$^2$"), (r"Beam mass $\rho AL$","beam_mass_kg",r"kg"),
    (r"Core volume $V_m$","magnet_volume_m3",r"m$^3$"), (r"Core mass $m_t$","tip_mass_kg",r"kg"),
    (r"Core inertia $J_t$","tip_rotary_inertia_kg_m2",r"kg\,m$^2$"),
    (r"Dipole moment $\mu$","mu_A_m2",r"A\,m$^2$"), (r"Energy scale $E_0$","E0_J",r"J")]], "fe.properties")
gram=bid["normalized_joint_Gram_AtransA_over_2L"]
token("GRAM_MATRIX",gram,r"\begin{pmatrix}"+" & ".join(sci(x,8) for x in gram[0])+r"\\"+" & ".join(sci(x,8) for x in gram[1])+r"\end{pmatrix}","b.shared_identification.normalized_joint_Gram_AtransA_over_2L")

protocol_assertions = {
    "geometry":fe["parameters"]["L_m"] == .08 and fe["parameters"]["r_m"] == .0006,
    "material":fe["parameters"]["E_Pa"] == 2.1e6 and fe["parameters"]["rho_kg_m3"] == 1028,
    "core":fe["parameters"]["magnet_side_m"] == .00025 and fe["parameters"]["magnet_rho_kg_m3"] == 7500 and fe["parameters"]["Br_T"] == 1.425,
    "bias":fe["parameters"]["B0_T"] == .03,
    "nominal_damping":red["gamma"] == .05 and red["zeta"][0] == .025,
    "training":aid["duration_each"] == 4 and aid["generator_RK4_step"] == .0005 and aid["observation_step"] == .002 and aid["window_length"] == .04 and aid["training_scalar_rows"] == 800,
    "main_protocol":a["comparison"]["duration_tau"] == 20 and a["comparison"]["step_tau"] == .001,
    "tracking_gains":b["tracking"]["kappa_p"] == 1 and b["tracking"]["kappa_d"] == 2,
    "scan_protocol":scan["duration_tau"] == 10 and scan["midpoint_step_tau"] == .002 and scan["zeta1_scenarios"] == [0,.01,.025,.05,.1],
}
assert all(protocol_assertions.values()), protocol_assertions

for source, destination in [("analysis_source.tex.in", "analysis.tex"), ("supp_experiments_source.tex.in", "supp_experiments.tex")]:
    text=(REV/source).read_text()
    used=set(re.findall(r"@@([A-Z0-9_]+)@@", text))
    for key in used:
        if key not in tokens:
            raise KeyError(f"Unknown numerical token {key} in {source}")
        text=text.replace("@@"+key+"@@",tokens[key])
    assert "@@" not in text
    (SEC/destination).write_text("% Generated from existing JSON by reviews/build_analysis_assets.py.\n"+text)

(REV/"analysis_numeric_provenance.json").write_text(json.dumps({
    "source_files": {key:{"path":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()} for key,path in paths.items()},
    "numerical_tokens": evidence,
    "transcribed_protocol_checks": protocol_assertions,
    "figure_sources": {"new_baseline_results.pdf":"a.comparison.groups and b.tracking.groups", "new_baseline_verification.pdf":"fe.finite_element_convergence, a.oracle_midpoint_convergence, audit.damping_scenarios"},
    "scope":"No rerun and no fabricated time histories; all reported outputs are rendered from the supplied run records. Protocol constants are transcribed from the associated scripts and JSON."
},ensure_ascii=False,indent=2)+"\n")

os.environ.setdefault("MPLCONFIGDIR", "/tmp/v10_integrated_matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"axes.titlesize":9,"axes.labelsize":8,"xtick.labelsize":7,"ytick.labelsize":7,"legend.fontsize":7,"pdf.fonttype":42,"ps.fonttype":42,"axes.spines.top":False,"axes.spines.right":False,"savefig.facecolor":"white"})

fig,axs=plt.subplots(1,2,figsize=(7.3,3.05),layout="constrained")
labels=["Passive","Damping\nonly","Learned","Oracle"]
vals=[ag[k]["RMS_target_state_error"] for k in ["passive","damping_only","learned","oracle"]]
bars=axs[0].bar(range(4),vals,width=.62,color=[".8",".6",".3","white"],edgecolor="black",linewidth=.7)
bars[3].set_hatch("///")
axs[0].set(yscale="log",ylim=(7e-6,.12),xticks=range(4),xticklabels=labels,ylabel="State RMS against independent reference",title="(a) Route A: restoration of $h_0$")
for i,v in enumerate(vals):axs[0].text(i,v*1.3,f"{v:.2e}",ha="center",va="bottom",fontsize=7)
keys=["passive","damping_only","learned_tracking","oracle_tracking"]
x=np.arange(4); w=.33
axs[1].bar(x-w/2,[bg[k]["RMS_state_error_independent_reference"] for k in keys],w,label=r"All $\tau\in[0,20]$",color=".35",edgecolor="black",linewidth=.6)
axs[1].bar(x+w/2,[bg[k]["second_half_RMS_state_error_independent_reference"] for k in keys],w,label=r"Late $\tau\in[10,20]$",color="white",edgecolor="black",hatch="///",linewidth=.6)
axs[1].set(yscale="log",ylim=(7e-6,.12),xticks=x,xticklabels=labels,ylabel="State RMS against independent reference",title=r"(b) Route B: tracking of $\widehat h$")
axs[1].legend(loc="upper right",frameon=False)
for ax in axs:ax.grid(axis="y",which="major",alpha=.2);ax.set_axisbelow(True)
fig.savefig(FIG/"new_baseline_results.pdf",bbox_inches="tight")
plt.close(fig)

fig,axs=plt.subplots(1,3,figsize=(7.3,3.0),layout="constrained")
ne=np.array([r["n_elements"] for r in fe["finite_element_convergence"]])
err=np.array([r["relative_error_vs_continuum"] for r in fe["finite_element_convergence"]])
for j,(marker,gray) in enumerate(zip(["o","s","^","D"],["0",".25",".5",".7"])):
    axs[0].loglog(ne,err[:,j],marker=marker,color=gray,linewidth=.9,label=f"Mode {j+1}",markersize=4,markerfacecolor="white")
axs[0].set(xticks=ne,xticklabels=["16","32","64"],xlabel="Hermite elements",ylabel="Relative frequency error",title="(a) FE / continuum check")
axs[0].minorticks_off();axs[0].legend(frameon=False,loc="upper right",ncol=1)
cv=a["oracle_midpoint_convergence"]
steps=np.array([r["step"] for r in cv]);errs=np.array([r["maximum_state_error"] for r in cv])
axs[1].loglog(steps,errs,"ko-",markersize=4,markerfacecolor="white",label="Measured")
axs[1].loglog(steps,errs[-1]*(steps/steps[-1])**2,"k--",linewidth=.8,label=r"$C\Delta^2$")
axs[1].set(xlabel=r"Midpoint step $\Delta$",ylabel="Maximum state error",title="(b) Route-A oracle order",xticks=[.005,.01,.02,.04],xticklabels=[".005",".01",".02",".04"])
axs[1].minorticks_off();axs[1].legend(frameon=False,loc="upper left")
zs=[r["zeta1"] for r in audit["damping_scenarios"]]
for key,label,marker,linestyle,color in [("Ap","A passive","o","-",".6"),("Al","A learned","s","-","0"),("Bp","B passive, late","^","--",".6"),("Bl","B learned, late","D","--","0")]:
    vals=[]
    for r in audit["damping_scenarios"]:
        vals.append(r["route_a_RMS"]["passive" if key=="Ap" else "learned"] if key.startswith("A") else r["route_b_second_half_RMS_independent"]["passive" if key=="Bp" else "learned_tracking"])
    axs[2].semilogy(zs,vals,marker=marker,linestyle=linestyle,color=color,linewidth=.9,markersize=4,markerfacecolor="white",label=label)
axs[2].set(xlabel=r"Declared first-mode ratio $\zeta_1^{\mathrm{d}}$",ylabel="Independent-reference state RMS",title="(c) Refit at every damping value",xticks=[0,.025,.05,.1],xticklabels=["0",".025",".05",".10"],ylim=(1.5e-5,.15))
axs[2].legend(frameon=False,loc="center right",fontsize=6.5)
for ax in axs:ax.grid(which="major",alpha=.2)
fig.savefig(FIG/"new_baseline_verification.pdf",bbox_inches="tight")
plt.close(fig)

counts={name:len(re.findall(r"\b[A-Za-z][A-Za-z'-]*\b",(SEC/name).read_text())) for name in ["analysis.tex","supp_experiments.tex"]}
print(json.dumps({"generated_sections":counts,"numerical_tokens":len(tokens),"figures":["new_baseline_results.pdf","new_baseline_verification.pdf"]},indent=2))
