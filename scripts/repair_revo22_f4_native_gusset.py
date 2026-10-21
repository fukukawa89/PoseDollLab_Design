from pathlib import Path
import sys,json,numpy as np,shapely
from o22_f3_gcode import extract_paths
from shapely.geometry import Point,box as box2
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import context,O
from build_revo22_fins import solid,vf,union,md,protected
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check

def trial(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));r=json.loads((src/'design'/f'{pid}.json').read_text());audit=check(pid,label);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);old=solid(n['v'],n['f']);new=old;parts,key,T=context(r,pid);offsets=np.array([[x,y,z] for x in [-.2,0,.2] for y in [-.2,0,.2] for z in [-.2,0,.2]]);guard_cache={};rows=[];rejected={};project=json.loads((src/'verification/local_extrusion.json').read_text())['project'];_,raw=extract_paths(src/'projects'/project,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];zs=np.unique(np.round(a[:,5],3));bead_cache={};vols=next((x['volumes'] for x in json.loads((O.parent/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects'] if x['part']==key),[]);ban=protected(vols).transform(np.c_[np.array(r['orientation']['matrix']),np.array(r['orientation']['source_translation_mm'])])
 for issue in audit['external_islands']:
  b=issue['bounds_mm'];z=issue['z_mm']-.1;points=(np.array([[x,y,z] for x in [b[0],b[2]] for y in [b[1],b[3]]])-t)@M;lo=points.min(0);hi=points.max(0);p=(lo+hi)/2;seed=polygon(new.slice(z+.2)).intersection(box2(lo[0]-.1,lo[1]-.1,hi[0]+.1,hi[1]+.1))
  if seed.is_empty:continue
  seed=seed.convex_hull;top=np.array(seed.exterior.coords)[:-1];top=np.c_[top,np.full(len(top),z+.1)];best=None
  for h in np.arange(.4,min(12.,z-.3)+.01,.4):
   zz=z-h;zp=float(zs[np.argmin(abs(zs-(zz+.1)))]);zz=zp-.1;h=z-zz
   if zp not in bead_cache:
    ar=a[abs(a[:,5]-zp)<.002];xy=(np.stack([ar[:,:2],ar[:,3:5]],axis=1)-t[:2])@M[:2,:2];bead_cache[zp]=shapely.union_all(shapely.buffer(shapely.linestrings(xy),ar[:,8]/2,quad_segs=6))
   prev=polygon(new.slice(zz)).buffer(-.15).intersection(bead_cache[zp])
   if prev.is_empty:continue
   near=nearest_points(prev,Point(p[:2]))[0];q=np.array([near.x,near.y]);di=p[:2]-q;distance=np.linalg.norm(di)
   if distance>.5*h:continue
   direction=di/max(distance,1e-12);c=q-direction*.45;angles=np.arange(8)*np.pi/4;botxy=c+np.c_[np.cos(angles),np.sin(angles)]*.6;bottom=np.c_[botxy,np.full(8,zz)];wedge=md.Manifold.hull_points(np.r_[top,bottom]);added=wedge-new
   if added.volume()>8. or added.volume()<1e-5:continue
   if (wedge^new).volume()<.03 or (added^ban).volume()>1e-7:continue
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
  else:rejected[str(z)]='No <=8 mm3 permanent fillet anchored to prior printed body and clear of functional voids and hardware +0.2 mm found.'
 added=new-old;assert len(material_components(new))==len(material_components(old));n['source_f']=n.get('source_f',n['f']).copy();n['v'],n['f']=vf(new);n['added_body_v'],n['added_body_f']=vf(added);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);rep=r.get('body_change',{});rep.update(kind='local_print_chamfer_and_permanent_gusset',additions=rows,added_volume_mm3=float(added.volume()),failed_gusset_sites=rejected,part_fit_and_motion_check_required=True,assembly_contact_validation_pending=True);r.update(source_mesh_preserved=False,body_change=rep);(dst/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('PERMANENT_GUSSET',pid,len(rows),float(added.volume()),rejected,flush=True);run(pid,newlabel);return check(pid,newlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:trial(*spec.split(':'))
