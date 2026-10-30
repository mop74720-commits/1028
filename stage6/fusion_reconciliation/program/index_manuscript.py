"""Locate mathematical blocks in actual bilingual TeX, without judging validity.

Displayed equations, theorem-like blocks and tables are review units. Inline
math is separately indexed as notation/context, not counted as proven theorems.
Exact file/line locations and text hashes make semantic annotations traceable.
"""
from pathlib import Path
import hashlib
import json
import re
from materials import resolve_source

BASE = Path(__file__).resolve().parents[1]
ENVIRONMENTS = r'equation\*?|align\*?|alignat\*?|gather\*?|multline\*?|eqnarray\*?|displaymath'
STATEMENTS = r'theorem|lemma|proposition|corollary|definition|assumption|remark|table\*?'


def blocks(text, pattern, kind):
    rows = []
    for match in re.finditer(pattern, text, re.S):
        body = match.group(0)
        rows.append(dict(kind=kind, line_start=text.count('\n', 0, match.start())+1,
                         line_end=text.count('\n', 0, match.end())+1,
                         labels=re.findall(r'\\label\{([^}]+)\}', body),
                         tex=body, sha256=hashlib.sha256(body.encode()).hexdigest(),
                         _start=match.start(), _end=match.end()))
    return rows


def main():
    provenance = json.loads((BASE/'results/materials.json').read_text())
    source = resolve_source()
    chapters, review, inline = [], [], []
    for language in ['english', 'chinese']:
        for path in sorted((source/language/'sections').glob('*.tex')):
            original = path.read_text()
            # Keep newline counts stable; ignore unescaped TeX comments.
            text = re.sub(r'(?<!\\)%[^\n]*', '', original)
            relative = str(path.relative_to(source))
            math = blocks(text, r'\\begin\{('+ENVIRONMENTS+r')\}.*?\\end\{\1\}', 'display')
            math += blocks(text, r'\\\[.*?\\\]', 'display')
            math += blocks(text, r'(?<!\\)\$\$.*?(?<!\\)\$\$', 'display')
            statements = blocks(text, r'\\begin\{('+STATEMENTS+r')\}.*?\\end\{\1\}', 'statement')
            ordinary = blocks(text, r'\\\(.*?\\\)', 'inline')
            ordinary += blocks(text, r'(?<![\\$])\$(?!\$).*?(?<![\\$])\$(?!\$)', 'inline')
            ordinary = [row for row in ordinary if not any(m['_start'] <= row['_start'] < m['_end'] for m in math)]
            counts = {}
            for row in sorted(math+statements+ordinary, key=lambda x:(x['_start'],x['kind'])):
                anchor = f"{relative}:L{row['line_start']:04d}:{row['kind']}"
                counts[anchor] = counts.get(anchor,0)+1
                row.update(id=anchor+f":{counts[anchor]}", source=relative, language=language,
                           archive=provenance['archive'], archive_sha256=provenance['archive_sha256'])
                row.pop('_start'); row.pop('_end')
                (inline if row['kind']=='inline' else review).append(row)
            chapters.append(dict(source=relative, language=language, bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), lines=original.count('\n')+1,
                headings=[dict(kind=m.group(1),line=text.count('\n',0,m.start())+1,title=m.group(2))
                    for m in re.finditer(r'\\((?:sub)*section)\*?\{([^\n]+)\}',text)],
                review_units=len(math)+len(statements), inline_context_units=len(ordinary),
                old_framework_source='stage3/source_inputs/v10/v10_framework_20261028/'+relative,
                annotation_status='index_only_not_mathematical_verification'))
    result = dict(archive_sha256=provenance['archive_sha256'], chapters=chapters,
                  review_units=review, inline_context=inline,
                  scope='Mechanical location index. Review conclusions require separately authored annotations and executed evidence; extraction itself proves no theorem.')
    (BASE/'results/manuscript_index.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(chapters=len(chapters),review_units=len(review),inline_context=len(inline)),ensure_ascii=False))


if __name__=='__main__':
    main()
