import json,numpy as np
from search_revo22_f5_orientation268 import O
from stage_revo22_f5_compact296 import S
m=json.loads((S/'stage_manifest.json').read_text());p=next(p for p in m['plates']if p['id']=='D01');r=json.loads((S/'plate_results/D01.json').read_text());q=json.loads((S/'candidates/PLATE_D01'/r['label']/'verification/native_final.json').read_text())
print('ITEMS',[(i['id'],i['number'],i['rotation_z_deg'],i.get('finer_layer_for_compact_layout',False))for i in p['items']])
for q in q['external_islands']+q['critical_external_runs']:
 b=q['bounds_mm'];x,y=(b[0]+b[2])/2,(b[1]+b[3])/2;print('FLAG',q.get('area_mm2',q.get('length_mm')),q['z_mm'],[(i['id'],i['number'])for i in p['items']if i['bounds_mm'][0]<x<i['bounds_mm'][3]and i['bounds_mm'][1]<y<i['bounds_mm'][4]])
