"""Check citations, cross references and translated mathematical content."""
from pathlib import Path
import hashlib
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
LABEL = re.compile(r"\\label\{([^}]+)\}")
REFERENCE = re.compile(r"\\(?:eqref|ref|pageref)\{([^}]+)\}")
CITATION = re.compile(r"\\cite[a-zA-Z]*(?:\[[^\]]*\])*\{([^}]+)\}")
DISPLAY = re.compile(
    r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}(.*?)\\end\{\1\}", re.S
)
UNNUMBERED_DISPLAY = re.compile(r"\\\[(.*?)\\\]", re.S)


def without_comments(text):
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def math_key(text):
    text = re.sub(r"\\text\{[^{}]*\}", r"\\text{}", text)
    return re.sub(r"\s+", "", text)


def analyze(language):
    folder = ROOT / language
    files = [folder / "main.tex", folder / "supplement.tex"] + sorted((folder / "sections").glob("*.tex"))
    labels, refs, cites = [], [], set()
    for path in files:
        text = without_comments(path.read_text(encoding="utf-8"))
        labels.extend(LABEL.findall(text))
        refs.extend(REFERENCE.findall(text))
        for item in CITATION.findall(text):
            cites.update(key.strip() for key in item.split(","))
    bibliography = (folder / "sections/references.tex").read_text(encoding="utf-8")
    keys = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", bibliography))
    duplicate = [key for key, count in Counter(labels).items() if count > 1]
    missing_refs = sorted(set(refs) - set(labels))
    missing_cites = sorted(cites - keys)
    assert not duplicate, (language, "duplicate labels", duplicate)
    assert not missing_refs, (language, "unresolved references", missing_refs)
    assert not missing_cites, (language, "missing citations", missing_cites)
    return {"labels": sorted(labels), "label_count": len(labels),
            "citation_count": len(cites), "missing_references": missing_refs,
            "missing_citations": missing_cites, "duplicate_labels": duplicate}


def main():
    report = {language: analyze(language) for language in ("english", "chinese")}
    assert report["english"]["labels"] == report["chinese"]["labels"], "Translation label mismatch"
    comparisons = []
    for english in sorted((ROOT / "english/sections").glob("*.tex")):
        chinese = ROOT / "chinese/sections" / english.name
        assert chinese.exists(), f"Missing translation: {english.name}"
        left = without_comments(english.read_text(encoding="utf-8"))
        right = without_comments(chinese.read_text(encoding="utf-8"))
        le = [math_key(content) for _, content in DISPLAY.findall(left)]
        ri = [math_key(content) for _, content in DISPLAY.findall(right)]
        lu = [math_key(content) for content in UNNUMBERED_DISPLAY.findall(left)]
        ru = [math_key(content) for content in UNNUMBERED_DISPLAY.findall(right)]
        different = [i + 1 for i, (a, b) in enumerate(zip(le, ri)) if a != b]
        comparisons.append({"file": english.name, "english_display_count": len(le),
                            "chinese_display_count": len(ri), "different_display_blocks": different,
                            "english_unnumbered_display_count": len(lu),
                            "chinese_unnumbered_display_count": len(ru),
                            "unnumbered_displays_equal": lu == ru,
                            "english_sha256": hashlib.sha256(english.read_bytes()).hexdigest(),
                            "chinese_sha256": hashlib.sha256(chinese.read_bytes()).hexdigest()})
        assert len(le) == len(ri), (english.name, "Display equation count differs")
        assert not different, (english.name, "Mathematical content differs", different)
        assert lu == ru, (english.name, "Unnumbered display mathematics differs")
    freeze = json.loads((ROOT / "provenance/english_master_freeze.json").read_text())
    for relative, digest in freeze["files"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative + " changed after English freeze"
    report["english_master_matches_final_reviewed_freeze"] = True
    report["post_freeze_reference_corrections"] = freeze.get("post_freeze_reference_corrections")
    # Page numbers may differ across languages; equation and theorem numbers may not.
    def numbers(language, document):
        content = (ROOT / language / (document + ".aux")).read_text(encoding="utf-8")
        return {key: value for key, value in re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", content)
                if key not in ("FirstPage", "LastPage")}
    for document in ("main", "supplement"):
        assert numbers("english", document) == numbers("chinese", document), document + " numbering differs"
    for language in ("english", "chinese"):
        for document in ("main", "supplement"):
            content = (ROOT / language / (document + ".log")).read_text(errors="replace")
            bad = [line for line in content.splitlines()
                   if re.search(r"undefined|multiply defined|Overfull|Missing character", line)]
            assert not bad, (language, document, bad)
    report["mathematical_content_comparison"] = comparisons
    report["all_checks_passed"] = True
    destination = ROOT / "provenance/manuscript_validation.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Cross-language labels, numbered statements, display equations and citations agree.")
    print("All four final compiler logs have no unresolved references, overflow or missing glyphs.")


if __name__ == "__main__":
    main()
