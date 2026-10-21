import json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import build_revo22_f4_repair_fins as b
from audit_revo22_f4 import audit
from slice_revo22_f4_candidate import run
O=b.O;B=b.B
items={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items']}
vols={i['id']:i['volumes'] for i in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects']}
for pid in sys.argv[1:]:
 folder=O/'candidates'/pid/'repair_fins_00'
 for sub in ['parts','design','verification','figures']:(folder/sub).mkdir(parents=True,exist_ok=True)
 src=O/'candidates'/pid/('cov_00' if pid in ['X046','X038','H006'] else 'repair_flat_00')
 ori=json.loads((src/'design'/f'{pid}.json').read_text())['orientation'];b.O=folder;b.choose=lambda _:ori;b.NORMAL_THRESHOLD=-.6;b.PITCH_OVERRIDE=2.4;b.AXIS=0;b.FACE_FILTER=None;b.THICKNESS_OVERRIDE=None;b.SEGMENT_OVERRIDE=24
 if not (folder/'design'/f'{pid}.json').exists():
  st=time.time();rep=b.make(pid,items[pid],vols.get(pid,[]));print('BUILT',pid,rep['support_count'],len(rep['teeth']),round(time.time()-st,1),flush=True);audit(pid,folder,folder)
 if not (folder/'verification/local_extrusion.json').exists():run(pid,'repair_fins_00')
 d=json.loads((folder/'verification/local_extrusion.json').read_text());print('NATIVE',pid,len(d['detached_bead_regions']),d['unresolved_count'],d['max_unresolved_span_mm'],flush=True)
