"""Inspect tiny screw-shank clearance reliefs separately from load-bearing head faces."""
from pathlib import Path
import sys,json,numpy as np,collections,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,md,union,box
import repair_revo22_f4_guarded_chamfer as ctx
from o22_reference_mesh import reference_mesh,reference_solid
O=ctx.O
def assess(pid,label):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());parts,key,T=ctx.context(d,pid);meta=ctx.CACHE[1];M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);rv,rf=reference_mesh(n,d);old=reference_solid(n,d);new=solid(n['v'],n['f']);roi=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:]) for q in d['body_change']['chamfers']]);removed=((old-new)^roi).transform(np.linalg.inv(T)[:3,:]);old=old.transform(np.linalg.inv(T)[:3,:]);rows=[]
 def probe(s,m):return union([s.translate([x,y,z]) for x in [-m,0,m] for y in [-m,0,m] for z in [-m,0,m]])
 for name,s in parts.items():
  sku=meta[name].get('sku') or ''
  if not sku.startswith('SCREW_') or float(removed.min_gap(s,.08))>=.08:continue
  near=max(0,float((removed^probe(s,.08)).volume()))
  if near<1e-6:continue
  tight=max(0,float((removed^probe(s,.02)).volume()));A=np.array(meta[name]['transform']);inv=np.linalg.inv(A);ss=s.transform(inv[:3,:]);rr=removed.transform(inv[:3,:]);oo=old.transform(inv[:3,:]);v,f=vf(ss);tm=trimesh.Trimesh(v,f,process=False);tri=v[f];norm=tm.face_normals;groups=collections.defaultdict(list)
  for i,nn in enumerate(norm):
   if abs(nn[2])>.99999:groups[(int(np.sign(nn[2])),round(float(tri[i,:,2].mean()),5))].append(i)
  faces=[]
  for (sign,z),ids in groups.items():
   cs=md.CrossSection([a[:,:2][::sign] for a in tri[ids]])
   if cs.area()<.02:continue
   slab=cs.extrude(.08).translate([0,0,z if sign>0 else z-.08]);before=max(0,float((oo^slab).volume()));lost=max(0,float((rr^slab).volume()))
   if before>1e-5:faces.append({'z_local_mm':z,'normal_sign':sign,'original_head_face_band_mm3':before,'removed_head_face_band_mm3':lost,'passed':lost<1e-6})
  ok=near<=.02 and tight<1e-6 and all(q['passed'] for q in faces);rows.append({'part':name,'sku':sku,'removed_within_008mm_margin_mm3':near,'removed_within_002mm_margin_mm3':tight,'axial_bearing_face_checks':faces,'qualified_clearance_corner_relief':ok,'scope':'At most 0.02 mm3 is removed within the 0.08 mm screw clearance envelope; no removed material lies in the 0.02 mm envelope, and every originally contacted axial screw face retains its full 0.08 mm contact band. This qualifies a local free-clearance corner, not a thread or screw-head bearing modification. No strength test is claimed.'});print('SCREW_CLEARANCE',pid,name,ok,'near',near,'tight',tight,flush=True)
 (p/'verification/screw_clearance_contacts.json').write_text(json.dumps(rows,indent=2));return rows
if __name__=='__main__':assess(*sys.argv[1:])
