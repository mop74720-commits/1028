#!/usr/bin/env python3
"""Validate manuscript sources/artifacts; does not execute scientific models."""
import collections
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

PAPER = Path(__file__).resolve().parents[1]
REPO = PAPER.parents[1]


def clean(text):
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def normalized(text):
    return re.sub(r"\s+", "", text)


def signatures(path):
    text = clean(path.read_text())
    displays = re.findall(
        r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}",
        text, re.S)
    dollar_positions = []
    for i, char in enumerate(text):
        if char != '$':
            continue
        j = i - 1
        while j >= 0 and text[j] == chr(92):
            j -= 1
        if (i - 1 - j) % 2 == 0:
            dollar_positions.append(i)
    assert len(dollar_positions) % 2 == 0, path
    inline = [text[a+1:b] for a,b in zip(dollar_positions[::2], dollar_positions[1::2])]
    return {
        'display': [normalized(s) for _, s in displays],
        'inline': collections.Counter(normalized(s) for s in inline),
        'labels': re.findall(r"\\label\{([^}]+)\}", text),
        'citations': re.findall(r"\\cite\w*\{([^}]+)\}", text),
        'numeric_tokens': collections.Counter(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", text)),
    }


def main():
    report = {'scope': 'Typesetting, bilingual parity and frozen-source integrity only',
              'new_scientific_experiments': False, 'pairs': {}, 'pdfs': {}, 'source_files': 0}
    pairs = [(p, PAPER/'chinese/sections'/p.name)
             for p in sorted((PAPER/'english/sections').glob('*.tex'))]
    pairs += [(PAPER/'supplement'/f'{n}_en.tex', PAPER/'supplement'/f'{n}_zh.tex')
              for n in ['theory', 'learning_kam', 'evidence']]
    for en, zh in pairs:
        a, b = signatures(en), signatures(zh)
        checks = {k: a[k] == b[k] for k in a}
        report['pairs'][str(en.relative_to(PAPER))] = {
            'matching': checks, 'display_count': len(a['display']),
            'inline_count': sum(a['inline'].values()), 'labels': len(a['labels'])}
        assert all(checks.values()), (str(en), checks)
    for row in csv.DictReader((PAPER/'evidence/source_manifest.csv').open()):
        src = row['source_path']
        assert src.startswith(('stage3/', 'stage4/', 'stage5/')), src
        assert hashlib.sha256((REPO/src).read_bytes()).hexdigest() == row['sha256'], src
        report['source_files'] += 1
    for lang in ['english', 'chinese']:
        labels = []
        refs = []
        for path in (PAPER/lang).rglob('*.tex'):
            text = clean(path.read_text())
            labels += re.findall(r'\\label\{([^}]+)\}', text)
            refs += re.findall(r'\\(?:eqref|ref)\{([^}]+)\}', text)
        assert len(labels) == len(set(labels)), (lang, 'duplicate labels')
        assert not set(refs)-set(labels), (lang, 'missing labels', set(refs)-set(labels))
    report['compiled_numbering'] = {}
    for name, left, right in [
        ('main', PAPER/'english/main.aux', PAPER/'chinese/main.aux'),
        ('supplement', PAPER/'supplement/main_en.aux', PAPER/'supplement/main_zh.aux')]:
        def numbers(path):
            return {k: v for k, v in re.findall(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}', path.read_text())
                    if k not in ('FirstPage', 'LastPage')}
        a, b = numbers(left), numbers(right)
        assert a == b, (name, 'compiled numbering mismatch')
        report['compiled_numbering'][name] = {'matching': True, 'labels': len(a)}
    for stem in ['Stage5_IJRR_EN', 'Stage5_IJRR_ZH',
                 'Stage5_IJRR_Supplement_EN', 'Stage5_IJRR_Supplement_ZH']:
        pdf = PAPER/f'{stem}.pdf'
        log = (PAPER/'build_logs'/f'{stem}.log').read_text()
        bad = re.findall(r'^.*(?:Overfull|Missing character|undefined references|undefined citations|Label\(s\) may have changed|^!).*$', log, re.M)
        assert not bad, (stem, bad)
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        fonts = subprocess.check_output(['pdffonts', str(pdf)], text=True)
        # pdffonts columns: name, type, encoding, emb, sub, uni, object ID.
        unembedded = [line for line in fonts.splitlines()[2:]
                      if len(line.split()) >= 7 and line.split()[-5] != 'yes']
        assert not unembedded, (stem, unembedded)
        text = subprocess.check_output(['pdftotext', str(pdf), '-'], text=True)
        assert '??' not in text, (stem, 'unresolved marker')
        report['pdfs'][stem] = {
            'pages': int(re.search(r'Pages:\s+(\d+)', info).group(1)),
            'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
            'bytes': pdf.stat().st_size, 'all_fonts_embedded': True,
            'overflow_or_missing_reference_errors': 0,
            'latex_warnings': re.findall(r'^.*Warning.*$', log, re.M),
            'bibtex_warnings': re.findall(r'^Warning.*$', (PAPER/'build_logs'/f'{stem}.blg').read_text(), re.M),
        }
    base = json.loads((PAPER/'evidence/provenance.json').read_text())['base_commit']
    changed = subprocess.check_output(['git', 'diff', '--name-only', base, '--'], cwd=REPO, text=True).splitlines()
    assert all(p.startswith('papers/stage5_ijrr/') for p in changed), changed
    report['existing_research_files_changed'] = []
    (PAPER/'evidence/validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'pairs': len(pairs), 'source_files': report['source_files'],
                      'pages': {k:v['pages'] for k,v in report['pdfs'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
