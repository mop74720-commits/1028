"""Package this session's v10 evidence without redistributing upstream inputs.

Run from the project root with Python 3.  This script only copies existing
evidence and checks hashes; it does not run the scientific experiments.
"""
from pathlib import Path
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone

STAGE2 = Path(__file__).resolve().parent.parent
DEST = STAGE2 / "evidence_v10"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    included, excluded, reviewed = [], [], Counter()
    s1 = STAGE2 / "runs/v10_s1"
    original = {}
    for manifest in ["input_copy_manifest.json", "extended_input_copy_manifest.json"]:
        for item in json.loads((s1 / manifest).read_text()):
            rel = item.get("path", item.get("relative_path"))
            original["reproducibility/" + rel] = {
                "manifest": manifest,
                "source_sha256": item["source_sha256"],
                "initial_copy_sha256": item["copy_sha256"],
            }
    regenerated = {
        "reproducibility/mainline_completion/integral_certificate/comsol_integral_certificate.json",
        "reproducibility/mainline_completion/integral_certificate/comsol_integral_certificate_exact_curves.json",
        "reproducibility/mainline_completion/integral_certificate/torus_COMSOL_integral_certificate.json",
    }
    training_inputs = {
        Path(item["copy"]).relative_to("stage2/runs/v10_training").as_posix(): item
        for item in json.loads((STAGE2 / "runs/v10_training/input_manifest.json").read_text())
    }

    def record(source, target, category, reason=None, identity=None):
        entry = {
            "source": source.relative_to(STAGE2).as_posix(),
            "bytes": source.stat().st_size,
            "sha256": sha(source),
            "classification": category,
        }
        if reason:
            entry["reason"] = reason
        if identity:
            entry["input_identity"] = identity
        if target is None:
            excluded.append(entry)
        else:
            out = DEST / target
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, out)
            assert sha(out) == entry["sha256"], str(out)
            entry["evidence_path"] = target
            included.append(entry)

    roots = [
        ("v10_s1", STAGE2 / "runs/v10_s1"),
        ("v10_training", STAGE2 / "runs/v10_training"),
        ("v10_s2", STAGE2 / "runs/v10_s2"),
        ("reuse_guard", STAGE2 / "runs/learning_reuse_guard"),
        ("source_metadata", STAGE2 / "sources/v10_metadata"),
    ]
    for group, root in roots:
        for source in sorted(root.rglob("*")):
            if not source.is_file():
                continue
            reviewed[group] += 1
            rel = source.relative_to(root).as_posix()
            target = group + "/" + rel
            if any(p in {"__pycache__", "numba_cache", "matplotlib_cache"} for p in source.parts):
                record(source, None, "runtime_cache", "Reproducible runtime cache, not scientific evidence.")
            elif group == "v10_s1" and rel in original and rel not in regenerated:
                assert sha(source) == original[rel]["initial_copy_sha256"], rel
                record(source, None, "upstream_input", "Unchanged upstream code/data/history/weights; exact identity retained in input manifest.", original[rel])
            elif group == "v10_s1" and rel in regenerated:
                record(source, target, "newly_regenerated_result", "Written by the recorded rerun. Exact-curves JSON is deterministically identical to the input copy; it is retained as a regenerated derived result.", original[rel])
            elif group == "v10_s1" and rel.endswith("frozen_comsol7_rechecked_modal_model.npz"):
                record(source, target, "new_certificate_modal_export", "New export from the frozen modal constructor; eight numerical arrays are identical to the original modal input, as documented by frozen_modal_identity.json. Not a newly identified model or learned weight file.")
            elif group == "v10_training" and rel in training_inputs:
                assert sha(source) == training_inputs[rel]["sha256"], rel
                record(source, None, "upstream_input", "Copied original code or training/test arrays; not regenerated in this run.", training_inputs[rel])
            elif group == "v10_training" and rel.startswith("refits/"):
                record(source, target, "newly_fitted_output", "Newly refitted coefficients/readouts and new predictions; retained because these are generated outputs, not original frozen input weights.")
            elif group == "reuse_guard" and "/" in rel and rel != "valid/rom_metadata.json":
                record(source, None, "disposable_guard_input_fixture", "Copied or deliberately perturbed test input; omitted to avoid redistributing repeated training data. Six-case outcomes and audit script are included.")
            elif group == "reuse_guard" and rel == "valid/rom_metadata.json":
                record(source, target, "new_guard_metadata", "Small metadata file written after successful identity validation; training was stopped by the test sentinel.")
            elif group == "source_metadata":
                record(source, target, "source_identity_metadata", "Official API response, archive inventory or locally generated hash manifest; no upstream scientific source/data payload.")
            else:
                category = "audit_script" if source.suffix == ".py" else "new_result_or_run_record"
                if "input" in source.name and "manifest" in source.name:
                    category = "input_identity_manifest"
                record(source, target, category)

    for name in ["learning_reuse_guard_patch.json", "learning_trained_source_snapshot.json"]:
        record(STAGE2 / "notes" / name, "reuse_guard/" + name, "patch_identity_record")
    record(Path(__file__), "package_evidence.py", "packaging_audit_script")

    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "This session's original-v10 recomputation evidence and the six-case data-reuse guard audit; not new-3D model certification.",
        "all_reviewed_run_files_classified": True,
        "reviewed_file_count_by_source": dict(reviewed),
        "included_count": len(included),
        "included_bytes": sum(x["bytes"] for x in included),
        "excluded_count": len(excluded),
        "excluded_bytes": sum(x["bytes"] for x in excluded),
        "included": included,
    }
    (DEST / "evidence_manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    (DEST / "excluded_inputs_and_caches.json").write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "included"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
