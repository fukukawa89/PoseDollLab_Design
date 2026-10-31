from pathlib import Path
import sys,json,numpy as np,shutil
from build_revo22_x062_open242 import S,put,sha
from build_revo22_fins import solid,vf,union,write_stl
from o22_material_components import material_components
from route_revo22_x062244 import tooth,sweep_convex
old=S/'candidates/X062/open242_h';out=S/'candidates/X062/open242_i'
for sub in ['parts','design','verification','projects','stl']:(out/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(old/'parts/X062.npz'));d=json.loads((old/'design/X062.json').read_text());body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);pieces=material_components(fin)
# Replace opposing crossed fingers with a common outward-removable fan on one existing fin.
base=d['local_route_repairs'][48];a=np.array(base['root']);direction=np.array(base['removal_vector'])
for idx in [102,113]:
 q=d['local_route_repairs'][idx];q.update(root=a.tolist(),new_bed_fin=False,removal_vector=direction.tolist(),free_vertical_mm=q['target'][2]-a[2]-.2,rerouted_to_common_fin=True)
 b=np.array(q['target'])+[0,0,.24];tt=tooth(a,b);cut=a+(b-a)*((q['cut_z_mm']-a[2])/(b[2]-a[2]));assert(sweep_convex(tooth(a,cut),direction*210)^body).volume()<1e-6
fin=union([p for j,p in enumerate(pieces)if j not in[24,28]])
allteeth=[]
for q in d['teeth']:
 a=np.array([q['x'],q['root_y'],max(.4,q['roof']-q['free_vertical_mm']-.3)]);b=np.array([q['x'],q['y'],q['roof']+.18]);allteeth.append(tooth(a,b))
for q in d['local_route_repairs']:
 a=np.array(q['root']);b=np.array(q['target'])+[0,0,.24];tt=tooth(a,b);assert(tt^fin).volume()>.005 and(tt^body).volume()>.005;allteeth.append(tt)
teeth=union(allteeth);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(out/'parts/X062.npz',**n);d.update(trial='open242_i',support_volume_mm3=float((fin+teeth).volume()),support_count=len(material_components(fin)),crossed_fingers_removed=True);put(out/'design/X062.json',d);geo=json.loads((old/'verification/geometry.json').read_text());geo.update(parts_npz_sha256=sha(out/'parts/X062.npz'),native_audit_pending=True);put(out/'verification/geometry.json',geo)
for name,obj in [('body',body),('fins',fin),('teeth',teeth),('combined',body+fin+teeth)]:write_stl(out/'stl'/f'X062_{name}.stl',obj)
print('REROUTED',d['support_count'],d['support_volume_mm3'],flush=True)
