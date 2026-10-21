import json,shutil,numpy as np
from search_revo22_f5_orientation268 import O,put
from stage_revo22_f5_compact296 import S
from route_revo22_f5_scoped417 import run as route
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
m=json.loads((S/'stage_manifest.json').read_text());p=next(p for p in m['plates']if p['id']=='D09');it=next(i for i in p['items']if i['id']=='P130');r=json.loads((S/'plate_results/D09.json').read_text());q=json.loads((S/'candidates/PLATE_D09'/r['label']/'verification/native_final.json').read_text());src=json.loads((O/'selections/P130.json').read_text())['label'];a=O/'candidates/P130'/src;b=O/'candidates/P130/plate_observed447';b.mkdir(exist_ok=True)
for sub in ['parts','design','verification']:
 (b/sub).mkdir(exist_ok=True)
 for f in (a/sub).glob('*'):
  if sub!='verification' or f.name in ['guards.npz','strict_magnet_guards.npz']:shutil.copy2(f,b/sub/f.name)
put(b/'verification/native_final.json',q);put(b/'verification/plate_manifest.json',dict(id='D09',items=[it]));l='plate447';d=route('P130','plate_observed447',l,allow_removable_core=True);r=audit('P130',l)
if r['native_review_resolved']:
 g=geo('P130',l);assert g['geometric_constraints_passed']and not g['body_change_fit_and_pose_required'];put(O/'plate_repair_P130_447.json',dict(id='P130',label=l,native_pass=True,body_modified=False,teeth=d['new_tooth_count'],fins=d['support_count'],support_volume_mm3=d['support_volume_mm3'],fit_pending=False));print('P130_PLATE447_READY',flush=True)
