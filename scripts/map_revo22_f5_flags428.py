import json,numpy as np
from search_revo22_f5_orientation268 import O
from stage_revo22_f5_compact296 import S
m=json.loads((S/'stage_manifest.json').read_text())
for pid in ['D07','D08','D09','D10']:
 p=next(p for p in m['plates']if p['id']==pid);r=json.loads((S/'plate_results'/f'{pid}.json').read_text());q=json.loads((S/'candidates'/('PLATE_'+pid)/r['label']/'verification/native_final.json').read_text())
 for flag in q['external_islands']+q['critical_external_runs']:
  bb=flag['bounds_mm'];x,y=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2
  its=[i for i in p['items']if i['bounds_mm'][0]<=x<=i['bounds_mm'][3]and i['bounds_mm'][1]<=y<=i['bounds_mm'][4]]
  print(pid,round(flag['z_mm'],2),[(i['id'],i['number'],i['rotation_z_deg'])for i in its])
for pid in ['P130','X046']:
 sf=O/'selections'/f'{pid}.json';print('SELECTION',pid,json.loads(sf.read_text()) if sf.exists()else None)
