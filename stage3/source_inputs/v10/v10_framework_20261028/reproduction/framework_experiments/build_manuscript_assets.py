"""Render the current P1/P2/P3 numerical text and figures from recorded JSON.

No experiment is run and no historical authoring program is executed.
"""
from pathlib import Path
import hashlib
import json
import os
import re

import framework_values as V

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "authoring"
NEW_PATHS = {key: HERE/name for key, name in {
    "matrix": "matrix_structure_results.json", "closed": "closed_loop_convergence_results.json",
    "defect": "algebraic_defect_results.json", "weighted": "nonlinear_weighted_results.json",
}.items()}
NEW = {key: json.loads(path.read_text()) for key, path in NEW_PATHS.items()}
M, C, F, W = (NEW[key] for key in ("matrix", "closed", "defect", "weighted"))
assert all(x["status"] == "all assertions passed" for x in NEW.values())
TOKENS = dict(V.tokens)
EVIDENCE = dict(V.evidence)


def put(key, value, rendered=None, source="framework JSON"):
    TOKENS[key] = str(value) if rendered is None else rendered
    EVIDENCE[key] = {"value": value, "rendered": TOKENS[key], "source": source}


def s(value, digits=5):
    return V.sci(value, digits)


def dollar(value, digits=5):
    return "$"+s(value, digits)+"$"


def rows(key, values, source):
    put(key, values, "\n".join(" & ".join(row)+r" \\" for row in values), source)


eqmax = max(r["maximum_trajectory_equivalence_error"] for c in M["cases"] for r in c["equivalence"])
gmax = max(r["maximum_trajectory_equivalence_error"] for c in M["cases"] for r in c["general_drag_algebra_only"]["equivalence"])
c4 = C["conservative_nonlinear_central4"]
weighted = W["cases"][0]["methods"]
for key, value, digits in [
    ("MATRIX_EQ_MAX", eqmax, 4), ("GENERAL_EQ_MAX", gmax, 4),
    ("MATRIX_ORD_WEIGHT", M["cases"][1]["methods"]["ordinary_midpoint"][0]["exponential_weighted_defect_spectral2"], 4),
    ("MATRIX_WEIGHT", M["cases"][1]["methods"]["weighted_midpoint"][0]["exponential_weighted_defect_spectral2"], 4),
    ("NONLINEAR_ORD_WEIGHT", weighted["midpoint"][0]["maximum_ideal_exponential_weighted_defect_spectral2"], 4),
    ("NONLINEAR_WEIGHT", max(r["maximum_ideal_exponential_weighted_defect_spectral2"] for r in weighted["weighted_midpoint"]), 4),
    ("C4_REFINE", c4["maximum_reference_refinement_difference"], 4),
    ("C4_JAC", max(c4["jacobian_complex_step_max_errors"]), 4),
    ("CLOSED_PORT_ID", C["maximum_physical_vs_explicit_closed_field_difference"], 4),
    ("CLOSED_LAST_ERROR", C["rows"][-1]["maximum_state_error"], 5),
    ("CLOSED_LAST_TARGET", C["rows"][-1]["maximum_error_to_nominal_h0"], 5),
    ("CLOSED_CONTINUOUS_GAP", C["continuous_actual_to_nominal_maximum_on_finest_grid"], 5),
    ("CLOSED_REFINE", C["maximum_actual_reference_refinement_difference"], 4),
    ("DEFECT_TARGET_DISCREPANCY", max(r["maximum_residual_target_discrepancy_inf"] for c in F["cases"] for r in c["rows"]), 4),
]:
    put(key, value, s(value, digits))
for key, value in [
    ("WEIGHT_ORD_ORDER", weighted["midpoint"][-1]["observed_order"]),
    ("WEIGHT_ORDER", weighted["weighted_midpoint"][-1]["observed_order"]),
    ("C4_ORDER", c4["rows"][-1]["observed_order"]),
    ("CLOSED_ORDER", C["rows"][-1]["observed_order"]),
]:
    put(key, value, f"{value:.6f}")
put("DEFECT_ADDED_ORDERS", [c["rows"][-1]["added_error_observed_order"] for c in F["cases"]],
    ",\\,".join(f"{c['rows'][-1]['added_error_observed_order']:.6f}" if abs(c['rows'][-1]['added_error_observed_order']) > .0000005 else "0.000000" for c in F["cases"]))
