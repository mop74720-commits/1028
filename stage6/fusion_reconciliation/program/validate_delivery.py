"""Packaging/provenance checks only; mathematical tests have separate logs."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile
from materials import resolve_source

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]


def main():
    resolve_source()  # Checks every extracted source hash; recovers if absent.
    original=json.loads((BASE/'results/materials.json').read_text())
    changed=[p for p,h in original['frozen_sha256'].items()
             if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    assert not changed, changed
    # Failure JSON is kept and validated as data, never relabeled successful.
    def reject(value): raise ValueError('Nonfinite JSON constant: '+value)
    json_files=[]; npzs=[]; python_files=[]
    for path in sorted(BASE.rglob('*.json')):
        json.loads(path.read_text(),parse_constant=reject)
        json_files.append(str(path.relative_to(ROOT)))
    for path in sorted(BASE.rglob('*.npz')):
        with ZipFile(path) as archive: assert archive.testzip() is None, str(path)
        npzs.append(str(path.relative_to(ROOT)))
    for path in sorted(BASE.rglob('*.py')):
        ast.parse(path.read_text(),filename=str(path))
        python_files.append(str(path.relative_to(ROOT)))
    tests=json.loads((BASE/'results/tests/latest_all.json').read_text())
    assert tests['status']=='passed'
    # Validate stable numerical modules against the actual final test run.
    changed_numerical=[]
    for name,old in tests['source_sha256'].items():
        if name.startswith('stage6/') and (('/tests/' in name) or Path(name).name in [
            'fusion_budget.py','fusion_physics.py','fusion_theory.py',
            'nonautonomous_transport.py','learned_reference_tracking.py']):
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=old:changed_numerical.append(name)
    assert not changed_numerical, changed_numerical
    comparison=json.loads((BASE/'results/comparison_validation.json').read_text())
    assert comparison['status']=='passed' and comparison['review_units']==582
    report=dict(status='passed',command=sys.argv,checked_utc=datetime.now(timezone.utc).isoformat(),
        source_head=original['start_head'],current_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        frozen_files=len(original['frozen_sha256']),frozen_changed=changed,
        strict_json_count=len(json_files),npz_crc_count=len(npzs),python_ast_count=len(python_files),
        numerical_modules_match_final_tests=True,final_tests=tests['total_tests'],
        review_units=comparison['review_units'],source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ['program','tests','proofs','notes'] for p in sorted((BASE/folder).glob('*')) if p.is_file()},
        scope='File integrity and evidence packaging only; no new dynamical, physical or KAM certificate.')
    (BASE/'results/delivery_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},ensure_ascii=False))


if __name__=='__main__':main()
