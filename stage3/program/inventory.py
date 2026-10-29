"""Audit supplied research material without modifying archives or frozen evidence.

Run from the checkout: python3 stage3/program/inventory.py [--network]
The optional network check reads Git refs only; it does not download S1 data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile

REPO = Path(__file__).resolve().parents[2]
STAGE = REPO / 'stage3'
SOURCE = STAGE / 'source_inputs'
FIXED_COMMIT = '82519542dd057e8fbd6d6879ef33217761e8cbbb'
UPSTREAM = 'https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007.git'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive_audit(archive, extracted):
    rows = []
    with ZipFile(archive) as zipped:
        for info in zipped.infolist():
            relative = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            safe = (not relative.is_absolute() and '..' not in relative.parts
                    and not stat.S_ISLNK(mode) and '\\' not in info.filename)
            if not safe:
                raise ValueError(f'Unsafe archive member: {info.filename}')
            if info.is_dir():
                continue
            data = zipped.read(info)  # ZIP CRC is verified by ZipFile.read.
            local = extracted / relative
            same = local.is_file() and sha(local.read_bytes()) == sha(data)
            rows.append(dict(path=info.filename, bytes=len(data), sha256=sha(data),
                             extracted_status='matched' if same else
                             ('mismatch' if local.exists() else 'missing')))
    return dict(path=str(archive.relative_to(REPO)), bytes=archive.stat().st_size,
                sha256=sha(archive.read_bytes()), extracted_root=str(extracted.relative_to(REPO)),
                files=len(rows), all_paths_safe=True, zip_crc_read_passed=True,
                status_counts=dict(Counter(row['extracted_status'] for row in rows)),
                entries=rows)


def docx_audit(source, text_name):
    with ZipFile(source) as zipped:
        raw = zipped.read('word/document.xml')
    root = ET.fromstring(raw)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    paragraphs = [''.join(node.text or '' for node in paragraph.iter()
                          if node.tag.rsplit('}', 1)[-1] == 't')
                  for paragraph in root.findall('.//w:p', ns)]
    text = '\n'.join(paragraphs)
    output = STAGE / 'notes' / text_name
    output.write_text(text, encoding='utf-8')
    return dict(path=str(source.relative_to(REPO)), sha256=sha(source.read_bytes()),
                bytes=source.stat().st_size, document_xml_sha256=sha(raw),
                paragraphs=len(paragraphs), omml_math_objects=len(root.findall('.//m:oMath', ns)),
                extracted_text=str(output.relative_to(REPO)),
                extraction_limitation='Paragraph text includes OMML token text; flattened text is not a faithful formula typesetting. Original DOCX XML remains authoritative.')


def required_external_inputs():
    root = SOURCE / 'starter/stage2'
    specs = []
    for group in ('learning', 'learning_stress'):
        for name in ['learning_data.npz', 'analytic_coefficients.npy', 'rom_matrices.npz',
                     'learning_summary.json', 'evaluation_summary.json'] + [
                         f'complex_seed{seed}.pt' for seed in (1025, 1026, 1027)]:
            specs.append((f'results/{group}/{name}', 'evaluate_models.py / run_confirmation.py / train_spd_complex.py'))
    for group in ('local', 'stress'):
        for name in ('spd_complex_seed1025.pt', 'learning_summary.json'):
            specs.append((f'results/learning_spd/{group}/{name}', 'evaluate_spd_confirmation.py'))
    for group in ('main', 'stress'):
        for name in ('confirmation_data.npz', 'dataset_manifest.json', 'confirmation_summary.json'):
            specs.append((f'results/learning_confirmation/{group}/{name}', 'evaluate_spd_confirmation.py'))
        specs.append((f'results/learning_confirmation/frozen/models/{group}/rom_matrices.npz', 'evaluate_spd_confirmation.py'))
    specs.append(('results/learning_confirmation/frozen/config.json', 'evaluate_spd_confirmation.py'))
    for variant in ('linear', 'analytic', 'complex', 'truth'):
        specs.append((f'results/learning/feedforward/{variant}.npz', 'rod3d/run_learning_comparison.py'))
    specs.extend([
        ('verify_delivery.py', 'stage2/README.md: full delivery verification, distinct from verify_starter.py'),
        ('notes/1025_stage1_detailed.md', 'notes/route_a.md: historical 118-page detailed review; supplied DOCX review is independently available'),
        ('sources/s1_original/IJRR_CHNN_KAM_导师意见凝练稿_20261002', 'notes/v10_baseline.md: complete historical S1 scientific records'),
        ('sources/integration_latest/v10_birkhoff_20261028', 'notes/route_a.md: historical latest integration; supplied v10_framework is a different package'),
    ])
    return [dict(path=str((root / relative).relative_to(REPO)), required_by=reason,
                 status='present' if (root / relative).exists() else 'missing_data' if not relative.endswith('.py') else 'missing_source')
            for relative, reason in specs]


def baseline_evidence():
    pointer = Path('/workspace/1028-cloud/latest-validation.txt')
    if not pointer.exists():
        return dict(status='not_executed_or_no_runtime_record', checks=[])
    report = Path(pointer.read_text().strip()) / 'validation.json'
    if not report.is_file():
        return dict(status='not_executed_or_no_runtime_record', checks=[])
    data = json.loads(report.read_text())
    retained = STAGE / 'results/baseline'
    for row in data['checks']:
        row['status'] = 'executed_passed' if row['exit_code'] == 0 else 'executed_failed'
        log = report.parent / 'logs' / (row['name'] + '.log')
        row['log_sha256'] = sha(log.read_bytes()) if log.exists() else None
        retained_log = retained / 'logs' / log.name
        if retained_log.exists():
            row['retained_log'] = str(retained_log.relative_to(REPO))
            row['retained_log_hash_matches_runtime'] = sha(retained_log.read_bytes()) == row['log_sha256']
    return dict(status='actual_runtime_report_read', report_path=str(report),
                retained_report=str((retained / 'validation.json').relative_to(REPO)),
                report_sha256=sha(report.read_bytes()), checks=data['checks'],
                evidence_scope='Exit statuses and logs from current onboarding scratch copies, not inherited source_inputs result JSONs.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--network', action='store_true', help='Read upstream advertised Git refs.')
    args = parser.parse_args()
    (STAGE / 'results').mkdir(parents=True, exist_ok=True)
    (STAGE / 'notes').mkdir(parents=True, exist_ok=True)
    archives = [
        ('codex_stage3_starter_1MB.zip', SOURCE / 'starter'),
        ('v10_英文中文整合源码与复算包 (1).zip', SOURCE / 'v10'),
        ('一般Birkhoff_推导与验证材料.zip', SOURCE / 'birkhoff'),
    ]
    checked = [archive_audit(REPO / name, root) for name, root in archives]
    docs = [docx_audit(REPO / '推理草稿5月1025.docx', 'original_1025_text.txt'),
            docx_audit(SOURCE / 'starter/references/1025_stage1_review.docx', 'stage1_review_text.txt')]
    manifest = json.loads((SOURCE / 'starter/FILE_HASHES_SHA256.json').read_text())
    manifest_errors = [name for name, record in manifest.items()
                       if not (SOURCE / 'starter' / name).is_file()
                       or sha((SOURCE / 'starter' / name).read_bytes()) != record['sha256']
                       or (SOURCE / 'starter' / name).stat().st_size != record['bytes']]
    source_files = [SOURCE / 'starter' / row['path'] for row in checked[0]['entries']]
    delivered_paths = {p.resolve() for p in source_files}
    extra_local_files = [str(p.relative_to(SOURCE / 'starter'))
                         for p in (SOURCE / 'starter').rglob('*')
                         if p.is_file() and p.resolve() not in delivered_paths]
    upstream = dict(status='not_executed', requested_fixed_commit=FIXED_COMMIT)
    if args.network:
        result = subprocess.run(['git', 'ls-remote', UPSTREAM], capture_output=True, text=True, timeout=45)
        refs = [dict(commit=line.split()[0], ref=line.split()[1])
                for line in result.stdout.splitlines() if len(line.split()) == 2] if result.returncode == 0 else []
        upstream.update(status='executed_passed' if result.returncode == 0 else 'executed_failed',
                        command='git ls-remote ' + UPSTREAM, exit_code=result.returncode, refs=refs,
                        fixed_commit_advertised=any(row['commit'] == FIXED_COMMIT for row in refs),
                        scope='Remote identity check only; no original GitHub scientific computation was rerun.')
    payload = dict(archives=checked, documents=docs,
                   requested_starter_name='1025_Codex_第三阶段_轻量开工包.zip',
                   actual_starter_name='codex_stage3_starter_1MB.zip',
                   starter_manifest=dict(entries=len(manifest), errors=manifest_errors),
                   source_counts=dict(Counter(p.suffix.lower() for p in source_files)),
                   extra_local_files_not_archive_inputs=extra_local_files,
                   starter_weight_or_trajectory_files=[str(p.relative_to(SOURCE / 'starter')) for p in source_files
                                                       if p.suffix.lower() in ('.pt', '.pth', '.npz', '.npy')],
                   original_docx_matches_starter_reference=(REPO / '推理草稿5月1025.docx').read_bytes() ==
                       (SOURCE / 'starter/references/推理草稿5月1025.docx').read_bytes(),
                   root_birkhoff_zip_matches_starter_reference=(REPO / '一般Birkhoff_推导与验证材料.zip').read_bytes() ==
                       (SOURCE / 'starter/references/一般Birkhoff_推导与验证材料.zip').read_bytes(),
                   external_input_requirements=required_external_inputs(),
                   upstream_git=upstream, baseline_checks=baseline_evidence(),
                   historical_result_policy='Existing JSON/CSV under source_inputs record prior work; presence alone does not mean executed or independently validated now.')
    output = STAGE / 'results/material_inventory.json'
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    mismatches = sum(a['status_counts'].get('mismatch', 0)+a['status_counts'].get('missing', 0) for a in checked)
    print(json.dumps(dict(archive_files=sum(a['files'] for a in checked), archive_mismatches=mismatches,
                          starter_manifest_entries=len(manifest), starter_manifest_errors=len(manifest_errors),
                          starter_weight_or_trajectory_files=len(payload['starter_weight_or_trajectory_files']),
                          output=str(output)), ensure_ascii=False))
    raise SystemExit(bool(mismatches or manifest_errors))


if __name__ == '__main__':
    main()
