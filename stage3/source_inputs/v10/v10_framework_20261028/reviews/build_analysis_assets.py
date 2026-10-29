"""Current P1/P2/P3 authoring wrapper; no numerical experiment is run."""
from pathlib import Path
import sys

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT / "reproduction/framework_experiments"))
from build_manuscript_assets import build

if __name__ == "__main__":
    build()
