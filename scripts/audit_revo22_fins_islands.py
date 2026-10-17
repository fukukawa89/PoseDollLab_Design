import json,numpy as np
from build_revo22_fins import O,solid,polygon
from check_revo22_fins_islands import check
results=[]
for p in sorted((O/'parts').glob('*.npz')):
 r=check(p.stem);n=np.load(p);s=solid(n['v'],n['f'])
 for q in r['islands']:
  z=q['z_mid_mm'];bb=q['bounds'];prev=s.slice(z-.2)
  from shapely.geometry import box
  q['previous_model_xy_gap_mm']=float(box(*bb).distance(polygon(prev))) if prev.area()>0 else 999
 results.append(r)
 if r['islands']:print(p.stem,len(r['islands']),'max_area',round(max(x['area_mm2'] for x in r['islands']),3),'unsupported',sum(x['supported_fraction_within_1_6mm']<.9 and x['previous_model_xy_gap_mm']>1.6 for x in r['islands']),flush=True)
(O/'verification/source_island_review.json').write_text(json.dumps({'purpose':'Diagnostic: new cross-section islands in the combined model. A gap above a modeled fin can still trigger slicer floating-region warnings. XY buffer 1.6 mm is a diagnostic distance, not a tested bridge limit.','parts':results},indent=2),encoding='utf-8')