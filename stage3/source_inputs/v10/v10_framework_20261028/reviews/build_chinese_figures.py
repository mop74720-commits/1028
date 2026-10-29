"""Render all four current numerical figures with Chinese labels only.

This does not edit English text or figures and does not rerun experiments.
"""
from pathlib import Path
import sys

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT / "reproduction/framework_experiments"))
from build_manuscript_assets import render_figures

if __name__ == "__main__":
    figures = render_figures("zh")
    print("Rendered Chinese figures:", ", ".join(figures))
