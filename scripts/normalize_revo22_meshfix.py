from pathlib import Path
import sys,json,numpy as np,trimesh,pymeshfix
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'));from build_revo22_fins import solid
B=R/'Hardware/PoseDoll44/bench/revO22';D=R/'.local/o22-cleaned-source-meshfix';D.mkdir(exist_ok=True)
for pid in sys.argv[1:]:
 n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');fix=pymeshfix.MeshFix(n['source_v'],n['f'],verbose=False);fix.repair(joincomp=False,remove_smallest_components=False);v=np.array(fix.points);f=np.array(fix.faces);m=trimesh.Trimesh(v,f,process=False);old=trimesh.Trimesh(n['source_v'],n['f'],process=False);s=solid(v,f)
 def maxdist(target,points):
  return max(float(trimesh.proximity.closest_point(target,points[i:i+2048])[1].max()) for i in range(0,len(points),2048))
 dist=maxdist(old,np.r_[v,m.triangles_center]);dist2=maxdist(m,np.r_[n['source_v'],old.triangles_center]);d={'id':pid,'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'status':str(s.status()),'self_difference_mm3':float((s-s).volume()),'max_repaired_vertices_and_face_centers_distance_to_frozen_surface_mm':dist,'max_frozen_vertices_and_face_centers_distance_to_repaired_surface_mm':dist2,'old_volume_mm3':float(old.volume),'new_volume_mm3':float(m.volume),'method':'MeshFix repair, joincomp=False, remove_smallest_components=False; source mesh retained separately.'};np.savez_compressed(D/f'{pid}.npz',v=v,f=f,source_v=n['source_v'],source_f=n['f']);(D/f'{pid}.json').write_text(json.dumps(d,indent=2));print('MESHFIX_REFERENCE',d,flush=True)
