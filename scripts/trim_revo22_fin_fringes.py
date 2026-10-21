"""Trim sub-layer dangling fin fringes found by the independent layer audit."""
import sys,json,numpy as np
from build_revo22_fins import O,solid,md,box,vf,put,write_stl
for pid in sys.argv[1:]:
 n=np.load(O/'parts'/f'{pid}.npz');b=solid(n['fin_v'],n['fin_f']);t=solid(n['teeth_v'],n['teeth_f']);s=solid(n['v'],n['f']);removed=[]
 for attempt in range(3):
  changes=0;prev=b.slice(.1)
  for z in np.arange(.3,b.bounding_box()[5],.2):
   cur=b.slice(float(z))
   for c in cur.decompose():
    if c.area()<.02 or (c^prev.offset(.005)).area()>.00001:continue
    cut=c.offset(.25,circular_segments=12).extrude(.200002).translate([0,0,float(z)-.100001]);dv=float((b^cut).volume());b=b-cut;removed.append({'section_mid_z_mm':round(float(z),3),'removed_mm3':dv});changes+=1
   prev=b.slice(float(z))
  if not changes:break
 assert all(c.bounding_box()[2]<1e-5 for c in b.decompose())
 assert (b^s).volume()<1e-6
 np.savez_compressed(O/'parts'/f'{pid}.npz',v=n['v'],f=n['f'],fin_v=vf(b)[0],fin_f=vf(b)[1],teeth_v=n['teeth_v'],teeth_f=n['teeth_f'])
 report=json.loads((O/'design'/f'{pid}.json').read_text());report['support_layer_fringe_trims']=removed;report['supports_volume_mm3']=float((b+t).volume());put(O/'design'/f'{pid}.json',report);write_stl(O/'parts'/f'{pid}_fins.stl',b+t);print(pid,removed,flush=True)