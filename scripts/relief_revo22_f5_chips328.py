"""Bounded underside relief only after native-directed fin routes have been tried."""
import sys,json,shutil,numpy as np
from shapely.geometry import Point
from shapely.ops import nearest_points
from search_revo22_f5_orientation268 import O,OLD,put
from build_revo22_fins import solid,vf,box,union,md,extrude_xz
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
import repair_revo22_f4_guarded_chamfer as ctx
import shapely
from o22_f3_gcode import extract_paths
from verify_revo22_f5_contacts298 import envelope

def run(pid,src,label):
 a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if(b/'parts'/f'{pid}.npz').exists():return json.loads((b/'design'/f'{pid}.json').read_text())
 n=dict(np.load(a/'parts'/f'{pid}.npz'));d=json.loads((a/'design'/f'{pid}.json').read_text());rep=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);old=solid(n['v'],n['f']);new=old;parts,key,T=ctx.context(d,pid);offsets=np.array([[x,y,z]for x in[-.1,0.,.1]for y in[-.1,0.,.1]for z in[-.1,0.,.1]]);rows=[];protected=[]
 oldbb=np.array(old.bounding_box())
 for k,p in parts.items():
  if k==key:continue
  v=vf(p)[0];v=v@T[:3,:3].T+T[:3,3];sep=np.maximum(np.maximum(v.min(0)-oldbb[3:],oldbb[:3]-v.max(0)),0)
  if np.linalg.norm(sep)>.5:continue
  protected.append(p.transform(T[:3,:]))
 guard=union(protected)
 _,raw=extract_paths(next((a/'projects').glob('*.3mf')),arc_tolerance_mm=.025,max_arc_segment_mm=1.);paths=np.array(raw).reshape(-1,9);paths=paths[paths[:,7]==0];zs=np.unique(paths[:,5]);native_cache={}
 for q in list(rep['external_islands'])+list(rep['critical_external_runs']):
  bb=q['bounds_mm'];pts=(np.array([[x,y,q['z_mm']-.1]for x in[bb[0],bb[2]]for y in[bb[1],bb[3]]])-t)@M;lo=pts.min(0);hi=pts.max(0);p=(lo+hi)/2;zlo=p[2]-.5;zhi=p[2]+2.5;prevz=zs[zs<q['z_mm']-.01][-1];keyz=round(float(prevz),3)
  if keyz not in native_cache:
   pp=paths[abs(paths[:,5]-prevz)<.002];aa=(pp[:,:3]-t)@M;bb0=(pp[:,3:6]-t)@M;lines=shapely.linestrings(np.stack([aa[:,:2],bb0[:,:2]],1));native_cache[keyz]=shapely.union_all(shapely.buffer(lines,pp[:,8]/2,quad_segs=8))
  prev=native_cache[keyz]
  if prev.is_empty:continue
  q0=nearest_points(prev,Point(p[:2]))[0];q0=np.array([q0.x,q0.y]);dire=p[:2]-q0;distance=np.linalg.norm(dire)
  print('DBG_DISTANCE',pid,distance,p.tolist(),q0.tolist(),flush=True)
  if distance<.02 or distance>2.5:continue
  dire/=distance;q0-=dire*.38;tangent=np.array([-dire[1],dire[0]]);rot=np.eye(3);rot[:2,0]=dire;rot[:2,1]=tangent;slope=.45;cs=md.CrossSection([[[-8,zlo-1],[-slope,zlo-1],[slope*(zhi+1-zlo),zhi+1],[-8,zhi+1]]]);allow=extrude_xz(cs,20,0).transform(np.c_[rot,[*q0,0.]]);roi=box([lo[0]-.5,lo[1]-.5,zlo],[hi[0]+.5,hi[1]+.5,zhi]);cut=(roi-allow)-guard;delta=new^cut;print('DBG_CUT',pid,float((new^(roi-allow)).volume()),float(delta.volume()),flush=True)
  local_guards=[];rb=np.array(roi.bounding_box())
  for sp in protected:
   pb=np.array(sp.bounding_box());sep=np.maximum(np.maximum(pb[:3]-rb[3:],rb[:3]-pb[3:]),0)
   if np.linalg.norm(sep)>.24:continue
   local_guards.append(envelope(sp,roi,margin=.12))
  cut-=union(local_guards);delta=new^cut;print('DBG_GUARD',pid,float(delta.volume()),flush=True)
  if not 1e-7<delta.volume()<min(10.,old.volume()*.003):continue
  proposal=new-cut
  pieces=sorted(material_components(proposal),key=lambda q:-q.volume());expected_count=len(material_components(old))
  if len(pieces)>expected_count:
   chips=union(pieces[expected_count:]);protected_here=union(local_guards)+guard
   if chips.volume()>1. or (chips-roi).volume()>1e-6 or (chips^protected_here).volume()>1e-6:continue
   proposal=union(pieces[:expected_count]);delta=new-proposal
  if len(material_components(proposal))!=expected_count:continue
  reference=solid(n.get('f5_pre_relief_v',n['v']),n.get('f5_pre_relief_f',n['f']))
  if float((reference-proposal).volume())>=min(40.,reference.volume()*.006):continue
  new=proposal;rows.append(dict(native_issue=q,local_bounds_mm=list(roi.bounding_box()),removed_volume_mm3=float(delta.volume()),kind='extrusion_aware_underside_chamfer',printable_slope_xy_per_z=slope,anchor_inset_mm=.38,horizontal_distance_to_parent_mm=distance))
 delta=old-new
 if not rows:print('F5_RELIEF_NONE',pid,src,flush=True);return None
 assert float(delta.volume())<min(40.,old.volume()*.006)
 for sub in['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n.setdefault('f5_pre_relief_v',n['v'].copy());n.setdefault('f5_pre_relief_f',n['f'].copy());n['v'],n['f']=vf(new);fin=solid(n['fin_v'],n['fin_f']);ts=solid(n['teeth_v'],n['teeth_f']);ts=union([c for c in material_components(ts)if(c^new).volume()>.005 and(c^fin).volume()>.005]);fin=union([c for c in material_components(fin)if(c^ts).volume()>.005]);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{pid}.npz',**n);shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz')
 total=solid(n['f5_pre_relief_v'],n['f5_pre_relief_f'])-new;d.update(trial=label,part_body_modified_from_F4=True,body_f4_faces_identical=False,body_rigid_transform_only=False,f5_reliefs=d.get('f5_reliefs',[])+rows,f5_removed_volume_mm3=float(total.volume()),support_count=len(material_components(fin)),support_volume_mm3=float((fin+ts).volume()),fit_and_pose_pending=True,f5_edit_budget_mm3=40.,f5_edit_budget_fraction=.006);put(b/'design'/f'{pid}.json',d);put(b/'verification/relief_geometry.json',dict(removed_volume_mm3=float(total.volume()),added_volume_mm3=float((new-solid(n['f5_pre_relief_v'],n['f5_pre_relief_f'])).volume()),actual_assembly_shape_minimum_clearance_mm=.08,body_components_preserved=True,contact_and_pose_verification_pending=True,rows=rows));print('F5_RELIEF',pid,label,len(rows),float(total.volume()),flush=True);return d
if __name__=='__main__':run(*sys.argv[1:4])
