from pathlib import Path
import sys,json,time
import numpy as np
from build_revo22_fins import O,solid
from check_revo22_fins_islands import check

def verify(pid):
 n=np.load(O/'parts'/f'{pid}.npz');issues=[];layers=0;maxz=0
 if len(n['fin_f']):
  b=solid(n['fin_v'],n['fin_f']);maxz=b.bounding_box()[5];previous=b.slice(.1)
  for z in np.arange(.3,maxz,.2):
   cur=b.slice(float(z));layers+=1
   for c in cur.decompose():
    if c.area()>.02 and (c^previous.offset(.005)).area()<.00001:
     issues.append({'z_mid_mm':round(float(z),3),'area_mm2':c.area(),'bounds':list(c.bounds())})
   previous=cur
  roots=all(c.bounding_box()[2]<1e-5 for c in b.decompose())
 else:roots=True
 return {'id':pid,'checked_layers':layers,'body_components_all_on_bed':roots,'unsupported_body_layer_islands':issues}

if __name__=='__main__':
 results=[]
 for p in sorted((O/'parts').glob('*.npz')):
  r=verify(p.stem);results.append(r);print(p.stem,len(r['unsupported_body_layer_islands']),flush=True)
 (O/'verification/body_layer_continuity.json').write_text(json.dumps({'layer_height_mm':.2,'first_layer_mm':.2,'section_midpoints_mm':[.1,.3],'minimum_component_area_mm2':.02,'maximum_previous_layer_xy_buffer_mm':.005,'unique_parts':len(results),'all_body_components_on_bed':all(r['body_components_all_on_bed'] for r in results),'unsupported_body_layer_island_count':sum(len(r['unsupported_body_layer_islands']) for r in results),'parts':results},indent=2),encoding='utf-8')