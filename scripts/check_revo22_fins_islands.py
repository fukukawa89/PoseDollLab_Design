from pathlib import Path
import json,numpy as np,sys
from build_revo22_fins import O,solid,union,polygon
from shapely.geometry import Point
def check(pid):
 n=np.load(O/'parts'/f'{pid}.npz');s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else None;t=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else None
 allsolid=union([x for x in [s,b,t] if x is not None]);previous=allsolid.slice(.1);found=[]
 for z in np.arange(.3,s.bounding_box()[5],.2):
  current=allsolid.slice(float(z))
  for c in current.decompose():
   if c.area()<.05 or (c^previous.offset(.01)).area()>.0001:continue
   source=c^s.slice(float(z))
   if source.area()<.01:role='support'
   else:role='part'
   below=(b.slice(float(z)-.4)+b.slice(float(z)-.2)) if b else c-c
   dist=polygon(c).distance(polygon(below)) if below.area()>0 else 999
   found.append(dict(z_mid_mm=round(float(z),3),area_mm2=c.area(),role=role,bounds=list(c.bounds()),support_xy_gap_mm=float(dist),supported_fraction_within_1_6mm=(c^below.offset(1.6)).area()/c.area() if below.area()>0 else 0))
  previous=current
 return dict(id=pid,islands=found)
if __name__=='__main__':
 for pid in sys.argv[1:]:
  r=check(pid);(O/'verification'/f'{pid}_islands.json').write_text(json.dumps(r,indent=2));print(pid,len(r['islands']),r['islands'][:12],flush=True)
