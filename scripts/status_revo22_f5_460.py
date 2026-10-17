import json,hashlib
from stage_revo22_f5_compact296 import S,sha
m=json.loads((S/'stage_manifest.json').read_text())
for p in m['plates']:
 key=hashlib.sha256(json.dumps(dict(plate=p,geometry={i['id']:sha(S/'parts'/f"{i['id']}.npz")for i in p['items']}),sort_keys=True).encode()).hexdigest();f=S/'plate_results'/f"{p['id']}.json";q=json.loads(f.read_text())if f.exists()else{};print(p['id'],q.get('native_clear'),q.get('layout_and_source_hash')==key,q.get('external_islands'),q.get('critical_external_runs'))
