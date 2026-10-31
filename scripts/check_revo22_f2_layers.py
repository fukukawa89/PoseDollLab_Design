from pathlib import Path
import json,sys,time
import numpy as np
from build_revo22_fins_v2 import O,solid,union

def check(pid):
 n=np.load(O/'parts'/f'{pid}.npz');s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else None;t=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else None
 whole=union([p for p in [s,b,t] if p is not None]);last=whole.slice(.1);lastbody=b.slice(.1) if b else None;issues=[];bissues=[];over=[]
 for z in np.arange(.3,whole.bounding_box()[5],.2):
  curr=whole.slice(float(z));cb=b.slice(float(z)) if b else None
  for c in curr.decompose():
   if c.area()>.03 and (c^last.offset(.025)).area()<1e-6:issues.append({'z_mm':round(float(z),2),'area_mm2':c.area(),'bounds':list(c.bounds())})
  if b:
   for c in cb.decompose():
    if c.area()>.03 and (c^lastbody.offset(.01)).area()<1e-6:bissues.append({'z_mm':round(float(z),2),'area_mm2':c.area()})
  cc=s.slice(float(z))-last.offset(2.0)
  if cc.area()>.5:over.append({'z_mm':round(float(z),2),'unbacked_beyond_2mm_area':cc.area(),'bounds':list(cc.bounds())})
  last=curr;lastbody=cb
 r={'id':pid,'layer_height_mm':.2,'combined_floating_islands':issues,'fin_floating_islands':bissues,'long_overhang_layers':over}
 (O/'verification'/f'{pid}_layers.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(pid,'islands',len(issues),'fin',len(bissues),'long overhangs',len(over),'maxarea',round(max([x['unbacked_beyond_2mm_area'] for x in over],default=0),2),flush=True)
if __name__=='__main__':
 for pid in sys.argv[1:]:check(pid)