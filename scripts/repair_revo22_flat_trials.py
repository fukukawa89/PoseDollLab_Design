import json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import build_revo22_fins_v4 as b
from audit_revo22_f4 import audit
from o22_cross_section_geometry import polygon
from slice_revo22_f4_candidate import run
O=b.O;B=b.B
items={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items']}
vols={i['id']:i['volumes'] for i in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects']}
b.polygon=polygon
for pid in sys.argv[1:]:
 folder=O/'candidates'/pid/'repair_flat_00'
 for s in ['parts','design','verification','figures']:(folder/s).mkdir(parents=True,exist_ok=True)
 n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');v=n['source_v'];f=n['f'];ori={'matrix':np.eye(3).tolist(),'source_translation_mm':(-v.min(0)).tolist(),'gravity_in_source':[0.,0.,1.],'size_mm':np.ptp(v,0).tolist(),'reason':'Original source flat placement; lower fins and larger natural bed contacts.'}
 b.O=folder;b.choose=lambda _:ori;b.NORMAL_THRESHOLD=-.6;b.PITCH_OVERRIDE=2.4;b.AXIS=0;b.FACE_FILTER=None;b.THICKNESS_OVERRIDE=None;b.SEGMENT_OVERRIDE=24
 if not (folder/'design'/f'{pid}.json').exists():
  st=time.time();rep=b.make(pid,items[pid],vols.get(pid,[]));print('BUILT',pid,rep['support_count'],len(rep['teeth']),round(time.time()-st,1),flush=True);audit(pid,folder,folder)
 if not (folder/'verification/local_extrusion.json').exists():run(pid,'repair_flat_00')
 d=json.loads((folder/'verification/local_extrusion.json').read_text());print('NATIVE',pid,len(d['detached_bead_regions']),d['unresolved_count'],d['max_unresolved_span_mm'],flush=True)
