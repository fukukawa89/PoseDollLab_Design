import json,numpy as np
from stage_revo22_f5_compact296 import S
m=json.loads((S/'stage_manifest.json').read_text());p=next(p for p in m['plates']if p['id']=='D12');r=json.loads((S/'plate_results/D12.json').read_text());q=json.loads((S/'candidates/PLATE_D12'/r['label']/'verification/native_final.json').read_text())
for q in q['external_islands']+q['critical_external_runs']:
 b=q['bounds_mm'];x,y=(b[0]+b[2])/2,(b[1]+b[3])/2
 print(q)
 for i in p['items']:
  c=i['bounds_mm']
  if c[0]<=x<=c[3]and c[1]<=y<=c[4]:print('OBJECT',i['id'],i['number'],i['rotation_z_deg'],'LOCAL',((np.array([x,y,q['z_mm']])-i['translation_mm'])@np.array(i['rotation_matrix'])).tolist())
