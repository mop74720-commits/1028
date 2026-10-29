"""Preserve raw OMML and produce an indexed structural reading of both DOCX files.

The original XML and every raw math object remain authoritative. The rendering
retains fraction, script, delimiter, matrix, limit and accent structure; it is a
reading aid rather than a claim of exact Word typography or a proof checker.
"""
from pathlib import Path
from zipfile import ZipFile
import collections
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]/'source_omml'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
for prefix,uri in NS.items():ET.register_namespace(prefix,uri)

def tag(e):return e.tag.split('}')[-1]
def child(e,name):return e.find('m:'+name,NS)
def value(e,name,default=''):
    x=e.find('.//m:'+name,NS)
    return default if x is None else x.get('{'+NS['m']+'}val',default)
def render(e):
    if e is None:return ''
    t=tag(e)
    if t=='t':return e.text or ''
    if t.endswith('Pr'):return ''
    r=lambda n:render(child(e,n))
    if t=='f':return r'\frac{'+r('num')+'}{'+r('den')+'}'
    if t=='sSub':return '{'+r('e')+'}_{'+r('sub')+'}'
    if t=='sSup':return '{'+r('e')+'}^{'+r('sup')+'}'
    if t=='sSubSup':return '{'+r('e')+'}_{'+r('sub')+'}^{'+r('sup')+'}'
    if t=='rad':return r'\sqrt'+('['+r('deg')+']' if r('deg') else '')+'{'+r('e')+'}'
    if t=='d':return r'\left'+value(e,'begChr','(')+' '+r'\middle|'.join(render(x) for x in e.findall('m:e',NS))+r' \right'+value(e,'endChr',')')
    if t=='m':return r'\begin{matrix}'+r' \\ '.join(' & '.join(render(c) for c in row.findall('m:e',NS)) for row in e.findall('m:mr',NS))+r'\end{matrix}'
    if t=='eqArr':return r'\begin{aligned}'+r' \\ '.join(render(x) for x in e.findall('m:e',NS))+r'\end{aligned}'
    if t=='nary':return value(e,'chr','∫')+'_{'+r('sub')+'}^{'+r('sup')+'}{'+r('e')+'}'
    if t in ('limLow','limUpp'):return '{'+r('e')+'}'+('_' if t=='limLow' else '^')+'{'+r('lim')+'}'
    if t=='func':return r('fName')+' '+r('e')
    if t=='acc':return r'\overset{'+value(e,'chr','^')+'}{'+r('e')+'}'
    if t=='bar':return ('\\underline{' if value(e,'pos','top')=='bot' else '\\overline{')+r('e')+'}'
    if t=='groupChr':return (r'\underset{' if value(e,'pos','bot')=='bot' else r'\overset{')+value(e,'chr','⏟')+'}{'+r('e')+'}'
    return ''.join(render(x) for x in e)

def extract(name,path):
    with ZipFile(path) as z:xml=z.read('word/document.xml')
    tree=ET.fromstring(xml);maths=tree.findall('.//m:oMath',NS)
    ids={id(e):f'{name}-m{i:04d}' for i,e in enumerate(maths,1)}
    records=[];paras=[];texts=[];tagcounts=collections.Counter()
    for i,p in enumerate(tree.findall('.//w:p',NS),1):
        pid=f'{name}-p{i:04d}';local=[]
        def read(e):
            if e.tag=='{'+NS['m']+'}oMath':
                mid=ids[id(e)];local.append(mid)
                records.append(dict(id=mid,paragraph=pid,rendering=render(e),
                    omml_xml=ET.tostring(e,encoding='unicode'),
                    structure_tags=dict(collections.Counter(tag(x) for x in e.iter()))))
                tagcounts.update(tag(x) for x in e.iter())
                return ' ⟦'+mid+': '+render(e)+'⟧ '
            if e.tag=='{'+NS['w']+'}t':return e.text or ''
            if tag(e) in ('br','tab'):return ' '
            return ''.join(read(x) for x in e)
        text=read(p)
        paras.append(dict(id=pid,text=text,math_ids=local))
        texts.append(pid+' '+text)
    report=dict(source=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        document_xml_sha256=hashlib.sha256(xml).hexdigest(),paragraph_count=len(paras),
        math_count=len(records),math_tag_counts=dict(tagcounts),paragraphs=paras,math_objects=records,
        interpretation='Document-order p/m IDs, independent of unstable printed equation numbers. Raw XML is authoritative; structural rendering is a reading aid.')
    assert len(records)==len(maths)
    (OUT/f'{name}_document.xml').write_bytes(xml)
    (OUT/f'{name}_indexed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (OUT/f'{name}_reading.txt').write_text('\n'.join(texts)+'\n')
    print(name,report['paragraph_count'],report['math_count'],report['source_sha256'])

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    extract('original1025',ROOT/'推理草稿5月1025.docx')
    extract('stage1review',ROOT/'stage3/source_inputs/starter/references/1025_stage1_review.docx')
