"""Current, bilingual renderer for the retained S4 comparison figures.

This reads the same audited JSON as the principal numerical chapter. It never
edits manuscript text or executes the archived two-route authoring program.
"""
from pathlib import Path
import os

import framework_values as V

ROOT = Path(__file__).resolve().parents[2]


def render_supplement_figures(language="en", save_outputs=True, capture_callback=None):
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
        font_path = ROOT / "fonts/NotoSansCJKsc-Regular.otf"
        font_manager.fontManager.addfont(str(font_path))
        family = font_manager.FontProperties(fname=str(font_path)).get_name()
    else:
        family = "DejaVu Sans"
    plt.rcParams.update({"font.family": family, "font.size": 8,
        "axes.titlesize": 9, "axes.labelsize": 8, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "legend.fontsize": 7,
        "pdf.fonttype": 3 if chinese else 42, "ps.fonttype": 3 if chinese else 42,
        "axes.spines.top": False, "axes.spines.right": False,
        "savefig.facecolor": "white"})
    def t(en, zh):
        return zh if chinese else en
    plotted = {}
    def save(fig, name, data):
        plotted[name] = data
        if capture_callback is not None:
            capture_callback(name, fig)
        if save_outputs:
            fig.savefig(target / name, bbox_inches="tight")
        plt.close(fig)

    ag, bg = V.ag, V.bg
    fig, axs = plt.subplots(1, 2, figsize=(7.3, 3.05), layout="constrained")
    labels = [t("Passive", "无控制"), t("Damping\nonly", "仅阻尼\n补偿"),
              t("Learned", "学习"), t("Oracle", "真值参数\n对照")]
    vals = [ag[k]["RMS_target_state_error"] for k in ["passive", "damping_only", "learned", "oracle"]]
    bars = axs[0].bar(range(4), vals, width=.62, color=[".8", ".6", ".3", "white"], edgecolor="black", linewidth=.7)
    bars[3].set_hatch("///")
    axs[0].set(yscale="log", ylim=(7e-6, .12), xticks=range(4), xticklabels=labels,
        ylabel=t("State RMS against independent reference", "相对独立参考的状态 RMS"),
        title=t("(a) Route A: restoration of $h_0$", "(a) 路线 A：恢复 $h_0$"))
    for i, v in enumerate(vals):
        axs[0].text(i, v*1.3, f"{v:.2e}", ha="center", va="bottom", fontsize=7)
    keys = ["passive", "damping_only", "learned_tracking", "oracle_tracking"]
    x, width = np.arange(4), .33
    all_rms = [bg[k]["RMS_state_error_independent_reference"] for k in keys]
    late_rms = [bg[k]["second_half_RMS_state_error_independent_reference"] for k in keys]
    axs[1].bar(x-width/2, all_rms, width,
        label=t(r"All $\tau\in[0,20]$", r"全时窗 $\tau\in[0,20]$"),
        color=".35", edgecolor="black", linewidth=.6)
    axs[1].bar(x+width/2, late_rms, width,
        label=t(r"Late $\tau\in[10,20]$", r"后半时窗 $\tau\in[10,20]$"),
        color="white", edgecolor="black", hatch="///", linewidth=.6)
    axs[1].set(yscale="log", ylim=(7e-6, .12), xticks=x, xticklabels=labels,
        ylabel=t("State RMS against independent reference", "相对独立参考的状态 RMS"),
        title=t(r"(b) Route B: tracking of $\widehat h$", r"(b) 路线 B：跟踪 $\widehat h$"))
    axs[1].legend(loc="upper right", frameon=False)
    for ax in axs:
        ax.grid(axis="y", which="major", alpha=.2)
        ax.set_axisbelow(True)
    save(fig, "new_baseline_results.pdf", {"route_a_RMS": vals,
         "route_b_independent_RMS_all": all_rms, "route_b_independent_RMS_late": late_rms})

    fig, axs = plt.subplots(1, 3, figsize=(7.3, 3.0), layout="constrained")
    ne = np.array([r["n_elements"] for r in V.fe["finite_element_convergence"]])
    err = np.array([r["relative_error_vs_continuum"] for r in V.fe["finite_element_convergence"]])
    for j, (marker, gray) in enumerate(zip(["o", "s", "^", "D"], ["0", ".25", ".5", ".7"])):
        axs[0].loglog(ne, err[:, j], marker=marker, color=gray, linewidth=.9,
             label=t(f"Mode {j+1}", f"模态 {j+1}"), markersize=4, markerfacecolor="white")
    axs[0].set(xticks=ne, xticklabels=["16", "32", "64"],
        xlabel=t("Hermite elements", "Hermite 单元数"),
        ylabel=t("Relative frequency error", "频率相对误差"),
        title=t("(a) FE / continuum check", "(a) 有限元／连续体核查"))
    axs[0].minorticks_off()
    axs[0].legend(frameon=False, loc="upper right", ncol=1)
    cv = V.a["oracle_midpoint_convergence"]
    steps = np.array([r["step"] for r in cv])
    errs = np.array([r["maximum_state_error"] for r in cv])
    guide = errs[-1]*(steps/steps[-1])**2
    axs[1].loglog(steps, errs, "ko-", markersize=4, markerfacecolor="white", label=t("Measured", "计算结果"))
    axs[1].loglog(steps, guide, "k--", linewidth=.8, label=r"$C\Delta^2$")
    axs[1].set(xlabel=t(r"Midpoint step $\Delta$", r"中点步长 $\Delta$"),
        ylabel=t("Maximum state error", "最大状态误差"),
        title=t("(b) Route-A oracle order", "(b) A 真值参数对照收敛阶"),
        xticks=[.005, .01, .02, .04], xticklabels=[".005", ".01", ".02", ".04"])
    axs[1].minorticks_off()
    axs[1].legend(frameon=False, loc="upper left")
    zs = [r["zeta1"] for r in V.audit["damping_scenarios"]]
    damping = {}
    for key, en, zh, marker, style, color in [
        ("Ap", "A passive", "A 无控制", "o", "-", ".6"),
        ("Al", "A learned", "A 学习", "s", "-", "0"),
        ("Bp", "B passive, late", "B 无控制，后半窗", "^", "--", ".6"),
        ("Bl", "B learned, late", "B 学习，后半窗", "D", "--", "0")]:
        vals = [r["route_a_RMS"]["passive" if key == "Ap" else "learned"]
                if key.startswith("A") else
                r["route_b_second_half_RMS_independent"]["passive" if key == "Bp" else "learned_tracking"]
                for r in V.audit["damping_scenarios"]]
        damping[key] = vals
        axs[2].semilogy(zs, vals, marker=marker, linestyle=style, color=color,
            linewidth=.9, markersize=4, markerfacecolor="white", label=t(en, zh))
    axs[2].set(xlabel=t(r"Declared first-mode ratio $\zeta_1^{\mathrm{d}}$", r"设定第一阶阻尼比 $\zeta_1^{\mathrm{d}}$"),
        ylabel=t("Independent-reference state RMS", "相对独立参考的状态 RMS"),
        title=t("(c) Refit at every damping value", "(c) 逐阻尼值重新拟合"),
        xticks=[0, .025, .05, .1], xticklabels=["0", ".025", ".05", ".10"], ylim=(1.5e-5, .15))
    axs[2].legend(frameon=False, loc="center right", fontsize=6.5)
    for ax in axs:
        ax.grid(which="major", alpha=.2)
    save(fig, "new_baseline_verification.pdf", {"fe_elements": ne.tolist(),
        "fe_relative_errors": err.tolist(), "oracle_midpoint_steps": steps.tolist(),
        "oracle_midpoint_errors": errs.tolist(), "quadratic_guide": guide.tolist(),
        "damping_ratios": zs, "damping_errors": damping})
    return plotted
