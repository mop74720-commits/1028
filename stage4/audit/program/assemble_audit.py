"""Assemble granular inheritance rows and verify unchanged frozen sources.

This validates evidence packaging, not mathematical correctness. Free-text status
values deliberately preserve scope instead of collapsing six levels to booleans.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / 'stage4/audit'
COLUMNS = ('id,item_kind,original_location,mathematical_item,old_v10,'
           'general_birkhoff,stage2,stage3,latest_manuscript_or_notes,source_code,'
           'evidence,material_exists,mentioned_in_latest,full_derivation_inherited,'
           'algorithm_reused,verified_on_3d,generalization_proved,proof_status,'
           'defect,repair,priority').split(',')
DELIVERABLES = ['1025_master_route.md', 'full_inheritance_matrix.csv',
                'missing_or_weakened_results.md', 'birkhoff_full_audit.md',
                'chnn_kam_inheritance.md', 'physical_and_control_audit.md',
                'proof_errors_and_corrections.md', 'reproduction_and_tests.md',
                'proposed_complete_manuscript_structure.md', 'final_verdict.md']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows, parts = [], {}
    for path in sorted((AUDIT / 'matrix_parts').glob('*.csv')):
        with path.open(encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)
            assert reader.fieldnames == COLUMNS, (path, reader.fieldnames)
            added = list(reader)
        assert added, path
        for row in added:
            assert all(row[c] and row[c].strip() for c in COLUMNS), row['id']
        rows.extend(added)
        parts[path.name] = len(added)
    assert len(rows) == len({row['id'] for row in rows})
    with (AUDIT / 'full_inheritance_matrix.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Validate explicit repository-relative references, retaining intentional
    # missing historical assets as warnings to be reviewed, never inventing them.
    paths, unresolved = set(), []
    for row in rows:
        for column, value in row.items():
            for token in re.findall(r'stage[34]/[^\s;|,`（）()，；]+', value):
                token = token.rstrip('.。')
                path_text = re.split(r'[:#]', token)[0]
                path = ROOT / path_text
                if path.exists():
                    paths.add(path_text)
                    match = re.search(r':(\d+)', token)
                    if match and path.is_file() and path.suffix in {'.md', '.py', '.tex', '.txt'}:
                        lineno = int(match.group(1))
                        count = len(path.read_text().splitlines())
                        if lineno > count:
                            unresolved.append(dict(id=row['id'], column=column, reference=token,
                                                   reason=f'line {lineno} exceeds {count}'))
                else:
                    unresolved.append(dict(id=row['id'], column=column, reference=token,
                                           reason='not a single existing path; inspect grouping or explicit missing asset'))
    provenance = json.loads((AUDIT / 'results/start_provenance.json').read_text())
    changes = [name for name, sha in provenance['tracked_files_before'].items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != sha]
    assert not changes, changes
    assert all((AUDIT / name).is_file() for name in DELIVERABLES)
    inventory = json.loads((ROOT / 'stage3/results/material_inventory.json').read_text())
    archive_checks = []
    for record in inventory['archives']:
        archive_path = ROOT / record['path']
        assert digest(archive_path) == record['sha256'], archive_path
        count = 0
        with ZipFile(archive_path) as archive:
            for entry in record['entries']:
                raw = archive.read(entry['path'])  # Includes ZIP CRC verification.
                assert hashlib.sha256(raw).hexdigest() == entry['sha256']
                extracted = ROOT / record['extracted_root'] / entry['path']
                assert extracted.read_bytes() == raw, extracted
                count += 1
        archive_checks.append(dict(path=record['path'], matched_files=count,
                                   archive_sha256=record['sha256'], crc_and_extracted_bytes='passed'))
    remote_texts = json.loads((AUDIT / 'external_v10/manifest.json').read_text())
    retrieved = [item for item in remote_texts['files'] if item['status'] == 'downloaded']
    unavailable = [item for item in remote_texts['files'] if item['status'] != 'downloaded']
    for item in retrieved:
        assert digest(AUDIT / 'external_v10' / item['path']) == item['sha256'], item['path']
    report = dict(status='assembled; reference warnings require inspection' if unresolved else 'passed',
                  audited_head=provenance['audit_start_head'], rows=len(rows), columns=COLUMNS,
                  parts=parts, priorities=dict(Counter(row['priority'] for row in rows)),
                  six_status_fields=COLUMNS[11:17], checked_existing_paths=len(paths),
                  reference_warnings=unresolved,
                  unchanged_start_tracked_files=len(provenance['tracked_files_before']),
                  changed_start_files=changes, required_deliverables=DELIVERABLES,
                  archive_checks=archive_checks,
                  external_fixed_commit=remote_texts['fixed_commit'],
                  external_text_files_hash_verified=len(retrieved),
                  external_unsuccessful_requests=unavailable,
                  packaging_correction='Initial validator assumed every manifest entry was downloaded; '
                  'learning_proof.tex is a recorded failed request. Corrected to verify downloaded '
                  'entries and retain unsuccessful requests explicitly; no missing file fabricated.',
                  scope='Packaging and source-preservation validation, not proof certification.')
    (AUDIT / 'results/delivery_validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'rows', 'parts', 'checked_existing_paths',
                                           'reference_warnings', 'unchanged_start_tracked_files')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
