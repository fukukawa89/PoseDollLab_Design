from pathlib import Path
import sys,json,numpy as np,trimesh,shapely
from shapely.geometry import Polygon
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid
B=R/'Hardware/PoseDoll44/bench/revO22';D=R/'.local/o22-cleaned-source-v3';D.mkdir(exist_ok=True)
for pid in sys.argv[1:]:
 n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');v=n['source_v'];f=n['f'];tm=trimesh.Trimesh(v,f,process=False);tri=v[f];z=20.2;flat=(np.max(abs(tri[:,:,2]-z),axis=1)<1e-7);parts=[tri[~flat]];rep=[]
 for sign in [-1,1]:
  mask=flat & (tm.face_normals[:,2]*sign>.99);tris=tri[mask];polys=[Polygon(t[:,:2]) for t in tris if Polygon(t[:,:2]).area>1e-15];region=shapely.union_all(polys);out=shapely.constrained_delaunay_triangles(region);patch=[]
  for t in out.geoms:
   xy=np.array(t.exterior.coords)[:3];ab=xy[1]-xy[0];ac=xy[2]-xy[0];cross=ab[0]*ac[1]-ab[1]*ac[0];xy=xy if cross*sign>0 else xy[::-1];patch.append(np.c_[xy,np.full(3,z)])
  parts.append(np.array(patch));rep.append({'normal':sign,'input_faces':int(mask.sum()),'output_faces':len(patch),'union_area_mm2':float(region.area),'input_area_sum_mm2':float(sum(p.area for p in polys))})
 alltri=np.concatenate(parts);mesh=trimesh.Trimesh(alltri.reshape(-1,3),np.arange(len(alltri)*3).reshape(-1,3),process=False);mesh.merge_vertices(digits_vertex=8);s=solid(mesh.vertices,mesh.faces);result={'id':pid,'coplanar_plane_z_mm':z,'patches':rep,'watertight':bool(mesh.is_watertight),'status':str(s.status()),'self_difference_mm3':float((s-s).volume()),'old_volume_mm3':float(tm.volume),'new_volume_mm3':float(mesh.volume)};np.savez_compressed(D/f'{pid}.npz',v=mesh.vertices,f=mesh.faces,source_v=v,source_f=f);(D/f'{pid}.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
