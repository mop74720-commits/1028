"""Byte and text comparisons of actual supplied sources; no semantic shortcuts."""
from pathlib import Path
import csv
import difflib
import hashlib
import json
import re
from materials import resolve_source, ROOT, BASE


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    fusion = resolve_source()
    old = ROOT/'stage3/source_inputs/v10/v10_framework_20261028'
    diffs = BASE/'results/source_diffs'; diffs.mkdir(parents=True,exist_ok=True)
    rows = []
    for language in ('english','chinese'):
        for current in sorted((fusion/language/'sections').glob('*.tex')):
            relative = current.relative_to(fusion)
            previous = old/relative
            text = current.read_text(); before = previous.read_text() if previous.exists() else ''
            matcher = difflib.SequenceMatcher(None,before.splitlines(),text.splitlines(),autojunk=False)
            operations = matcher.get_opcodes()
            added = sum(j2-j1 for tag,i1,i2,j1,j2 in operations if tag in ('insert','replace'))
            removed = sum(i2-i1 for tag,i1,i2,j1,j2 in operations if tag in ('delete','replace'))
            before_labels = set(re.findall(r'\\label\{([^}]+)\}',before))
            after_labels = set(re.findall(r'\\label\{([^}]+)\}',text))
            patch = ''.join(difflib.unified_diff(before.splitlines(True),text.splitlines(True),
                fromfile=str(previous.relative_to(ROOT)),tofile='fusion_archive::'+str(relative)))
            patch_path = diffs/(language+'_'+current.stem+'.diff')
            patch_path.write_text(patch)
            rows.append(dict(source=str(relative),old_source=str(previous.relative_to(ROOT)),
                old_exists=previous.exists(),byte_identical=previous.exists() and current.read_bytes()==previous.read_bytes(),
                current_sha256=digest(current),old_sha256=digest(previous) if previous.exists() else '',
                added_lines=added,removed_lines=removed,added_labels=';'.join(sorted(after_labels-before_labels)),
                removed_labels=';'.join(sorted(before_labels-after_labels)),diff=str(patch_path.relative_to(ROOT)),
                interpretation='Text provenance only; semantic validity and inheritance assessed in formula annotations.'))
    with (BASE/'chapter_source_comparison.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    identities=[]
    for srcprefix, oldprefix in [
        (fusion/'provenance/material_A_sources',old),
        (fusion/'provenance/material_B_original',ROOT/'stage3/source_inputs/birkhoff')]:
        for path in sorted(srcprefix.rglob('*')):
            if not path.is_file():continue
            counterpart=oldprefix/path.relative_to(srcprefix)
            identities.append(dict(archive_path=str(path.relative_to(fusion)),
                repository_path=str(counterpart.relative_to(ROOT)),counterpart_exists=counterpart.exists(),
                byte_identical=counterpart.exists() and path.read_bytes()==counterpart.read_bytes(),
                archive_sha256=digest(path),repository_sha256=digest(counterpart) if counterpart.exists() else None))
    (BASE/'results/source_lineage.json').write_text(json.dumps(dict(chapters=rows,
        embedded_historical_sources=identities,scope='Unchanged bytes do not prove a theorem; changed bytes do not by themselves show a mathematical conflict.'),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(chapters=len(rows),unchanged_chapters=sum(x['byte_identical'] for x in rows),
        historical_counterparts=len(identities),historical_identical=sum(x['byte_identical'] for x in identities))))


if __name__=='__main__':main()
