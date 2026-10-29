"""Verify the evidence index against the untouched ZIP/XML source documents."""
from pathlib import Path
from zipfile import ZipFile
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parents[1]/'source_omml'
MATH='{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'
STRUCTURE={'f','sSub','sSup','sSubSup','m','eqArr','nary','rad','d',
           'limLow','limUpp','acc','bar','groupChr'}
out={}
for name in ('original1025','stage1review'):
    data=json.loads((BASE/f'{name}_indexed.json').read_text())
    raw=(BASE/f'{name}_document.xml').read_bytes()
    with ZipFile(ROOT/data['source']) as archive:
        assert archive.read('word/document.xml')==raw
        other=[]
        for member in archive.namelist():
            if member.startswith('word/') and member.endswith('.xml') and member!='word/document.xml':
                count=len(ET.fromstring(archive.read(member)).findall('.//'+MATH))
                if count: other.append([member,count])
    assert len(data['math_objects'])==data['math_count']
    assert len({m['id'] for m in data['math_objects']})==data['math_count']
    assert all(ET.fromstring(m['omml_xml']).tag==MATH for m in data['math_objects'])
    lines=(BASE/f'{name}_reading.txt').read_text().splitlines()
    assert len(lines)==data['paragraph_count']
    assert all(line.startswith(f'{name}-p{i:04d} ') for i,line in enumerate(lines,1))
    out[name]={k:data[k] for k in ('source','source_sha256','document_xml_sha256',
                                'paragraph_count','math_count')}
    out[name].update(raw_document_matches_docx=True,all_math_xml_parseable=True,
                     unique_math_ids=True,reading_line_equals_paragraph_index=True,
                     other_word_parts_with_math=other,
                     structural_tag_counts={k:v for k,v in data['math_tag_counts'].items()
                                            if k in STRUCTURE})
out['commands']=['python stage4/audit/program/extract_omml.py',
                 'python stage4/audit/program/verify_omml.py']
original=json.loads((BASE/'original1025_indexed.json').read_text())
out['critical_original_anchors']=[
    {key:original['math_objects'][number-1][key]
     for key in ('id','paragraph','rendering','structure_tags')}
    for number in (24,31,194,195,399,400,408,417,434,442,505,509,530,541,565,570)
]
out['scope']='OMML preservation/index verification, not a mathematical proof checker or full Word typographical rendering.'
(BASE/'extraction_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('PASS: raw XML identity, all math objects, unique IDs, paragraph lines, other document parts')
