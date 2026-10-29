"""Write only the three Chinese numerical inputs from frozen English.

All resources are package-relative. Reused translations are stored with their
English block hashes; no earlier workspace or external project is required.
"""
from pathlib import Path
import hashlib
import json
import re

from framework_translation_overrides import TRANSLATIONS, REPLACEMENTS

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "reviews"
reuse = json.loads((REV / "numeric_translation_reuse.json").read_text())
frozen = json.loads((ROOT / "provenance/english_master_freeze.json").read_text())["files"]
display_pattern = r"\\begin\{(equation\*?|align\*?)\}.*?\\end\{\1\}"
record = {}

for name in ["analysis.tex", "supp_experiments.tex", "extension_tracking_results.tex"]:
    en_path = ROOT / "english/sections" / name
    relative = str(en_path.relative_to(ROOT))
    assert hashlib.sha256(en_path.read_bytes()).hexdigest() == frozen[relative], relative
    original = en_path.read_text()
    blocks = re.split(r"\n\s*\n", original)
    translated = []
    counts = {"reused": 0, "translated_prose": 0, "translated_labels": 0}
    for i, en in enumerate(blocks):
        key = (name, i)
        if key in TRANSLATIONS:
            zh = TRANSLATIONS[key]
            math = [m.group() for m in re.finditer(display_pattern, en, re.S)]
            for j, block in enumerate(math):
                marker = f"@DISPLAY{j}@"
                assert zh.count(marker) == 1, key
                zh = zh.replace(marker, block)
            assert "@DISPLAY" not in zh, key
            counts["translated_prose"] += 1
        elif key in REPLACEMENTS:
            zh = en
            for old, new in REPLACEMENTS[key]:
                assert old in zh, (key, old)
                zh = zh.replace(old, new)
            counts["translated_labels"] += 1
        else:
            previous = reuse[f"{name}:{i}"]
            assert hashlib.sha256(en.encode()).hexdigest() == previous["en_sha256"], key
            zh = previous["zh"]
            counts["reused"] += 1
        # Root's final Chinese term convention supersedes the previous version.
        zh = zh.replace("名义", "标称")
        translated.append(zh)
    content = "\n\n".join(translated)
    if original.endswith("\n") and not content.endswith("\n"):
        content += "\n"
    out = ROOT / "chinese/sections" / name
    out.write_text(content)
    record[name] = {"english_sha256": frozen[relative],
                    "chinese_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                    "block_counts": counts}
(REV / "framework_translation_generation.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
print(json.dumps(record, ensure_ascii=False, indent=2))
