import json,copy,numpy as np
from pathlib import Path
from search_revo22_f5_orientation268 import O,put
import stage_revo22_f5_compact296 as stage
S=stage.S
p=Path(stage.__file__);s=p.read_text(encoding='utf-8-sig');s=s.replace("['X062','X038','X046','X054','P130']else[0,1]","['X062','X038','X046','X054','P130','P035','W016','P117','P093','W017','P115','P049']else[0,1]");p.write_text(s,encoding='utf-8')
import importlib;importlib.reload(stage)
m=json.loads((S/'stage_manifest.json').read_text());put(S/'layout_before_rotation429.json',m)
for p in m['plates']:
 if p['id']not in ['D07','D08','D09','D10']:continue
 old={i['number']:i for i in p['items']};best=None
 for seed in range(5000):
  ps=stage.pack(p['items'],seed)
  if len(ps)!=1:continue
  pp=ps[0];score=(sum(i['rotation_z_deg']!=old[i['number']]['rotation_z_deg'] for i in pp['items']),sum(np.linalg.norm(np.array(i['translation_mm'])-old[i['number']]['translation_mm'])for i in pp['items']))
  if best is None or score<best[0]:best=(score,pp,seed)
 assert best,(p['id'],'Cannot keep one plate')
 p['items']=sorted(best[1]['items'],key=lambda i:i['number']);p['rotation_repair_seed']=best[2]
 print('REPACK429',p['id'],best[0],best[2],flush=True)
 for i in p['items']:
  b=np.array(i['bounds_mm']);assert min(b[:2])>=4-1e-6 and max(b[3:5])<=176+1e-6
  for j in p['items']:
   if j['number']<=i['number']:continue
   c=np.array(j['bounds_mm']);assert np.linalg.norm(np.maximum(np.maximum(b[:2]-c[3:5],c[:2]-b[3:5]),0))>=6-1e-6
put(S/'stage_manifest.json',m)
