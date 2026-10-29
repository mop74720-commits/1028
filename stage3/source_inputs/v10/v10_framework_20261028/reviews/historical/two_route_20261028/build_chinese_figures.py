"""Render the frozen numerical figures with Chinese labels only.

Read the same JSON fields and use the same plotting geometry, data, scales,
markers, hatch patterns and rounding as build_analysis_assets.py.  Do not
import or execute that authoring script: the frozen English files are never
written by this script, and no experiment is rerun.

Run from any directory: python reviews/build_chinese_figures.py
"""
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "reproduction"
EXP = REP / "experiments"
REV = ROOT / "reviews"
FIG = ROOT / "chinese" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
paths = {
    "fe": REP / "new_baseline.json",
    "a": EXP / "minimal_control_results.json",
    "b": EXP / "route_b_shared_results.json",
    "audit": EXP / "control_audit_summary.json",
}
data = {key: json.loads(path.read_text()) for key, path in paths.items()}
fe, a, b, audit = (data[key] for key in ("fe", "a", "b", "audit"))
ag, bg = a["comparison"]["groups"], b["tracking"]["groups"]
assert audit["all_cross_file_checks_passed"]
assert a["identification"]["beta_hat"] == b["shared_identification"]["beta_hat"]
assert a["identification"]["gamma_hat"] == b["shared_identification"]["gamma_hat"]

os.environ.setdefault("MPLCONFIGDIR", "/tmp/v10_integrated_matplotlib_chinese")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

font_path = ROOT / "fonts" / "NotoSansCJKsc-Regular.otf"
font_manager.fontManager.addfont(str(font_path))
font_family = font_manager.FontProperties(fname=str(font_path)).get_name()
plt.rcParams.update({
    "font.family": font_family,
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    # The supplied CJK OTF uses CFF outlines.  Type 3 embeds those outlines
    # without falsely advertising an embedded TrueType (Type 42) font.
    "pdf.fonttype": 3,
    "ps.fonttype": 3,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.facecolor": "white",
})

figure_data = {}
fig, axs = plt.subplots(1, 2, figsize=(7.3, 3.05), layout="constrained")
labels = ["无控制", "仅阻尼\n补偿", "学习", "真值参数\n对照"]
vals = [ag[k]["RMS_target_state_error"] for k in ["passive", "damping_only", "learned", "oracle"]]
figure_data["route_a_RMS"] = vals
bars = axs[0].bar(range(4), vals, width=.62, color=[".8", ".6", ".3", "white"], edgecolor="black", linewidth=.7)
bars[3].set_hatch("///")
axs[0].set(yscale="log", ylim=(7e-6, .12), xticks=range(4), xticklabels=labels, ylabel="相对独立参考的状态 RMS", title="(a) 路线 A：恢复 $h_0$")
for i, v in enumerate(vals):
    axs[0].text(i, v*1.3, f"{v:.2e}", ha="center", va="bottom", fontsize=7)
keys = ["passive", "damping_only", "learned_tracking", "oracle_tracking"]
x = np.arange(4)
w = .33
all_rms = [bg[k]["RMS_state_error_independent_reference"] for k in keys]
late_rms = [bg[k]["second_half_RMS_state_error_independent_reference"] for k in keys]
figure_data["route_b_independent_RMS_all"] = all_rms
figure_data["route_b_independent_RMS_late"] = late_rms
axs[1].bar(x-w/2, all_rms, w, label=r"全时窗 $\tau\in[0,20]$", color=".35", edgecolor="black", linewidth=.6)
axs[1].bar(x+w/2, late_rms, w, label=r"后半时窗 $\tau\in[10,20]$", color="white", edgecolor="black", hatch="///", linewidth=.6)
axs[1].set(yscale="log", ylim=(7e-6, .12), xticks=x, xticklabels=labels, ylabel="相对独立参考的状态 RMS", title=r"(b) 路线 B：跟踪 $\widehat h$")
axs[1].legend(loc="upper right", frameon=False)
for ax in axs:
    ax.grid(axis="y", which="major", alpha=.2)
    ax.set_axisbelow(True)
fig.savefig(FIG / "new_baseline_results.pdf", bbox_inches="tight")
plt.close(fig)

