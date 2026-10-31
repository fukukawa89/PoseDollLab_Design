import json,numpy as np
from stage_revo22_f5_compact296 import S
m=json.loads((S/'stage_manifest.json').read_text())
for pid in ['D11','D12']:
 p=next(p for p in m['plates']if p['id']==pid);r=json.loads((S/'plate_results'/f'{pid}.json').read_text());q=json.loads((S/'candidates'/('PLATE_'+pid)/r['label']/'verification/native_final.json').read_text())
 for q in q['external_islands']+q['critical_external_runs']:
  b=q['bounds_mm'];x,y=(b[0]+b[2])/2,(b[1]+b[3])/2;print(pid,q,[(i['id'],i['number'],i['rotation_z_deg'])for i in p['items']if i['bounds_mm'][0]<x<i['bounds_mm'][3]and i['bounds_mm'][1]<y<i['bounds_mm'][4]])
for pid in ['P035','P049']:
 d=json.loads((S/'design'/f'{pid}.json').read_text());print(pid,'ADD',len(d.get('f5_additions',[])),'REMOVE',len(d.get('f5_reliefs',[])))
