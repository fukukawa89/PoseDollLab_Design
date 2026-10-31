"""Recover nominal CAD precision only when it matches the frozen print boundary."""
from pathlib import Path
import sys,json,numpy as np,trimesh,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf
from repair_revo22_f4_guarded_chamfer import context
from select_revo22_f4_repairs import select,O
from o22_mesh_identity import body_sha
B=O.parent;D=R/'.local/o22-nominal-reference';D.mkdir(exist_ok=True)
rows={q['id']:q for q in select()}
for pid in sys.argv[1:]:
 p=O/'candidates'/pid/rows[pid]['label'];d=json.loads((p/'design'/f'{pid}.json').read_text());parts,key,T=context(d,pid);Q=np.eye(4);Q[:3,:3]=d['orientation']['matrix'];Q[:3,3]=d['orientation']['source_translation_mm'];s=parts[key].transform((np.linalg.inv(Q)@T)[:3,:]);v,f=vf(s);a=solid(v,f);n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');old=trimesh.Trimesh(n['source_v'],n['f'],process=False);new=trimesh.Trimesh(v,f,process=False)
 def maxdist(target,points):return max(float(trimesh.proximity.closest_point(target,points[i:i+2048])[1].max()) for i in range(0,len(points),2048))
 dist=maxdist(old,np.r_[v,new.triangles_center]);dist2=maxdist(new,np.r_[n['source_v'],old.triangles_center]);r={'id':pid,'method':'Regenerated from the unchanged nominal O22 assembly CAD, registered with the original owner and bed transforms. Frozen print source is retained.','source_status':str(a.status()),'self_difference_mm3':float((a-a).volume()),'max_nominal_vertices_and_face_centers_distance_to_frozen_surface_mm':dist,'max_frozen_vertices_and_face_centers_distance_to_nominal_surface_mm':dist2,'max_bidirectional_sampled_boundary_distance_mm':max(dist,dist2),'old_volume_mm3':float(old.volume),'nominal_volume_mm3':float(new.volume),'nominal_mesh_sha256':body_sha({'v':v,'f':f}),'frozen_source_mesh_sha256':body_sha({'v':n['source_v'],'f':n['f']})};r['nominal_reference_qualified']=max(dist,dist2)<.0001 and abs(r['self_difference_mm3'])<1e-6 and str(a.status())=='Error.NoError';np.savez_compressed(D/f'{pid}.npz',v=v,f=f);(D/f'{pid}.json').write_text(json.dumps(r,indent=2));print('NOMINAL_REFERENCE',r,flush=True)
