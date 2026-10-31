from pathlib import Path
import numpy as np,trimesh,sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'));from build_revo22_fins import solid
D=R/'.local/o22-cleaned-source-v4';D.mkdir(exist_ok=True)
for pid in sys.argv[1:]:
 n=np.load(R/'.local/o22-cleaned-source-v2'/f'{pid}.npz');m=trimesh.Trimesh(n['v'],n['f'],process=False);changes=[]
 for _ in range(5):
  count=np.bincount(m.edges_unique_inverse);each=count[m.edges_unique_inverse.reshape(-1,3)];ids=np.flatnonzero((each>2).all(axis=1))
  if not len(ids):break
  i=int(ids[np.argmin(m.area_faces[ids])]);changes.append({'kind':'remove_face_with_three_nonmanifold_edges','area_mm2':float(m.area_faces[i]),'vertices_mm':m.triangles[i].tolist()});mask=np.ones(len(m.faces),bool);mask[i]=False;m.update_faces(mask)
 before=len(m.faces);trimesh.repair.fill_holes(m);changes.append({'kind':'close_triangular_or_quad_boundaries','added_face_count':len(m.faces)-before});s=solid(m.vertices,m.faces);d={'id':pid,'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'status':str(s.status()),'self_difference_mm3':float((s-s).volume()),'changes':changes,'volume_mm3':float(m.volume)};np.savez_compressed(D/f'{pid}.npz',v=m.vertices,f=m.faces,source_v=n['source_v'],source_f=n['source_f']);(D/f'{pid}.json').write_text(json.dumps(d,indent=2));print(d,flush=True)
