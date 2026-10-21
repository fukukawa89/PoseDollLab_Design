import json,sys,time,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import build_revo22_f4_repair_fins as b
from audit_revo22_f4 import audit
from slice_revo22_f4_candidate import run
from search_revo22_f2_orientations import frame
O=b.O;B=b.B
items={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items']}
vols={i['id']:i['volumes'] for i in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects']}
for pid in sys.argv[1:]:
 n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');v=n['source_v'];dirs=[[0,0,1],[0,0,-1]]
 if pid in ['X079','N003']:dirs += [[0,1,0],[0,-1,0],[1,0,0],[-1,0,0]]
 rows=[]
 for j,dr in enumerate(dirs):
  M=frame(np.array(dr,float));ori={'matrix':M.tolist(),'source_translation_mm':(-(v@M.T).min(0)).tolist(),'gravity_in_source':dr,'size_mm':np.ptp(v@M.T,0).tolist()}
  for ax in [0,90]:
   label=f'repair_dir_{j:02}_{ax:02}';folder=O/'candidates'/pid/label
   for sub in ['parts','design','verification','figures']:(folder/sub).mkdir(parents=True,exist_ok=True)
   b.O=folder;b.choose=lambda _:ori;b.NORMAL_THRESHOLD=-.6;b.PITCH_OVERRIDE=1.8;b.AXIS=ax;b.FACE_FILTER=None;b.THICKNESS_OVERRIDE=None;b.SEGMENT_OVERRIDE=24
   if not (folder/f'{pid}.json').exists():
    rep=b.make(pid,items[pid],vols.get(pid,[]));aa=audit(pid,folder,folder)
   else:aa=json.loads((folder/f'{pid}.json').read_text())
   score=aa['max_local_excess_area_mm2']*25+aa['sum_layer_excess_area_mm2'];rows.append({'label':label,'score':score,'height':ori['size_mm'][2],'area':aa['max_local_excess_area_mm2']});print('OPTION',pid,label,'score',round(score,3),flush=True)
 rows.sort(key=lambda r:r['score']);(O/'candidates'/pid/'repair_direction_choices.json').write_text(json.dumps(rows,indent=2))
 for q in rows[:2]:
  label=q['label'];p=O/'candidates'/pid/label/'verification/local_extrusion.json'
  if not p.exists():run(pid,label)
  d=json.loads(p.read_text());print('NATIVE_REPAIR',pid,label,len(d['detached_bead_regions']),d['unresolved_count'],d['max_unresolved_span_mm'],flush=True)
