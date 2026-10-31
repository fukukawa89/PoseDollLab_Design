import json,numpy as np,trimesh
from search_revo22_f5_orientation268 import O,OLD
from build_revo22_fins import solid,union,box,vf
from verify_revo22_f5_contacts298 import envelope
from o22_material_components import material_components
import repair_revo22_f4_guarded_chamfer as ctx
p='X046';a=O/'candidates'/p/'contact423';d=json.loads((a/'design'/f'{p}.json').read_text());n=np.load(a/'parts'/f'{p}.npz');old=np.load(OLD/'parts'/f'{p}.npz');ref=solid(old['v']@np.array(d['f4_to_current_matrix']).T+np.array(d['f4_to_current_translation_mm']),old['f']);s=solid(n['v'],n['f']);change=union(material_components((ref-s)^ref))+union(material_components((s-ref)^s));parts,key,T=ctx.context(d,p);Ti=np.linalg.inv(T);rm=change.transform(Ti[:3,:]);other=parts['chest/C02_magnet_screw_6.1'];env=envelope(other,rm);print('ENV',env.volume(),env.bounding_box());tm=trimesh.Trimesh(*vf(other),process=False)
for c in env.decompose():
 v,f=vf(c);samples=np.r_[v,v[f].mean(1)];_,dist,_=trimesh.proximity.closest_point(tm,samples);print('COMP',c.volume(),c.bounding_box(),'distance',dist.min(),dist.max())
print('Local',envelope(other.transform(T[:3,:]),change).volume())
