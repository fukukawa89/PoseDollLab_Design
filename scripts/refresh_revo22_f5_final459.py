import json,collections,numpy as np
from search_revo22_f5_orientation268 import OLD,put
from stage_revo22_f5_compact296 import S,prepare
prepare();m=json.loads((S/'stage_manifest.json').read_text());old=json.loads((OLD/'manifest.json').read_text());assert len(m['plates'])==14;actual=collections.Counter();gaps=[];edges=[]
for p in m['plates']:
 for idx,i in enumerate(p['items']):
  actual[(i['id'],i['original_object_name'],i['optional_sample'])]+=1;n=np.load(S/'parts'/f"{i['id']}.npz");v=np.r_[n['v'],n['fin_v'],n['teeth_v']]@np.array(i['rotation_matrix']).T+i['translation_mm'];b=np.r_[v.min(0),v.max(0)];assert abs(b-np.array(i['bounds_mm'])).max()<2e-5,(p['id'],i['id'],'bounds');assert b[2]>-1e-6 and b[5]<180;assert min(b[:2])>=4-1e-6 and max(b[3:5])<=176+1e-6;edges.append(min(*b[:2],*(180-b[3:5])))
  for j in p['items'][idx+1:]:
   c=np.array(j['bounds_mm']);g=float(np.linalg.norm(np.maximum(np.maximum(b[:2]-c[3:5],c[:2]-b[3:5]),0)));assert g>=6-1e-6;gaps.append(g)
expected=collections.Counter((i['id'],i['original_object_name'],p['optional'])for p in old['plates']for i in p['items']);assert actual==expected
put(S/'final_inventory459.json',dict(types=150,instances=sum(actual.values()),bed_mm=[180,180,180],minimum_edge_mm=float(min(edges)),minimum_bbox_gap_mm=float(min(gaps)),all_source_meshes_and_actual_instance_bounds_verified=True));print('FINAL_INVENTORY459_PASS',sum(actual.values()),flush=True)
