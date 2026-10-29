"""Hash this new delivery; frozen input identity is in material_inventory.json."""
from pathlib import Path
import hashlib
import json
import platform
import importlib.metadata

root=Path(__file__).resolve().parents[1]
destination=root/'results/delivery_manifest.json'
files=[root/'README.md']
for folder in ('program','tests','notes','results'):
    files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=destination)
entries={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)}
report=dict(python=platform.python_version(),dependencies={name:importlib.metadata.version(name) for name in ('numpy','scipy','torch','matplotlib')},
    files=entries,scope='New stage3 delivery only. source_inputs and supplied archives are audited separately by inventory.py. Regenerate this manifest after rerunning experiments.')
destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Delivery files hashed:',len(entries))
