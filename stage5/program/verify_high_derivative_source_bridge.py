"""Verify exactly which tested AD functions survive a later numeric-wrapper edit.

This is source provenance, not a substitute for a numerical derivative test.
The preserved snapshot's SHA must first equal the actually executed report SHA.
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'stage5/results/high_derivatives'
old = ROOT / 'stage5/results/transport/legacy_ad_source/post_inverse_transport_native.py'
current = ROOT / 'stage5/program/transport_native.py'


def methods(path):
    tree = ast.parse(path.read_text())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'NativeTransport')
    return {node.name: ast.dump(node, include_attributes=False)
            for node in cls.body if isinstance(node, ast.FunctionDef)}


def main():
    source_key = str(current.relative_to(ROOT))
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    reports = {name: json.loads((OUT / (name + '.json')).read_text())
               for name in ('minimal', 'rom', 'transport')}
    recorded = {name: value['source_sha256'][source_key]
                for name, value in reports.items()}
    assert all(value == sha(old) for value in recorded.values())
    before, after = methods(old), methods(current)
    unchanged = sorted(name for name in before.keys() & after.keys()
                       if before[name] == after[name])
    changed = sorted(name for name in before.keys() | after.keys()
                     if before.get(name) != after.get(name))
    expected_changes = ['__init__', 'field', 'field_and_jacobian']
    assert changed == expected_changes, changed
    required = ['high_order_hamiltonian', 'legendre_difference', 'force_tensor',
                'field_tensor', 'a0', 'a1', 'b1', 'source_coefficient_function',
                'lie_oneform', 'coefficient_function', 'oneform', 'coefficient']
    assert all(name in unchanged for name in required)
    result = dict(
        status='executed_AD_functions_unchanged',
        command=[sys.executable, *sys.argv],
        utc=datetime.now(timezone.utc).isoformat(),
        report_source_hashes=recorded,
        preserved_snapshot=str(old.relative_to(ROOT)),
        preserved_snapshot_sha256=sha(old), current_sha256=sha(current),
        unchanged_methods=unchanged, changed_methods=changed,
        change_scope='An optional separate numeric-force callback was added. '
                     'All symbolic/high-order AD functions are byte-AST identical. '
                     'Physical numeric callbacks require their separate coil-interface check.',
        not_claimed='This does not establish uniform derivative correctness or certify new model callbacks.')
    (OUT / 'current_source_bridge.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
