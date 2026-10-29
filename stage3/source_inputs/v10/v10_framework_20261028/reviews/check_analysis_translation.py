"""Check all three current translated numerical inputs and four figure designs.

No manuscript, figure, experiment output or compiler state is modified.
--figures-only checks the shared bilingual plotting code before translation.
Only this audit's JSON report is written.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "reviews"
os.environ.setdefault("MPLCONFIGDIR", "/tmp/v10_framework_translation_check")
parser = argparse.ArgumentParser()
parser.add_argument("--figures-only", action="store_true")
args = parser.parse_args()

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
if not args.figures_only:
    for name in ["analysis.tex", "supp_experiments.tex", "extension_tracking_results.tex"]:
        en_path = ROOT / "english/sections" / name
        zh_path = ROOT / "chinese/sections" / name
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

import numpy as np
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, str(ROOT / "reproduction/framework_experiments"))
from build_manuscript_assets import render_figures

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

def capture_plots(language):
    saved = {}
    def capture(name, fig):
        saved[name] = {
            "figsize": fig.get_size_inches().tolist(),
            "axes": [numerical_axes(ax) for ax in fig.axes],
        }
    data = render_figures(language, save_outputs=False, capture_callback=capture)
    return saved, data

english_plots, english_data = capture_plots("en")
chinese_plots, chinese_data = capture_plots("zh")
assert english_data == chinese_data, "Plotted numerical source data differ"
assert english_plots == chinese_plots, "Figure numerical artists, scales, ticks or styles differ"
record = {
    "scope": "Current P1/P2/P3 and S4 translation equivalence; no compilation, experiment run or figure write.",
    "mode": "figures only" if args.figures_only else "three sections and four figures",
    "sections": sections,
    "figures": {
        "numerical_data_artists_scales_ticks_styles_identical": True,
        "figure_names": list(english_plots),
        "panel_count": sum(len(v["axes"]) for v in english_plots.values()),
        "compared": ["figure size", "data arrays", "axis scales and limits", "tick values", "line colors and widths", "markers", "bar geometry", "hatches"],
        "intentionally_excluded": ["translated labels", "CJK font encoding", "automatic text-width layout adjustments"],
    },
    "renderer_files": {
        name: hashlib.sha256((ROOT / "reproduction/framework_experiments" / name).read_bytes()).hexdigest()
        for name in ["build_manuscript_assets.py", "supplement_figures.py"]
    },
    "layout_review": "Separate root PDF review; this program does not compile LaTeX.",
}
name = "framework_figure_equivalence.json" if args.figures_only else "analysis_translation_checks.json"
(REV / name).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"sections_passed": list(sections), "figures_matched": list(english_plots), "all_checks_passed": True}, ensure_ascii=False, indent=2))
