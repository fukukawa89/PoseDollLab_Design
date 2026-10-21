import json,time,traceback,sys
import build_revo22_fins_v2 as f2
from check_revo22_f2_layers import check
from repair_revo22_f2_contacts import repair
B=f2.B;O=f2.O
u={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']};vols={i['part']:i['volumes'] for i in json.loads((f2.D/'all_protected_volumes.json').read_text())['objects']}
for pid,it in u.items():
 if (O/'parts'/f'{pid}.npz').exists():continue
 try:
  start=time.time();r=f2.make(pid,it,vols.get(it['part'],[]));print('BUILD',pid,r['support_count'],len(r['teeth']),round(r['new_height_mm'],2),round(time.time()-start,1),flush=True)
 except Exception:print('ERROR',pid,traceback.format_exc(),flush=True)
print('BUILD COMPLETE',flush=True)