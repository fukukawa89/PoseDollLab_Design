import json,copy,inspect,re,numpy as np
from search_revo22_f5_orientation268 import put
import stage_revo22_f5_compact296 as stage
S=stage.S;m=json.loads((S/'stage_manifest.json').read_text());p=next(p for p in m['plates']if p['id']=='D12');put(S/'layout_before462.json',m);items=copy.deepcopy(p['items']);old={i['number']:i for i in items}
code=inspect.getsource(stage.pack);code=re.sub(r'  options=.*?;best=None',"  options=[0 if it['id']=='H004' else it['rotation_z_deg']//90];best=None",code);env=dict(stage.__dict__);exec(code,env);fn=env['pack'];best=None
for seed in range(5000):
 ps=fn(items,seed)
 if len(ps)!=1:continue
 score=sum(np.linalg.norm(np.array(i['translation_mm'])-old[i['number']]['translation_mm'])for i in ps[0]['items'])
 if best is None or score<best[0]:best=(score,ps[0],seed)
assert best,'D12 fixed rotations cannot fit';p['items']=sorted(best[1]['items'],key=lambda i:i['number']);print('REPACK462',best[0],best[2],flush=True)
for k,i in enumerate(p['items']):
 b=np.array(i['bounds_mm']);assert min(b[:2])>=4-1e-6 and max(b[3:5])<=176+1e-6
 for j in p['items'][k+1:]:
  c=np.array(j['bounds_mm']);assert np.linalg.norm(np.maximum(np.maximum(b[:2]-c[3:5],c[:2]-b[3:5]),0))>=6-1e-6
put(S/'stage_manifest.json',m)
