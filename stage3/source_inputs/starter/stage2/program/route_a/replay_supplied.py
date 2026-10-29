"""Re-run supplied route-A tests in independent copies; sources remain read-only."""
from pathlib import Path
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "stage2/results/route_a"
SOURCES = ROOT / "stage2/sources"
LATEST = SOURCES / "integration_latest/v10_birkhoff_20261028"
OLDER = SOURCES / "integration_older_copy2/v10_framework_20261028"
B = SOURCES / "birkhoff_supplied"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def hashes(directory):
    return {str(p.relative_to(directory)): digest(p) for p in sorted(directory.rglob("*")) if p.is_file()}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = {"latest": hashes(LATEST), "older": hashes(OLDER), "supplied_B": hashes(B)}
    dst = OUT / "supplied_replay"
    dst.mkdir(exist_ok=True)
    shutil.copytree(LATEST / "reproduction", dst / "reproduction", dirs_exist_ok=True)
    shutil.copytree(B, dst / "birkhoff_supplied", dirs_exist_ok=True)
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    commands = [
        ("B_general", dst / "birkhoff_supplied/verify_general_birkhoff.py"),
        ("B_v10_special", dst / "birkhoff_supplied/verify_v10_special_case.py"),
        ("latest_framework", dst / "reproduction/framework_experiments/run_all.py"),
        ("latest_general", dst / "reproduction/general_birkhoff_experiments/run_all.py"),
    ]
    results = []
    for name, script in commands:
        logfile = OUT / ("replay_" + name + ".log")
        start = time.perf_counter()
        print("RUN", name, flush=True)
        with logfile.open("w") as log:
            log.write("COMMAND: " + repr([sys.executable, str(script)]) + "\n")
            log.flush()
            proc = subprocess.run([sys.executable, str(script)], cwd=dst, env=env, stdout=log, stderr=subprocess.STDOUT)
        row = {"name": name, "command": [sys.executable, str(script)], "returncode": proc.returncode,
               "wall_seconds": time.perf_counter() - start, "log": str(logfile.relative_to(ROOT))}
        results.append(row)
        print(json.dumps(row), flush=True)
        if proc.returncode:
            print(logfile.read_text()[-8000:], flush=True)
            break
    after = {"latest": hashes(LATEST), "older": hashes(OLDER), "supplied_B": hashes(B)}
    report = {"runs": results, "source_unchanged": before == after, "source_sha256": before,
              "python": sys.version, "platform": platform.platform(),
              "scope": "Independent-copy reruns, not new physical validation. Wall time includes test diagnostics and reference solves."}
    (OUT / "supplied_replay_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert before == after, "Read-only source files changed"
    assert len(results) == len(commands) and all(r["returncode"] == 0 for r in results), "A supplied replay failed; inspect logs"

if __name__ == "__main__":
    main()
