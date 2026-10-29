"""Check the two translated numerical sections and plotting instructions.

This does not compile LaTeX, rerun experiments, or modify English files.
The figure comparison intercepts savefig and compares numerical artists,
axis scales, ticks, markers and hatches, while excluding translated text
and CJK font encoding. Only this audit's JSON record is written.
"""
from pathlib import Path
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "reviews"
os.environ.setdefault("MPLCONFIGDIR", "/tmp/v10_translation_check_matplotlib")

def display_math(s):
    return [m.group() for m in re.finditer(r"\\begin\{(equation\*?|align\*?)\}.*?\\end\{\1\}", s, re.S)]

def inline_math(s):
    return re.findall(r"(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$", s, re.S)

extractors = {
    "display_math": display_math,
    "inline_math": inline_math,
    "references": lambda s: re.findall(r"\\(?:label|ref|eqref|cite[tp]?)\{[^}]*\}", s),
    "environment_order": lambda s: re.findall(r"\\(?:begin|end)\{[^}]*\}", s),
    "verbatim": lambda s: re.findall(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", s, re.S),
    "numeric_tokens_in_order": lambda s: re.findall(r"[+-]?(?:\d+\.\d*|\.\d+|\d+)", s),
    "code_identifiers": lambda s: re.findall(r"\\texttt\{[^}]*\}", s),
    "figure_paths": lambda s: re.findall(r"\\includegraphics(?:\[[^]]*\])?\{[^}]*\}", s),
    "paragraph_math": lambda s: [inline_math(p) for p in re.split(r"\n\s*\n", s)],
}
sections = {}
for name in ["analysis.tex", "supp_experiments.tex"]:
    en_path = ROOT / "english" / "sections" / name
    zh_path = ROOT / "chinese" / "sections" / name
    en, zh = en_path.read_text(), zh_path.read_text()
    comparisons = {}
    for label, extract in extractors.items():
        e, c = extract(en), extract(zh)
        comparisons[label] = {"identical": e == c, "english_count": len(e), "chinese_count": len(c)}
        assert e == c, (name, label)
    sections[name] = {
        "english_sha256": hashlib.sha256(en_path.read_bytes()).hexdigest(),
        "chinese_sha256": hashlib.sha256(zh_path.read_bytes()).hexdigest(),
        "comparisons": comparisons,
    }

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

paths = {
    "fe": ROOT / "reproduction" / "new_baseline.json",
    "a": ROOT / "reproduction" / "experiments" / "minimal_control_results.json",
    "b": ROOT / "reproduction" / "experiments" / "route_b_shared_results.json",
    "audit": ROOT / "reproduction" / "experiments" / "control_audit_summary.json",
}
data = {key: json.loads(path.read_text()) for key, path in paths.items()}

def numerical_axes(ax):
    lines = []
    for line in ax.lines:
        lines.append({
            "x": np.asarray(line.get_xdata()).tolist(),
            "y": np.asarray(line.get_ydata()).tolist(),
            "color": line.get_color(),
            "linestyle": line.get_linestyle(),
            "linewidth": float(line.get_linewidth()),
            "marker": line.get_marker(),
            "markersize": float(line.get_markersize()),
            "markerfacecolor": line.get_markerfacecolor(),
        })
    patches = []
    for p in ax.patches:
        patches.append({
            "x": float(p.get_x()), "y": float(p.get_y()),
            "width": float(p.get_width()), "height": float(p.get_height()),
            "facecolor": list(p.get_facecolor()), "edgecolor": list(p.get_edgecolor()),
            "linewidth": float(p.get_linewidth()), "hatch": p.get_hatch(),
        })
    return {
        "xscale": ax.get_xscale(), "yscale": ax.get_yscale(),
        "xlim": list(ax.get_xlim()), "ylim": list(ax.get_ylim()),
        "xticks": ax.get_xticks().tolist(), "yticks": ax.get_yticks().tolist(),
        "axisbelow": ax.get_axisbelow(),
        "lines": lines, "patches": patches,
    }

def capture_plot_source(script_name, start, end, language):
    source = (REV / script_name).read_text()
    start_index = source.index(start)
    stop_index = source.index(end, start_index)
    code = source[start_index:stop_index]
    namespace = dict(data)
    namespace.update({
        "plt": plt, "np": np,
        "ag": data["a"]["comparison"]["groups"],
        "bg": data["b"]["tracking"]["groups"],
        "FIG": ROOT / language / "figures",
    })
    saved = {}
    old_savefig = Figure.savefig
    def intercept(fig, destination, *args, **kwargs):
        saved[Path(destination).name] = {
            "figsize": fig.get_size_inches().tolist(),
            "axes": [numerical_axes(ax) for ax in fig.axes],
        }
    Figure.savefig = intercept
    try:
        exec(compile(code, script_name + " [plot-only, savefig intercepted]", "exec"), namespace)
    finally:
        Figure.savefig = old_savefig
        plt.close("all")
    return saved

english_plots = capture_plot_source("build_analysis_assets.py", "fig,axs=plt.subplots", "\ncounts=", "english")
chinese_plots = capture_plot_source("build_chinese_figures.py", "figure_data = {}", "\nrecord = {", "chinese")
assert english_plots == chinese_plots, "Figure numerical artists or graphical specification differ"
record = {
    "scope": "Translation-only equivalence checks; no LaTeX compilation and no numerical experiment rerun.",
    "sections": sections,
    "figures": {
        "numerical_artists_scales_ticks_styles_identical": True,
        "figure_names": list(english_plots),
        "panel_count": sum(len(v["axes"]) for v in english_plots.values()),
        "compared": ["figure size", "data arrays", "axis scales and limits", "tick values", "line colors and widths", "markers", "bar geometry", "hatches"],
        "intentionally_excluded": ["translated labels", "CJK font and its vector glyph encoding", "automatic layout adjustments caused by text width"],
    },
    "manual_review": {
        "terminology": "provenance/translation_terms.tsv followed; oracle = 真值参数对照; input-work governor = 输入功约束器; energy cap = 能量上限.",
        "scope_preserved": [
            "synthetic two-scalar feature test, not full CHNN training",
            "material references versus design choices versus computed outputs",
            "route A h0 restoration versus route B frozen learned reference tracking",
            "independent versus synchronous reference errors",
            "five damping scenarios each with fresh observations and refitting",
            "principal and scan time windows and solver tolerances remain distinct",
            "no saturation or input-work governor executed",
            "initial energy exceeds the proposed cap; no safety-cap verification claimed",
            "legacy outputs are not transferred to the new baseline",
        ],
        "full_chinese_manuscript_layout": "To be checked by the root assembly; no LaTeX compilation was performed by this agent.",
    },
}
(REV / "analysis_translation_checks.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"sections_passed": list(sections), "numeric_tokens": sum(v["comparisons"]["numeric_tokens_in_order"]["english_count"] for v in sections.values()), "figures_matched": list(english_plots), "all_checks_passed": True}, ensure_ascii=False, indent=2))
