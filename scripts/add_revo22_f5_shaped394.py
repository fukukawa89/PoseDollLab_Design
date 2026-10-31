"""Tiny permanent gussets inside the old convex envelope, outside all functional voids."""
import sys,json,shutil,traceback,concurrent.futures,collections,numpy as np,trimesh,shapely
from shapely.ops import nearest_points
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,union,box,md
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from o22_f3_gcode import extract_paths
from verify_revo22_f5_contacts298 import envelope
import repair_revo22_f4_guarded_chamfer as ctx
from optimize_revo22_f5_276 import candidates
from audit_revo22_f5_native271 import run as audit

def create(pid,src,label):
 a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if(b/'parts'/f'{pid}.npz').exists():return True
 n=dict(np.load(a/'parts'/f'{pid}.npz'));d=json.loads((a/'design'/f'{pid}.json').read_text());r=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);s=solid(n['v'],n['f']);hull=md.Manifold.hull_points(n['v']);gn=np.load(a/'verification/guards.npz');guard=solid(gn['v'],gn['f']);mesh=trimesh.Trimesh(n['v'],n['f'],process=False);parts,key,T=ctx.context(d,pid);others=[q.transform(T[:3,:])for k,q in parts.items()if k!=key];lh=d.get('required_layer_height_mm',.2);_,raw=extract_paths(next((a/'projects').glob('*.3mf')),arc_tolerance_mm=.025,max_arc_segment_mm=1.);paths=np.array(raw).reshape(-1,9);paths=paths[paths[:,7]==0];zs=np.unique(paths[:,5]);cache={};records=[];ref=solid(n.get('f5_pre_relief_v',n['v']),n.get('f5_pre_relief_f',n['f']))
 reasons=collections.Counter()
 for q in r['external_islands']+r['critical_external_runs']:
  bb=q['bounds_mm'];p=(np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2,q['z_mm']])-t)@M;prevz=float(zs[zs<q['z_mm']-.01][-1]);k=round(prevz,3)
  if k not in cache:
   pp=paths[abs(paths[:,5]-prevz)<.002];aa=(pp[:,:3]-t)@M;bb0=(pp[:,3:6]-t)@M;lines=shapely.linestrings(np.stack([aa[:,:2],bb0[:,:2]],1));beads=shapely.union_all(shapely.buffer(lines,pp[:,8]/2,quad_segs=4));cache[k]=beads.intersection(polygon(s.slice(prevz-lh/2)))
  mat=cache[k]
  if mat.is_empty:continue
  anchor_list=[]
  for rr in [0.,1.,2.,3.,4.]:
   for angle in (np.arange(0,2*np.pi,np.pi/6) if rr else [0]):
    pp=p[:2]+rr*np.array([np.cos(angle),np.sin(angle)]);pt=nearest_points(mat,shapely.Point(pp))[0];an=np.array([pt.x,pt.y])
    if not any(np.linalg.norm(an-aa)<.3 for aa in anchor_list):anchor_list.append(an)
  anchor_list.sort(key=lambda an:np.linalg.norm(an-p[:2]));success=False
  for anchor in anchor_list:
   dire=p[:2]-anchor;dist=np.linalg.norm(dire)
   if not .1<dist<4:reasons['anchor_distance']+=1;continue
   dire/=dist;close,di,faces=trimesh.proximity.closest_point(mesh,[p-[0,0,lh/2]]);h=close[0];tip=h-mesh.face_normals[faces[0]]*.2;tip[2]=max(tip[2],p[2]+.18);success=False
   for depth in [.6,1.,1.6,2.2,3.0,4.0,5.2]:
    for back in [.25,.6,1.0]:
     root=np.r_[anchor-dire*back,max(.15,prevz-depth)];root_box=box(root-[.4,.4,.25],root+[.4,.4,.25]);tip_box=box(tip-[.4,.4,.15],tip+[.4,.4,.15])
     if(root_box^s).volume()<.03 or(tip_box^s).volume()<.002:reasons['root_tip_overlap']+=1;continue
     gusset=md.Manifold.hull_points(np.r_[vf(root_box)[0],vf(tip_box)[0]])^box([-1000,-1000,0],[1000,1000,1000]);add=gusset-s;vol=float(add.volume())
     if not 1e-5<vol<3:reasons['volume']+=1;continue
     gusset=gusset-guard-solid(n['fin_v'],n['fin_f']);add=gusset-s;vol=float(add.volume())
     if not 1e-5<vol<3:continue
     if(gusset^root_box^s).volume()<.01 or(gusset^tip_box^s).volume()<.002:continue
     if(add-envelope(ref,add,margin=.6)).volume()>1e-6:reasons['surface_bound']+=1;continue
     ab=np.array(add.bounding_box());blocked=False
     for other in others:
      ob=np.array(other.bounding_box());sep=np.maximum(np.maximum(ob[:3]-ab[3:],ab[:3]-ob[3:]),0)
      if np.linalg.norm(sep)>.25:continue
      if envelope(other.transform(np.linalg.inv(T)[:3,:]),add.transform(np.linalg.inv(T)[:3,:]),margin=.052).volume()>1e-6:blocked=True;break
     if blocked:reasons['actual_neighbor']+=1;continue
     proposal=s+gusset
     if len(material_components(proposal))!=len(material_components(s)):reasons['split']+=1;continue
     if(proposal-ref).volume()>=min(10.,ref.volume()*.002):continue
     s=proposal;records.append(dict(kind='permanent_inner_gusset',local_bounds_mm=list(gusset.bounding_box()),added_volume_mm3=vol,root=root.tolist(),tip=tip.tolist(),native_issue=q,within_previous_convex_envelope=False,local_expansion_bound_per_axis_mm=.6,actual_neighbor_clearance_mm=.06));success=True;break
    if success:break
   if success:break
  print('SHAPED394_REASONS',pid,dict(reasons),flush=True)
  print('SHAPED394_TARGET',pid,np.round(p,3).tolist(),success,flush=True)
 if not records:return False
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n.setdefault('f5_pre_relief_v',n['v'].copy());n.setdefault('f5_pre_relief_f',n['f'].copy());n['v'],n['f']=vf(s);np.savez_compressed(b/'parts'/f'{pid}.npz',**n);shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz');
 if(a/'verification/strict_magnet_guards.npz').exists():shutil.copy2(a/'verification/strict_magnet_guards.npz',b/'verification/strict_magnet_guards.npz')
 d.update(trial=label,part_body_modified_from_F4=True,body_rigid_transform_only=False,body_f4_faces_identical=False,f5_additions=d.get('f5_additions',[])+records,f5_reliefs=d.get('f5_reliefs',[]),f5_added_volume_mm3=float((s-ref).volume()),f5_local_expansion_bound_mm=.6,fit_and_pose_pending=True);put(b/'design'/f'{pid}.json',d);return True

def run(pid):
 from optimize_revo22_f5_276 import pick
 if pick(pid):return(pid,'already_passed',True)
 cc=[q for q in candidates(pid)if list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))and float(q[4].get('required_process_overrides',{}).get('min_feature_size','25%').strip('%'))<=100];src={'P130':'ends366_0','X038':'cut374_0','X046':'cut374_0','X054':'ends366_0'}[pid]
 for i in range(4):
  label=f'shaped394_{i}'
  if not create(pid,src,label):break
  q=audit(pid,label)
  if q['native_review_resolved']:print('SHAPED394_NATIVE_PASS_REQUIRES_FIT',pid,label,flush=True);return(pid,label,True)
  src=label
 return(pid,src,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in sys.argv[1:]}
  for f in concurrent.futures.as_completed(fs):
   try:print('SHAPED394_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('SHAPED394_ERROR',fs[f],flush=True)
