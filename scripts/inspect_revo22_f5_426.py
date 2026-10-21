import json, numpy as np
from search_revo22_f5_orientation268 import O
from stage_revo22_f5_compact296 import S
m=json.loads((S/'stage_manifest.json').read_text())
for pid in ['D07','D08','D09','D10','D12']:
 p=next(p for p in m['plates']if p['id']==pid);f=S/'plate_results'/f'{pid}.json'
 if not f.exists():print(pid,'NO RESULT');continue
 r=json.loads(f.read_text());q=json.loads((S/'candidates'/('PLATE_'+pid)/r['label']/'verification/native_final.json').read_text())
 print(pid,[(i['number'],i['id'],i['rotation_z_deg'],i.get('finer_layer_for_compact_layout',False))for i in p['items']])
 for flag in q['external_islands']+q['critical_external_runs']:print('FLAG',flag)
for lab in ['reroute417_r4_2','reroute424_xp_2','reroute424_ym_2','reroute424_yp_2']:
 f=O/'candidates/P130'/lab/'verification/native_final.json'
 if f.exists():
  r=json.loads(f.read_text());print(lab,r['external_island_count'],r['critical_external_count']);print(r['external_islands']);print(r['critical_external_runs'])
