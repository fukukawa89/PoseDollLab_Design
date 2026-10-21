"""Create isolated candidate fins for directions picked by the complete F4 audit."""
from pathlib import Path
import sys,json,time,traceback
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import build_revo22_fins_v4 as builder
from audit_revo22_f4 import audit
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
ITEMS={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text(encoding='utf8'))['plates'] if not p['optional'] for i in p['items']}
VOLS={i['id']:i['volumes'] for i in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text(encoding='utf8'))['objects']}

def one(pid,indices=(0,1,2,3)):
 choices=json.loads((O/'orientation_v2'/f'{pid}.json').read_text(encoding='utf8'));rows=[]
 for index in indices:
  option=choices['best'][index];folder=O/'candidates'/pid/f'cov_{index:02}'
  for d in ['parts','design','verification','figures']:(folder/d).mkdir(parents=True,exist_ok=True)
  builder.O=folder;builder.choose=lambda _:option['orientation'];builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=3.2 if option['orientation']['size_mm'][2]<50 else 4.;builder.THICKNESS_OVERRIDE=None;builder.NORMAL_THRESHOLD=-.3;builder.SEGMENT_OVERRIDE=None
  t=time.time()
  try:
   r=builder.make(pid,ITEMS[pid],VOLS.get(pid,[]));a=audit(pid,folder,folder)
   row={'id':pid,'index':index,'folder':str(folder),'orientation':option,'audit':a,'support_count':r['support_count'],'teeth_count':len(r['teeth']),'elapsed_s':time.time()-t}
   print('CANDIDATE',pid,index,'fins',r['support_count'],'layer_excess',round(a['max_local_excess_area_mm2'],3),'sum',round(a['sum_layer_excess_area_mm2'],2),'seconds',round(time.time()-t,1),flush=True)
  except Exception:
   row={'id':pid,'index':index,'error':traceback.format_exc()};print('CANDIDATE_ERROR',pid,index,row['error'],flush=True)
  rows.append(row);(O/'candidates'/pid/'coverage_comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
 return rows
if __name__=='__main__':
 for pid in sys.argv[1:]:one(pid)
