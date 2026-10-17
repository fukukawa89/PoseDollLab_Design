import sys,json,numpy as np
from build_revo22_x062_open242 import S,put,sha
from build_revo22_fins import solid,vf,union,box,write_stl
from o22_material_components import material_components
from route_revo22_x062244 import tooth,sweep_convex
old=S/'candidates/X062/open242_l';out=S/'candidates/X062/open242_m'
for sub in ['parts','design','verification','projects','stl']:(out/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(old/'parts/X062.npz'));d=json.loads((old/'design/X062.json').read_text());body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);oldroot=np.array(d['local_route_repairs'][109]['root']);pieces=material_components(fin);remove=[i for i,p in enumerate(pieces)if(p^box(oldroot-.15,oldroot+.15)).volume()>.001];assert len(remove)==1,remove
for index,parent in [(109,48),(116,50)]:
 q=d['local_route_repairs'][index];r=d['local_route_repairs'][parent];a=np.array(r['root']);b=np.array(q['target'])+[0,0,.24];direction=np.array(r['removal_vector']);cut=a+(b-a)*((q['cut_z_mm']-a[2])/(b[2]-a[2]));assert(sweep_convex(tooth(a,cut),direction*210)^body).volume()<1e-6;q.update(root=a.tolist(),new_bed_fin=False,removal_vector=direction.tolist(),free_vertical_mm=q['target'][2]-a[2]-.2,rerouted_to_common_fin=True)
fin=union([p for i,p in enumerate(pieces)if i not in remove]);ts=[]
for q in d['teeth']:
 a=np.array([q['x'],q['root_y'],max(.4,q['roof']-q['free_vertical_mm']-.3)]);b=np.array([q['x'],q['y'],q['roof']+.18]);ts.append(tooth(a,b))
for q in d['local_route_repairs']:
 tt=tooth(np.array(q['root']),np.array(q['target'])+[0,0,.24]);assert(tt^fin).volume()>.005;ts.append(tt)
teeth=union(ts);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(out/'parts/X062.npz',**n);d.update(trial='open242_m',support_count=len(material_components(fin)),support_volume_mm3=float((fin+teeth).volume()));put(out/'design/X062.json',d);geo=json.loads((old/'verification/geometry.json').read_text());geo.update(parts_npz_sha256=sha(out/'parts/X062.npz'),native_audit_pending=True);put(out/'verification/geometry.json',geo)
for name,obj in [('body',body),('fins',fin),('teeth',teeth),('combined',body+fin+teeth)]:write_stl(out/'stl'/f'X062_{name}.stl',obj)
print('CROSSING_FANS_RESOLVED',d['support_count'],flush=True)
