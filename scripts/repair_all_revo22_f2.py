import json,traceback
from build_revo22_fins_v2 import O
from repair_revo22_f2_contacts import repair
for p in sorted((O/'verification').glob('*_layers.json')):
 r=json.loads(p.read_text());pid=r['id']
 if not r['combined_floating_islands'] or pid in ['X046','W016','X050']:continue
 try:repair(pid)
 except Exception:print('ERROR',pid,traceback.format_exc(),flush=True)
print('ALL REPAIRS COMPLETE',flush=True)