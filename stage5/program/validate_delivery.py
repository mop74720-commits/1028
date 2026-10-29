"""Check provenance, ledger completeness and parseability, not research success."""
from pathlib import Path
import ast
import csv
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]


def load_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    base = ROOT / 'stage5'
    original = load_csv(ROOT / 'stage4/audit/full_inheritance_matrix.csv')
    updated = load_csv(base / 'inheritance_update.csv')
    repairs = load_csv(base / 'repair_status.csv')
    old = {row['id']: row for row in original}
    new = {row['id']: row for row in updated}
    assert len(new) == 115 and old.keys() == new.keys()
    assert all(new[key][column] == value for key, row in old.items() for column, value in row.items())
    repair_id_column = next(key for key in repairs[0] if repairs[0][key] == 'E01')
    assert {row[repair_id_column] for row in repairs} == {f'E{i:02d}' for i in range(1, 17)}
    snapshot = json.loads((base / 'results/start_provenance.json').read_text())
    changed = [name for name, sha in snapshot['frozen_files'].items()
               if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha]
    assert not changed, changed
    syntax = []
    for directory in ('program', 'tests'):
        for path in (base / directory).glob('*.py'):
            ast.parse(path.read_text(), filename=str(path))
            syntax.append(str(path.relative_to(ROOT)))
    invalid_json = []
    json_count = 0
    def reject_nonfinite(value):
        raise ValueError('Non-standard JSON numeric constant: ' + value)
    for path in (base / 'results').rglob('*.json'):
        if path.name == 'delivery_validation.json':
            continue
        json_count += 1
        try:
            json.loads(path.read_text(), parse_constant=reject_nonfinite)
        except (ValueError, OSError) as exc:
            invalid_json.append(dict(path=str(path.relative_to(ROOT)), error=str(exc)))
    report = dict(checked_utc=datetime.now(timezone.utc).isoformat(),
                  status='passed' if not invalid_json else 'failed',
                  original_inheritance_rows_preserved=115, error_ids_preserved=16,
                  frozen_files_unchanged=len(snapshot['frozen_files']), changed_frozen_files=changed,
                  python_syntax_checked=syntax, json_files_checked=json_count,
                  invalid_json=invalid_json,
                  meaning='Packaging validation only. Scientific acceptance and remaining gaps are reported separately.')
    (base / 'results/delivery_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'original_inheritance_rows_preserved',
                    'error_ids_preserved', 'frozen_files_unchanged', 'json_files_checked', 'invalid_json')}, indent=2))
    assert not invalid_json, invalid_json


if __name__ == '__main__':
    main()
