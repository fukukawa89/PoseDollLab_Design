from pathlib import Path
import sys,json,numpy as np
from shapely.geometry import Point,box as box2
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import context,O
from build_revo22_fins import solid,vf,union,md
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check

def trial(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());audit=check(pid,label);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);old=solid(n['v'],n['f']);new=old;parts,key,T=context(r,pid);offsets=np.array([[x,y,z] for x in [-.08,0,.08] for y in [-.08,0,.08] for z in [-.08,0,.08]]);guard_cache={};rows=[];rejected={}
 for issue in audit['external_islands']:
  b=issue['bounds_mm'];z=issue['z_mm']-.1;points=(np.array([[x,y,z] for x in [b[0],b[2]] for y in [b[1],b[3]]])-t)@M;lo=points.min(0);hi=points.max(0);p=(lo+hi)/2;seed=polygon(new.slice(z+.1)).intersection(box2(lo[0]-.03,lo[1]-.03,hi[0]+.03,hi[1]+.03))
  if seed.is_empty:continue
  seed=seed.convex_hull;top=np.array(seed.exterior.coords)[:-1];top=np.c_[top,np.full(len(top),z+.1)];best=None
  for h in np.arange(.4,4.01,.2):
   zz=z-h;prev=polygon(new.slice(zz))
   if prev.is_empty:continue
   near=nearest_points(prev,Point(p[:2]))[0];q=np.array([near.x,near.y]);di=p[:2]-q;distance=np.linalg.norm(di)
   if distance>.75*h:continue
   direction=di/max(distance,1e-12);c=q-direction*.3;angles=np.arange(8)*np.pi/4;botxy=c+np.c_[np.cos(angles),np.sin(angles)]*.36;bottom=np.c_[botxy,np.full(8,zz)];wedge=md.Manifold.hull_points(np.r_[top,bottom]);added=wedge-new
   if added.volume()>5. or added.volume()<1e-5:continue
   if (wedge^new).volume()<.02:continue
   wa=added.transform(np.linalg.inv(T)[:3,:]);bb=np.array(wa.bounding_box());guards=[];nearparts=[]
   for k,s in parts.items():
    if k==key:continue
    sb=np.array(s.bounding_box());sep=np.maximum(np.maximum(sb[:3]-bb[3:],bb[:3]-sb[3:]),0)
    if np.linalg.norm(sep)>.3:continue
    if float(wa.min_gap(s,.3))>.18:continue
    if k not in guard_cache:
     guard_cache[k]=union([s.translate(v) for v in offsets]).transform(T[:3,:])
    guards.append(guard_cache[k]);nearparts.append(k)
   collision=float((added^union(guards)).volume())
   if collision>1e-6:continue
   score=float(added.volume())+h*.1
   if best is None or score<best[0]:best=(score,wedge,added,h,distance,nearparts)
  if best:
   _,wedge,added,h,distance,nearparts=best;new=new+wedge;rows.append({'native_island':issue,'local_bounds_mm':list(added.bounding_box()),'added_volume_mm3':float(added.volume()),'height_mm':float(h),'horizontal_reach_mm':float(distance),'protected_neighbors':nearparts,'permanent_part_feature':True})
  else:rejected[str(z)]='No <=3 mm3, bed-printable wedge clear of actual neighboring hardware found.'
 added=new-old;assert len(material_components(new))==len(material_components(old));n['source_f']=n.get('source_f',n['f']).copy();n['v'],n['f']=vf(new);n['added_body_v'],n['added_body_f']=vf(added);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);rep=r.get('body_change',{});rep.update(kind='local_print_chamfer_and_permanent_gusset',additions=rows,added_volume_mm3=float(added.volume()),failed_gusset_sites=rejected,part_fit_and_motion_check_required=True,assembly_contact_validation_pending=True);r.update(source_mesh_preserved=False,body_change=rep);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('PERMANENT_GUSSET',pid,len(rows),float(added.volume()),rejected,flush=True);run(pid,newlabel);return check(pid,newlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:trial(*spec.split(':'))
