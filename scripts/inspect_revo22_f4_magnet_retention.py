"""Separate geometric assessment of M2 magnet-cap retention pockets.
This does not relax joint-nut screening. The screw-facing bearing wall and its
one-millimetre backing must remain exactly unchanged. Only the opposite entry
edge may be relieved. No force/creep qualification is implied.
"""
from pathlib import Path
import sys,json,numpy as np,collections,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,md
import repair_revo22_f4_guarded_chamfer as ctx
from o22_reference_mesh import reference_mesh,reference_solid
O=ctx.O

def assess(pid,label):
 p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());parts,key,T=ctx.context(d,pid);rv,rf=reference_mesh(n,d);M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);old=reference_solid(n,d).transform(np.linalg.inv(T)[:3,:]);new=solid(n['v'],n['f']).transform(np.linalg.inv(T)[:3,:]);removed=old-new;rows=[]
 for name,s in parts.items():
  if 'magnet_nut_' not in name or ctx.CACHE[1][name].get('sku')!='NUT_M2' or float(removed.min_gap(s,.08))>=.08:continue
  screwname=name.replace('magnet_nut_','magnet_screw_')
  if screwname not in parts or ctx.CACHE[1][screwname].get('sku') not in ['SCREW_M2_L4','SCREW_M2_L5']:continue
  sv,sf=vf(parts[screwname]);sc=trimesh.Trimesh(sv,sf,process=False).center_mass;v,f=vf(s);tm=trimesh.Trimesh(v,f,process=False);nc=tm.bounds.mean(0);norm=tm.face_normals;tri=v[f];ds=np.sum(norm*tri.mean(1),axis=1);groups=collections.defaultdict(list)
  for i,(nn,dd) in enumerate(zip(norm,ds)):groups[tuple(np.round(np.r_[nn,dd],5))].append(i)
  largest=max(groups.values(),key=lambda inds:tm.area_faces[inds].sum());axis=norm[largest[0]].copy();axis*=1 if np.dot(axis,sc-nc)>0 else -1;faces=[]
  for inds in groups.values():
   if tm.area_faces[inds].sum()<.3:continue
   nn=norm[inds[0]];u=np.cross([0,0,1] if abs(nn[2])<.9 else [1,0,0],nn);u/=np.linalg.norm(u);vv=np.cross(nn,u);Q=np.array([u,vv,nn]);xy=tri[inds]@Q.T;cs=md.CrossSection([t[:,:2] for t in xy]);z=float(ds[inds].mean());alignment=float(np.dot(nn,axis));kind='screw_facing_loaded_wall' if alignment>.99 else 'opposite_entry_wall' if alignment<-.99 else 'anti_rotation_flat';bands=[]
   for depth in [.08,.2,.5,1.]:
    prism=cs.extrude(depth).translate([0,0,z]).transform(np.c_[Q.T,[0,0,0]]);before=max(0.,float((old^prism).volume()));loss=max(0.,float((removed^prism).volume()));inset=.15 if kind=='opposite_entry_wall' else .25;core=cs.offset(-inset,circular_segments=8);cp=core.extrude(depth).translate([0,0,z]).transform(np.c_[Q.T,[0,0,0]]);cl=max(0.,float((removed^cp).volume()));bands.append({'depth_mm':depth,'original_material_mm3':before,'removed_mm3':loss,'retained_fraction':1-loss/before if before>1e-7 else 1.,'core_inset_mm':inset,'core_removed_mm3':cl})
   if kind=='screw_facing_loaded_wall':ok=bands[-1]['removed_mm3']<1e-6 and bands[-1]['original_material_mm3']>.05
   elif kind=='opposite_entry_wall':ok=bands[0]['retained_fraction']>=.95 and bands[0]['core_removed_mm3']<1e-6 and bands[-1]['retained_fraction']>=.70
   else:ok=all(b['retained_fraction']>=.99 and b['core_removed_mm3']<1e-6 for b in bands[:3])
   faces.append({'kind':kind,'normal_world':nn.tolist(),'area_mm2':float(cs.area()),'bands':bands,'passed':ok})
  passes=all(f['passed'] for f in faces) and sum(f['kind']=='screw_facing_loaded_wall' for f in faces)==1 and abs(float(np.dot(axis,sc-nc)))>.5
  rows.append({'part':name,'screw_part':screwname,'screw_facing_axis_world':axis.tolist(),'qualified_magnet_retention_entry_relief':passes,'face_checks':faces,'criteria':'Magnet-cap M2 nuts only, independently identified by matching magnet_screw hardware. Entire screw-facing bearing footprint and existing material through 1 mm remain unchanged. Opposite unloaded entry-face band retains >=95% and its 0.15 mm inset core, with >=70% of existing 1 mm backing. Anti-rotation flats retain >=99% through 0.5 mm and their 0.25 mm inset cores. Screw and nut geometry/position are unchanged. This is geometry screening, not a strength/creep test.','source_design_evidence':'cad/revO15/twist.py: sensor-cap M2x4 screws and magnet_nut pockets; radial M3 brake and captured rotor collar are separate.'})
 (p/'verification/magnet_retention_load_faces.json').write_text(json.dumps(rows,indent=2));print('MAGNET_RETENTION',pid,[(q['part'],q['qualified_magnet_retention_entry_relief'])for q in rows],flush=True);return rows
if __name__=='__main__':assess(*sys.argv[1:])
