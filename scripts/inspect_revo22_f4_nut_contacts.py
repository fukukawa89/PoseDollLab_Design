from pathlib import Path
import sys,json,numpy as np,collections,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,md,union
import repair_revo22_f4_guarded_chamfer as ctx
from o22_reference_mesh import reference_mesh,reference_solid
O=ctx.O

def core_guards(s):
 v,f=vf(s);tm=trimesh.Trimesh(v,f,process=False);norm=tm.face_normals;tri=v[f];ds=np.sum(norm*tri.mean(1),axis=1);groups=collections.defaultdict(list);guards=[]
 for i,(nn,dd) in enumerate(zip(norm,ds)):groups[tuple(np.round(np.r_[nn,dd],5))].append(i)
 for indices in groups.values():
  if tm.area_faces[indices].sum()<.3:continue
  nn=norm[indices[0]];u=np.cross([0,0,1] if abs(nn[2])<.9 else [1,0,0],nn);u/=np.linalg.norm(u);vv=np.cross(nn,u);Q=np.array([u,vv,nn]);xy=tri[indices]@Q.T;cs=md.CrossSection([t[:,:2] for t in xy]).offset(-.15,circular_segments=8);z=float(ds[indices].mean())
  if not cs.is_empty():guards.append(cs.extrude(.08).translate([0,0,z]).transform(np.c_[Q.T,[0,0,0]]))
 return union(guards)

def assess(pid,label):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');design=json.loads((p/'design'/f'{pid}.json').read_text());parts,key,T=ctx.context(design,pid);meta=ctx.CACHE[1];M=np.array(design['orientation']['matrix']);t=np.array(design['orientation']['source_translation_mm']);rv,rf=reference_mesh(n,design);old=reference_solid(n,design).transform(np.linalg.inv(T)[:3,:]);new=solid(n['v'],n['f']).transform(np.linalg.inv(T)[:3,:]);removed=old-new;rows=[]
 for name,s in parts.items():
  sku=meta[name].get('sku') or ''
  if not sku.startswith('NUT_') or float(removed.min_gap(s,.08))>=.08:continue
  v,f=vf(s);tm=trimesh.Trimesh(v,f,process=False);norm=tm.face_normals;tri=v[f];ds=np.sum(norm*tri.mean(1),axis=1);groups=collections.defaultdict(list)
  for i,(nn,dd) in enumerate(zip(norm,ds)):groups[tuple(np.round(np.r_[nn,dd],5))].append(i)
  faces=[]
  for indices in groups.values():
   if tm.area_faces[indices].sum()<.3:continue
   nn=norm[indices[0]];u=np.cross([0,0,1] if abs(nn[2])<.9 else [1,0,0],nn);u/=np.linalg.norm(u);vv=np.cross(nn,u);Q=np.array([u,vv,nn]);xy=tri[indices]@Q.T;cs=md.CrossSection([t[:,:2] for t in xy]);z=float(ds[indices].mean());prism=cs.extrude(.08).translate([0,0,z]).transform(np.c_[Q.T,[0,0,0]]);before=float((old^prism).volume())
   if before<1e-5:continue
   lost=max(0,float((removed^prism).volume()));core=cs.offset(-.15,circular_segments=8);core_prism=core.extrude(.08).translate([0,0,z]).transform(np.c_[Q.T,[0,0,0]]) if not core.is_empty() else md.Manifold();core_loss=max(0,float((removed^core_prism).volume()));fraction=1-lost/before;faces.append({'normal_world':nn.tolist(),'face_area_mm2':float(cs.area()),'original_clearance_band_material_mm3':before,'removed_band_material_mm3':lost,'retained_band_fraction':fraction,'central_face_material_removed_mm3':core_loss,'passed':fraction>=.98 and core_loss<1e-6})
  approved=bool(faces) and all(q['passed'] for q in faces);rows.append({'part':name,'sku':sku,'qualified_corner_relief':approved,'face_checks':faces,'scope':'Within a 0.08 mm clearance band outside every nut planar face with original surrounding material, retain at least 98% of material and preserve the face core 0.15 mm from its edges. This protects nominal flat spacing and bearing centers, without claiming a load test.'});print('NUT_CONTACT',pid,name,approved,len(faces),flush=True)
 (p/'verification/nut_contact_surfaces.json').write_text(json.dumps(rows,indent=2));return rows
if __name__=='__main__':assess(*sys.argv[1:])