put("DEFECT_TOTAL_ORDERS", [c["rows"][-1]["observed_order"] for c in F["cases"]], ",\\,".join(f"{c['rows'][-1]['observed_order']:.6f}" for c in F["cases"]))
put("DEFECT_RATIO", F["cases"][-1]["rows"][-1]["added_error_over_eta_divided_by_step"], f"{F['cases'][-1]['rows'][-1]['added_error_over_eta_divided_by_step']:.6f}")
for key, val, digits in [
    ("A_BY_MT", V.ag["learned"]["input_domain"]["maximum_abs_By_T"]*1e3, 6),
    ("A_TOTAL_MT", V.ag["learned"]["input_domain"]["maximum_total_local_field_T"]*1e3, 6),
    ("A_GRAD", V.ag["learned"]["input_domain"]["maximum_local_gradient_spectral2_T_per_m"], 8),
]:
    put(key, val, f"{val:.{digits}f}", "principal learned restoration input_domain")

method_keys = ["ordinary_midpoint", "weighted_midpoint", "conservative_midpoint", "conservative_central4"]
rows("MATRIX_SUMMARY_ROWS", [[str(c["n"]), dollar(max(r["maximum_trajectory_equivalence_error"] for r in c["equivalence"]), 3)]+[f"${c['methods'][key][-1]['observed_order']:.6f}$" for key in method_keys] for c in M["cases"]], "matrix.cases")
rows("MATRIX_FINE_ROWS", [[str(c["n"])]+[dollar(c["methods"][key][-1]["maximum_state_error"], 5) for key in method_keys] for c in M["cases"]], "matrix.cases.*.methods.*[-1]")
rows("A_ENERGY_ROWS", [[label, dollar(V.ag[key]["RMS_target_state_error"]), f"${V.ag[key]['physical_target_errors']['RMS_tip_displacement_error_m']*1e6:.6f}$", dollar(V.ag[key]["maximum_nominal_energy_drift"])] for key,label in [("passive","Passive"),("damping_only","Damping compensation"),("learned","Learned restoration"),("oracle","Oracle restoration")]], "existing principal restoration records")
rows("NONLINEAR_ORDER_ROWS", [[f"${old['step']:g}$", dollar(old["maximum_state_error"]), "---" if old["observed_order"] is None else f"${old['observed_order']:.6f}$", dollar(new["maximum_state_error"]), "---" if new["observed_order"] is None else f"${new['observed_order']:.6f}$"] for old,new in zip(V.a["oracle_midpoint_convergence"], c4["rows"])], "existing oracle midpoint and new conservative nonlinear Central4")
rows("CLOSED_ROWS", [[f"${r['step']:g}$", dollar(r["maximum_state_error"]), "---" if r["observed_order"] is None else f"${r['observed_order']:.6f}$", dollar(r["maximum_error_to_nominal_h0"])] for r in C["rows"]], "closed.rows")
rows("DEFECT_ROWS", [[str(c["q"]), dollar(c["rows"][-1]["maximum_actual_residual_inf"], 3), dollar(c["rows"][-1]["maximum_state_error"], 5), f"${c['rows'][-1]['observed_order']:.6f}$", f"${c['rows'][-1]['added_error_observed_order']:.6f}$", f"${c['rows'][-1]['added_error_over_eta_divided_by_step']:.6f}$"] for c in F["cases"]], "defect.cases.*.rows[-1]")
rows("NONLINEAR_WEIGHT_ROWS", [[f"$({c['delta_beta']:g},{c['delta_gamma']:g})$", dollar(c["methods"]["midpoint"][0]["maximum_ideal_exponential_weighted_defect_spectral2"],4), dollar(c["methods"]["weighted_midpoint"][0]["maximum_ideal_exponential_weighted_defect_spectral2"],4), f"${c['methods']['midpoint'][-1]['observed_order']:.6f}$", f"${c['methods']['weighted_midpoint'][-1]['observed_order']:.6f}$"] for c in W["cases"]], "weighted.cases")
rows("DAMP_A_ROWS", [[f"${r['zeta1']:g}$"]+[dollar(r["route_a_RMS"][key]) for key in ["passive","learned","oracle"]] for r in V.audit["damping_scenarios"]], "audit.damping_scenarios.route_a_RMS")
port_lines = V.tokens["PORT_ROWS"].splitlines()
put("A_PORT_ROWS", port_lines[0], port_lines[0], "principal restoration port row")
put("B_PORT_ROWS", port_lines[1], port_lines[1], "supplementary tracking port row")


def replace_tokens(text):
    for key in set(re.findall(r"@@([A-Z0-9_]+)@@", text)):
        if key not in TOKENS:
            raise KeyError(key)
        text = text.replace("@@"+key+"@@", TOKENS[key])
    assert "@@" not in text
    return text


