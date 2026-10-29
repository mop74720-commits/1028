from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
m=json.loads((p/'FILE_HASHES_SHA256.json').read_text(encoding='utf-8'))
errors=[]
for rel,check in m.items():
    f=p/rel
    if not f.is_file(): errors.append('MISSING '+rel); continue
    b=f.read_bytes()
    if len(b)!=check['bytes'] or hashlib.sha256(b).hexdigest()!=check['sha256']:
        errors.append('MISMATCH '+rel)
print('轻量包已检查',len(m),'项，错误',len(errors))
for e in errors: print(e)
raise SystemExit(bool(errors))
