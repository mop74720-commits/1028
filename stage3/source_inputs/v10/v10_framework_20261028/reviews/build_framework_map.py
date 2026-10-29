"""Resolve the supplied framework's component maps against the compiled article."""
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reviews"


def read_table(name):
    with (REVIEWS / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def main():
    labels = {}
    for name in ("main", "supplement"):
        path = ROOT / "english" / (name + "_xr.aux")
        for label, number, page in re.findall(
            r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}", path.read_text()
        ):
            labels[label] = {"number": number, "page": page, "document": name}

    rows = []
    for part, filename in (
        ("Mechanics and application", "framework_mechanics_map.tsv"),
        ("Discretization and theory", "framework_theory_map.tsv"),
        ("Numerical verification", "framework_numerics_map.tsv"),
    ):
        for item in read_table(filename):
            mechanics = "source_anchor" in item
            references = (item["destination_labels"] if mechanics else
                          ";".join((item["new_main_location"], item["new_supplement_location"])))
            resolved = []
            for key in re.split(r"[;,]", references):
                key = key.strip()
                if not key or key.lower() in {"none", "n/a", "-"}:
                    continue
                if key not in labels:
                    raise ValueError(f"Unresolved framework destination {key!r} in {filename}")
                value = labels[key]
                resolved.append(f"{value['document']} {value['number']} (p. {value['page']}; {key})")
            rows.append({
                "component": part,
                "source_page": item["pdf_page"] if mechanics else item["source_pages"],
                "source_section_or_equations": item["source_anchor"] if mechanics else
                    item["source_section"] + "; " + item["source_equations"],
                "integrated_destinations": "; ".join(resolved),
                "change_or_status": item["change"] if mechanics else item["integration_status"],
                "scope_and_evidence": item["completion_status"] if mechanics else item["scope"],
                "source_mapping": filename,
            })
    destination = REVIEWS / "framework_integration_map.tsv"
    with destination.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "source": "provenance/source_direction_one_framework.pdf",
        "component_count": len(rows),
        "label_count": len(labels),
        "all_destinations_resolved": True,
        "mapping": str(destination.relative_to(ROOT)),
        "purpose": "Source-framework to integrated-v10 mapping; status distinguishes results from protocols.",
    }
    (ROOT / "provenance" / "framework_mapping_validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