def render_text():
    main = (TEMPLATES / "analysis.tex.in").read_text()
    supp = (TEMPLATES / "supp_experiments_base.tex.in").read_text()
    protocol = (TEMPLATES / "supp_framework_protocol.tex.in").read_text()
    anchor = r"\subsection{Conditional clearance and historical results that do not transfer}"
    assert anchor in supp
    supp = supp.replace(anchor, protocol+"\n"+anchor)
    ext = (TEMPLATES / "extension_tracking_results.tex.in").read_text()
    for name, content in [("analysis.tex", main), ("supp_experiments.tex", supp), ("extension_tracking_results.tex", ext)]:
        path = ROOT / "english" / "sections" / name
        path.write_text("% Generated by reproduction/framework_experiments/build_manuscript_assets.py.\n"+replace_tokens(content))


def render_figures(language="en", save_outputs=True, capture_callback=None):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/v10_framework_matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    import numpy as np
    chinese = language == "zh"
    target = ROOT / ("chinese" if chinese else "english") / "figures"
    if save_outputs:
        target.mkdir(parents=True, exist_ok=True)
    if chinese:
        font_path = ROOT / "fonts" / "NotoSansCJKsc-Regular.otf"
        font_manager.fontManager.addfont(str(font_path))
        family = font_manager.FontProperties(fname=str(font_path)).get_name()
    else:
        family = "DejaVu Sans"
    plt.rcParams.update({"font.family":family,"font.size":8,"axes.titlesize":9,"axes.labelsize":8,"xtick.labelsize":7,"ytick.labelsize":7,"legend.fontsize":6.5,"pdf.fonttype":3 if chinese else 42,"ps.fonttype":3 if chinese else 42,"axes.spines.top":False,"axes.spines.right":False,"savefig.facecolor":"white"})
    def t(en, zh):return zh if chinese else en
    plotted = {}
    def save(fig, name, values):
        plotted[name] = values
        if capture_callback is not None:
            capture_callback(name, fig)
        if save_outputs:
            fig.savefig(target/name, bbox_inches="tight")
        plt.close(fig)
    fig, axs = plt.subplots(1,3,figsize=(7.3,3.0),layout="constrained")
    case = M["cases"][1]
    labels = [t("MP, damped","中点，含阻尼"),t("Weighted MP","加权中点"),t("MP, conservative","中点，保守"),t("C4, conservative","四阶中央，保守")]
    matrix_plot = {}
    for key,label,marker,color,style in zip(method_keys,labels,["o","s","^","D"],[".6",".3","0","0"],["-","--","-","--"]):
        rr=case["methods"][key];xx=[r["step"] for r in rr];yy=[r["maximum_state_error"] for r in rr]
        axs[0].loglog(xx,yy,marker=marker,color=color,linestyle=style,markersize=3.5,markerfacecolor="white",linewidth=.9,label=label)
        matrix_plot[key]=[xx,yy]
    axs[0].set(title=t("(a) Matrix check, $n=2$","(a) 矩阵核查，$n=2$"),xlabel=t(r"Step $\Delta$",r"步长 $\Delta$"),ylabel=t("Maximum state error","最大状态误差"))
    axs[0].legend(frameon=False,loc="lower right",fontsize=6)
    for key,label,marker,color in [("ordinary_midpoint",t("Ordinary midpoint","普通中点"),"o",".5"),("weighted_midpoint",t("Weighted midpoint","加权中点"),"s","0")]:
        rr=case["methods"][key]
        axs[1].loglog([r["step"] for r in rr],[r["exponential_weighted_defect_spectral2"] for r in rr],marker=marker,color=color,markersize=3.5,markerfacecolor="white",label=label)
    axs[1].set(title=t("(b) Weighted structure","(b) 加权结构"),xlabel=t(r"Step $\Delta$",r"步长 $\Delta$"),ylabel=t("Exponential-weighted defect","指数加权缺陷"))
    axs[1].legend(frameon=False,loc="center right",fontsize=6)
    for rr,label,marker,style in [(V.a["oracle_midpoint_convergence"],t("Midpoint, oracle","中点，真值参数对照"),"o","-"),(c4["rows"],t("Central4, $h_0$","四阶中央，$h_0$"),"s","--")]:
        axs[2].loglog([r["step"] for r in rr],[r["maximum_state_error"] for r in rr],color="black",marker=marker,linestyle=style,markersize=4,markerfacecolor="white",label=label)
    axs[2].set(title=t("(c) Nonlinear magnetic $h_0$","(c) 非线性磁势 $h_0$"),xlabel=t(r"Step $\Delta$",r"步长 $\Delta$"),ylabel=t("Maximum state error","最大状态误差"))
    axs[2].legend(frameon=False,loc="lower right",fontsize=6)
    for i,ax in enumerate(axs):
        ticks=[.01,.02,.04,.08] if i<2 else [.005,.01,.02,.04]
        ax.set_xticks(ticks,[f"{v:g}" for v in ticks]);ax.minorticks_off();ax.grid(which="major",alpha=.2)
    save(fig,"framework_matrix_checks.pdf",{"matrix":matrix_plot,"structure":case["methods"],"magnetic_midpoint":V.a["oracle_midpoint_convergence"],"magnetic_central4":c4["rows"]})

    fig,axs=plt.subplots(1,3,figsize=(7.3,3.0),layout="constrained")
    xx=[r["step"] for r in C["rows"]]
    axs[0].loglog(xx,[r["maximum_state_error"] for r in C["rows"]],"ko-",markersize=3.5,markerfacecolor="white",label=t("To actual closed field","相对实际闭环"))
    axs[0].loglog(xx,[r["maximum_error_to_nominal_h0"] for r in C["rows"]],"ks--",markersize=3.5,markerfacecolor="white",label=t("To nominal $h_0$","相对标称 $h_0$"))
    axs[0].axhline(C["continuous_actual_to_nominal_maximum_on_finest_grid"],color=".5",linestyle=":",linewidth=1,label=t("Continuous model gap","连续模型差"))
    axs[0].set(title=t("(a) Fixed model error","(a) 固定模型误差"),xlabel=t(r"Step $\Delta$",r"步长 $\Delta$"),ylabel=t("Maximum state error","最大状态误差"))
    axs[0].legend(frameon=False,loc="lower right",fontsize=6)
    axs[0].set_xticks([.0025,.005,.01,.02,.04],[".0025",".005",".01",".02",".04"])
    for case,marker,color,style in zip(F["cases"],["o","s","^"],[".6",".3","0"],["-","--","-"]):
        rr=case["rows"]
        for ax,key in [(axs[1],"maximum_added_error_vs_unperturbed_midpoint"),(axs[2],"maximum_state_error")]:
            ax.loglog([r["step"] for r in rr],[r[key] for r in rr],color=color,marker=marker,linestyle=style,markersize=4,markerfacecolor="white",label=f"$q={case['q']}$")
    axs[1].set(title=t("(b) Added algebraic-defect error","(b) 代数缺陷新增误差"),xlabel=t(r"Step $\Delta$",r"步长 $\Delta$"),ylabel=t("Error to unperturbed midpoint","相对未扰动中点法的误差"))
    axs[2].set(title=t("(c) Total oscillator error","(c) 振子总误差"),xlabel=t(r"Step $\Delta$",r"步长 $\Delta$"),ylabel=t("Error to continuous flow","相对连续流的误差"))
    for ax in axs[1:]:ax.legend(frameon=False,loc="lower right");ax.set_xticks([.01,.02,.04,.08],[".01",".02",".04",".08"])
    for ax in axs:ax.minorticks_off();ax.grid(which="major",alpha=.2)
    save(fig,"framework_closed_loop_checks.pdf",{"closed":C["rows"],"continuous_model_gap":C["continuous_actual_to_nominal_maximum_on_finest_grid"],"defect":F["cases"]})
    from supplement_figures import render_supplement_figures
    plotted.update(render_supplement_figures(language, save_outputs, capture_callback))
    if save_outputs:
        (HERE / ("figure_data_"+language+".json")).write_text(json.dumps(plotted,ensure_ascii=False,indent=2)+"\n")
    return plotted


def build():
    render_text()
    render_figures("en")
    paths={**V.paths,**NEW_PATHS}
    record={"source_files":{k:{"path":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in paths.items()},
            "numerical_tokens":EVIDENCE,"transcribed_protocol_checks":V.protocol_assertions,
            "outputs":["english/sections/analysis.tex","english/sections/supp_experiments.tex","english/sections/extension_tracking_results.tex"],
            "scope":"Current P1/P2/P3 authoring from JSON; preserves the tracking extension in S4; never reruns numerical experiments."}
    (ROOT/"reviews/framework_numeric_provenance.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"sections":record["outputs"],"numerical_tokens":len(EVIDENCE),"new_figures":2,"retained_supplement_figures":2},indent=2))


if __name__ == "__main__":
    build()