fig, axs = plt.subplots(1, 3, figsize=(7.3, 3.0), layout="constrained")
ne = np.array([r["n_elements"] for r in fe["finite_element_convergence"]])
err = np.array([r["relative_error_vs_continuum"] for r in fe["finite_element_convergence"]])
figure_data["fe_elements"] = ne.tolist()
figure_data["fe_relative_errors"] = err.tolist()
for j, (marker, gray) in enumerate(zip(["o", "s", "^", "D"], ["0", ".25", ".5", ".7"])):
    axs[0].loglog(ne, err[:, j], marker=marker, color=gray, linewidth=.9, label=f"模态 {j+1}", markersize=4, markerfacecolor="white")
axs[0].set(xticks=ne, xticklabels=["16", "32", "64"], xlabel="Hermite 单元数", ylabel="频率相对误差", title="(a) 有限元／连续体核查")
axs[0].minorticks_off()
axs[0].legend(frameon=False, loc="upper right", ncol=1)
cv = a["oracle_midpoint_convergence"]
steps = np.array([r["step"] for r in cv])
errs = np.array([r["maximum_state_error"] for r in cv])
figure_data["oracle_midpoint_steps"] = steps.tolist()
figure_data["oracle_midpoint_errors"] = errs.tolist()
figure_data["quadratic_guide"] = (errs[-1]*(steps/steps[-1])**2).tolist()
axs[1].loglog(steps, errs, "ko-", markersize=4, markerfacecolor="white", label="计算结果")
axs[1].loglog(steps, errs[-1]*(steps/steps[-1])**2, "k--", linewidth=.8, label=r"$C\Delta^2$")
axs[1].set(xlabel=r"中点步长 $\Delta$", ylabel="最大状态误差", title="(b) A 真值参数对照收敛阶", xticks=[.005, .01, .02, .04], xticklabels=[".005", ".01", ".02", ".04"])
axs[1].minorticks_off()
axs[1].legend(frameon=False, loc="upper left")
zs = [r["zeta1"] for r in audit["damping_scenarios"]]
figure_data["damping_ratios"] = zs
figure_data["damping_errors"] = {}
for key, label, marker, linestyle, color in [
    ("Ap", "A 无控制", "o", "-", ".6"),
    ("Al", "A 学习", "s", "-", "0"),
    ("Bp", "B 无控制，后半窗", "^", "--", ".6"),
    ("Bl", "B 学习，后半窗", "D", "--", "0"),
]:
    vals = []
    for r in audit["damping_scenarios"]:
        vals.append(r["route_a_RMS"]["passive" if key == "Ap" else "learned"] if key.startswith("A") else r["route_b_second_half_RMS_independent"]["passive" if key == "Bp" else "learned_tracking"])
    figure_data["damping_errors"][key] = vals
    axs[2].semilogy(zs, vals, marker=marker, linestyle=linestyle, color=color, linewidth=.9, markersize=4, markerfacecolor="white", label=label)
axs[2].set(xlabel=r"设定第一阶阻尼比 $\zeta_1^{\mathrm{d}}$", ylabel="相对独立参考的状态 RMS", title="(c) 逐阻尼值重新拟合", xticks=[0, .025, .05, .1], xticklabels=["0", ".025", ".05", ".10"], ylim=(1.5e-5, .15))
axs[2].legend(frameon=False, loc="center right", fontsize=6.5)
for ax in axs:
    ax.grid(which="major", alpha=.2)
fig.savefig(FIG / "new_baseline_verification.pdf", bbox_inches="tight")
plt.close(fig)

record = {
    "scope": "Chinese labels and CJK font only; the English data fields, plot geometry, scales and style are unchanged; no experiment was rerun.",
    "source_files": {key: {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for key, path in paths.items()},
    "english_plot_source_sha256": hashlib.sha256((REV / "build_analysis_assets.py").read_bytes()).hexdigest(),
    "font": str(font_path.relative_to(ROOT)),
    "font_family": font_family,
    "font_embedding": "Type 3 vector glyphs for the supplied CFF OpenType font; plot data and graphical styles are unchanged.",
    "plotted_data": figure_data,
    "figures": ["chinese/figures/new_baseline_results.pdf", "chinese/figures/new_baseline_verification.pdf"],
}
(REV / "chinese_figure_provenance.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"figures": record["figures"], "font_family": font_family, "experiment_rerun": False}, ensure_ascii=False, indent=2))
