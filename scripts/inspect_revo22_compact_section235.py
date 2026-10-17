"""Capture an area-preservation failure without changing the native audit classification."""
from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import verify_revo22_f4_full_bead as full
import o22_recover_native_flag_paths as recover
S=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4/compact230';old=full.polygon
def inspect(cs):
 try:return old(cs)
 except AssertionError:
  import shapely
  from shapely.geometry import Polygon
  info={'manifold_area':cs.area(),'regions':[]}
  for region in cs.decompose():
   rings=[np.asarray(q)for q in region.to_polygons()];positive=[];negative=[]
   for q in rings:
    area2=np.sum(q[:,0]*np.roll(q[:,1],-1)-np.roll(q[:,0],-1)*q[:,1]);(positive if area2>0 else negative).append(q)
   polys=[]
   if len(positive)==1:
    p=Polygon(positive[0],negative);polys=[{'valid':p.is_valid,'reason':shapely.is_valid_reason(p),'signed_area':p.area,'linework_area':shapely.make_valid(p).area,'structure_area':shapely.make_valid(p,method='structure',keep_collapsed=False).area}]
   info['regions'].append({'area':region.area(),'positive_count':len(positive),'negative_count':len(negative),'polygons':polys,'rings':[q.tolist()for q in rings]})
  (S/'section_failure235.json').write_text(json.dumps(info,indent=2));print('SECTION235',info['manifold_area'],[{k:v for k,v in q.items()if k!='rings'}for q in info['regions']if any(not p['valid']for p in q['polygons'])],flush=True);raise
full.O=S;recover.O=S;full.polygon=inspect
full.check('PLATE_C03','native')
