"""Validate and join mathematical annotations to SHA-identified TeX locations.

Coverage counts describe review bookkeeping, never proof completeness.
"""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from materials import resolve_source

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
REQUIRED = ['topic','original_1025','old_v10','general_birkhoff','stage4',
            'stage5_code','stage5_proof','stage5_results','fusion_verdict',
            'stage5_inheritance','stage6_action','new_code','tests','evidence',
            'remaining','review_note','material_exists','mentioned',
            'derivation_inherited','algorithm_reused','verified_on_3d',
            'generalization_proved']
OWNERS = {
    'theory': ['structure','supp_general_birkhoff','supp_structure'],
    'algorithms': ['controlled_analysis','general_birkhoff_results','supp_general_experiments'],
    'kam': ['analysis','kam','route_interfaces','supp_route_budgets','route_budget_table','route_budget_main_values'],
    'physics': ['mechanics','supp_mechanics','background','application'],
    'history': ['supp_experiments','extension_tracking_theory','extension_tracking_results',
                'tracking_main','conclusion','endmatter','references'],
}


def cell(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True) if isinstance(value,(list,dict)) else str(value)


def write_csv(path, rows, fields):
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        writer.writerows({k:cell(row.get(k,'')) for k in fields} for row in rows)


def main():
    source=resolve_source()
    index=json.loads((BASE/'results/manuscript_index.json').read_text())
    annotated={};counts={}
    for owner in OWNERS:
        path=BASE/'annotations'/f'{owner}.json'
        rows=json.loads(path.read_text())['rows'];counts[owner]=len(rows)
        for row in rows:
            assert row['id'] not in annotated, ('duplicate',row['id'])
            assert not set(REQUIRED)-row.keys(), ('missing fields',row['id'],set(REQUIRED)-row.keys())
            annotated[row['id']]=(owner,row)
    expected={u['id'] for u in index['review_units']}
    assert set(annotated)==expected, dict(missing=sorted(expected-set(annotated)),extra=sorted(set(annotated)-expected))
    combined=[]
    for unit in index['review_units']:
        owner,row=annotated[unit['id']]
        assert Path(unit['source']).stem in OWNERS[owner]
        if 'source' in row: assert row['source']==unit['source']
        if 'line_start' in row: assert row['line_start']==unit['line_start']
        combined.append(dict(unit,reviewer=owner,**{k:row[k] for k in REQUIRED}))
    fields=['id','source','language','line_start','line_end','kind','labels','sha256','archive',
            'archive_sha256','reviewer',*REQUIRED,'tex']
    write_csv(BASE/'full_comparison.csv',combined,fields)
    bysource=Counter(u['source'] for u in combined)
    chapters=[]
    for chapter in index['chapters']:
        name=chapter['source'];data=(source/name).read_bytes()
        assert hashlib.sha256(data).hexdigest()==chapter['sha256']
        assert bysource[name]==chapter['review_units']
        owner=next(k for k,v in OWNERS.items() if Path(name).stem in v)
        chapters.append(dict(chapter,reviewer=owner,reviewed_units=bysource[name],
            analysis=f'stage6/fusion_reconciliation/notes/{owner}_reconciliation.md',
            status='chapter_read_and_annotated; zero-display chapters reviewed in linked note',
            proof_scope='Individual rows retain conditional, historical and unfinished states.'))
    write_csv(BASE/'chapter_coverage.csv',chapters,['source','language','sha256','lines','review_units',
              'reviewed_units','inline_context_units','headings','reviewer','analysis','status','proof_scope'])
    report=dict(status='passed',archive_sha256=index['archive_sha256'],chapters=len(chapters),
        review_units=len(combined),inline_context_units=len(index['inline_context']),counts_by_reviewer=counts,
        labels_are_original=True,missing=[],duplicates=[],
        supplementary_reading=['english/main.tex','english/supplement.tex','chinese/main.tex',
            'chinese/supplement.tex','delivery_report/report.tex','ARCHIVE_PROVENANCE.txt'],
        scope='46 bilingual section files; displayed formulas, theorem-like blocks and tables are exact indexed units. '
              '4464 inline expressions are contextual anchors, not independent certified theorems. '
              'Chapter reading includes surrounding hypotheses, proofs and prose. Coverage is not acceptance or generalization.')
    (BASE/'results/comparison_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    main()
