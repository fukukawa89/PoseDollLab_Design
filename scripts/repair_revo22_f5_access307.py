"""Create a small protected access slot only when a bed fin is blocked by the body."""
import sys,json,math,shutil,traceback,concurrent.futures,numpy as np,trimesh
from shapely.geometry import LineString
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,union,box,md
from o22_material_components import material_components
from verify_revo22_f5_contacts298 import envelope,run as fit
from verify_revo22_x062_removal245 import exact_clear
from build_revo22_f5_precise_guards283 import run as makeguards
from route_revo22_x062244 import tooth
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geometry
from optimize_revo22_f5_276 import pick,candidates
import repair_revo22_f4_guarded_chamfer as ctx

def create(pid,src,label):
 a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if(b/'parts'/f'{pid}.npz').exists():return True
 n=dict(np.load(a/'parts'/f'{pid}.npz'));d=json.loads((a/'design'/f'{pid}.json').read_text());rep=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);ts=solid(n['teeth_v'],n['teeth_f']);mesh=trimesh.Trimesh(n['v'],n['f'],process=False);makeguards(pid);gn=np.load(O/'guards_precise'/f'{pid}.npz');guard=solid(gn['v'],gn['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);parts,key,T=ctx.context(d,pid);neighbors=[];bb=np.array(s.bounding_box())
 for k,other in parts.items():
  if k==key:continue
  q=other.transform(T[:3,:]);ob=np.array(q.bounding_box());sep=np.maximum(np.maximum(ob[:3]-bb[3:],bb[:3]-ob[3:]),0)
  if np.linalg.norm(sep)<.5:neighbors.append(q)
 requests=[]
 for q in rep['external_islands']:
  r=q['bounds_mm'];requests.append((np.array([(r[0]+r[2])/2,(r[1]+r[3])/2,q['z_mm']])-t)@M)
 for q in rep['critical_external_runs']:
  line=LineString(q['xy_mm']);ct=max(1,int(math.ceil(line.length/2.)));requests +=[(np.r_[line.interpolate(x).coords[0],q['z_mm']]-t)@M for x in(np.arange(ct)+.5)*line.length/ct]
 changes=[];records=[];reasons={};offsets=np.array([[x,y,z]for x in[-.32,.32]for y in[-.32,.32]for z in[-.32,.32]])
 def rejected(reason):reasons[reason]=reasons.get(reason,0)+1
 for target in requests:
  surfaces=[]
  samples=np.array([[target[0]+dx,target[1]+dy,target[2]-.1]for dx,dy in [(0,0)]+[(r*math.cos(an),r*math.sin(an))for r in[.5,1.,1.5,2.]for an in np.arange(0,2*np.pi,np.pi/4)]])
  close,dist,face=trimesh.proximity.closest_point(mesh,samples)
  for h,di,fi in zip(close,dist,face):
   norm=mesh.face_normals[fi]
   if di<.8 and abs(h[2]-target[2])<.65 and norm[2]<.75:surfaces.append((h,h-norm*.22+[0,0,.1]))
  hh,_,ff=mesh.ray.intersects_location([[q[0],q[1],-.1]for q in samples],np.tile([0,0,1.],(len(samples),1)),multiple_hits=True)
  for h,fi in zip(hh,ff):
   if abs(h[2]-target[2])<1.1 and mesh.face_normals[fi,2]<-.15:surfaces.append((h,h+[0,0,.25]))
  surfaces.sort(key=lambda q:np.linalg.norm(q[0]-target));seen=set();success=False
  for h,tip in surfaces:
   ky=tuple(np.round(tip,3))
   if ky in seen:continue
   seen.add(ky);roof=h[2];tip[2]=max(tip[2],target[2]+.2)
   if roof<4:continue
   if (tooth(tip-[0,0,.15],tip,w=.6)^(guard-s)).volume()>1e-6:rejected('tip_guard');continue
   for gap in[5.2,3.2]:
    az=roof-gap
    if az<.5:continue
    for angle in [0,np.pi/2,np.pi/4,-np.pi/4]:
     u=np.array([math.cos(angle),math.sin(angle)]);perp=np.array([-u[1],u[0]]);root=np.r_[h[:2],az];w=max(4.5,az*.28);thick=1.2 if az<60 else 1.6;pts=[]
     for center,z,width in[(root[:2],0,w),(root[:2],az+.2,1.9)]:
      for l,k in[(-1,-1),(1,-1),(1,1),(-1,1)]:pts.append([*(center+u*l*width/2+perp*k*thick/2),z])
     core=md.Manifold.hull_points(np.array(pts));core+=core.slice(.1).offset(.8,circular_segments=8).extrude(.4);tt=tooth(root,tip,w=.6);bite=tt^s
     if not .008<bite.volume()<2.5:rejected('bite');continue
     if(tt^(guard-s)).volume()>1e-6:rejected('tooth_guard');continue
     cv=vf(core)[0];expanded=md.Manifold.hull_points((cv[:,None]+offsets[None]).reshape(-1,3));stem=tooth(root,tip-[0,0,.55],w=1.2);cut=(expanded+stem)^box(bb[:3]-1,[*list(bb[3:5]+1),roof-.42]);delta=s^cut
     if delta.volume()<.0001 or delta.volume()>min(16.,s.volume()*.003):rejected('cut_budget');continue
     protected=union([envelope(other,delta,margin=.12)for other in neighbors]);cut-=protected;delta=s^cut;proposal=s-cut
     if(core^proposal).volume()>1e-6:rejected('protected_body_blocks_fin');continue
     if len(material_components(proposal))!=len(material_components(s)):rejected('body_split');continue
     if(tt^proposal).volume()<.005:rejected('no_contact');continue
     if(tt^(guard-proposal)).volume()>1e-6:rejected('new_tooth_guard');continue
     total=solid(n.get('f5_pre_relief_v',n['v']),n.get('f5_pre_relief_f',n['f']))-proposal
     if total.volume()>min(20.,s.volume()*.004):rejected('total_budget');continue
     if not exact_clear(core,proposal,np.array([0,0,-250.]))[0]:rejected('withdrawal');continue
     allgeom=proposal+fin+ts+core+tt;ab=np.array(allgeom.bounding_box())
     if np.any((ab[3:]-ab[:3])[:2]>172):rejected('bed');continue
     s=proposal;fin+=core;ts+=tt;roi=np.array(cut.bounding_box());changes.append(dict(kind='noncontact_fin_access_slot',local_bounds_mm=roi.tolist(),removed_volume_mm3=float(delta.volume()),native_target_mm=target.tolist(),actual_neighbor_protection_mm=.12));records.append(dict(target=h.tolist(),tip=tip.tolist(),root=root.tolist(),neck_xy_mm=[.6,.6],tip_width_mm=.6,free_vertical_mm=gap-.2,new_bed_fin=True,removal_vector=[0,0,-1],kind='access_slot_fin'));success=True;break
    if success:break
   if success:break
  if success:break
 if not changes:print('ACCESS307_NONE',pid,src,reasons,flush=True);return False
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n.setdefault('f5_pre_relief_v',n['v'].copy());n.setdefault('f5_pre_relief_f',n['f'].copy());n['v'],n['f']=vf(s);ts=union([c for c in material_components(ts)if(c^s).volume()>.005 and(c^fin).volume()>.005]);fin=union([c for c in material_components(fin)if(c^ts).volume()>.005]);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{pid}.npz',**n);gv,gf=vf(guard);np.savez_compressed(b/'verification/guards.npz',v=gv,f=gf);d.update(trial=label,part_body_modified_from_F4=True,body_rigid_transform_only=False,body_f4_faces_identical=False,f5_reliefs=d.get('f5_reliefs',[])+changes,f5_removed_volume_mm3=float((solid(n['f5_pre_relief_v'],n['f5_pre_relief_f'])-s).volume()),fit_and_pose_pending=True,new_tooth_count=d['new_tooth_count']+len(records),local_route_repairs=d.get('local_route_repairs',[])+records,support_count=len(material_components(fin)),support_volume_mm3=float((fin+ts).volume()),removable_core_may_transit_empty_hardware_space=True);put(b/'design'/f'{pid}.json',d);print('ACCESS307_BUILT',pid,label,d['f5_removed_volume_mm3'],reasons,flush=True);return True

def run(pid):
 if pick(pid):return(pid,True)
 choices=[q for q in candidates(pid)if not q[4].get('part_body_modified_from_F4',False)and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))];current=choices[0][2]
 for step in range(4):
  label=f'access307_{step}'
  if not create(pid,current,label):break
  q=audit(pid,label)
  if q['native_review_resolved']:
   pick(pid);geometry(pid);assert fit(pid)['fit_and_pose_geometry_passed'];return(pid,True)
  current=label
 return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  fs={ex.submit(run,p):p for p in(sys.argv[1:]or['P001','P033','P049','P051','P073','W002','W006','W007','W016','W017','P130'])}
  for f in concurrent.futures.as_completed(fs):
   try:print('ACCESS307_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('ACCESS307_ERROR',fs[f],flush=True)
