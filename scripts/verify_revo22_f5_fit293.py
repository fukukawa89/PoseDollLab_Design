"""Check each F5 subtraction against the frozen F4 body and actual O22 assembly."""
import sys,json,hashlib,time,concurrent.futures,traceback,numpy as np
from search_revo22_f5_orientation268 import O,B,OLD,put
from build_revo22_fins import solid,vf
from o22_material_components import material_components
import repair_revo22_f4_guarded_chamfer as ctx
import build_revo22_assembly as assembly

def run(pid):
 sel=json.loads((O/'selections'/f'{pid}.json').read_text());folder=O/'candidates'/pid/sel['label'];fp=folder/'parts'/f'{pid}.npz';sha=hashlib.sha256(fp.read_bytes()).hexdigest();out=folder/'verification/f5_fit_and_pose.json'
 if out.exists()and json.loads(out.read_text())['parts_npz_sha256']==sha:return json.loads(out.read_text())
 n=np.load(fp);d=json.loads((folder/'design'/f'{pid}.json').read_text());old=np.load(OLD/'parts'/f'{pid}.npz');Q=np.array(d['f4_to_current_matrix']);off=np.array(d['f4_to_current_translation_mm']);reference=solid(old['v'],old['f']).transform(np.c_[Q,off]);new=solid(n['v'],n['f']);removed=reference-new;added=new-reference;assert added.volume()<1e-6;assert len(material_components(new))==len(material_components(reference));assert 0<removed.volume()<min(20.,reference.volume()*.004),(pid,removed.volume(),reference.volume())
 parts,key,T=ctx.context(d,pid);_,meta,base,*_=ctx.CACHE;Ti=np.linalg.inv(T);rm=removed.transform(Ti[:3,:]);before=reference.transform(Ti[:3,:]);after=new.transform(Ti[:3,:]);bounds={k:np.array([[x,y,z]for x in[p.bounding_box()[0],p.bounding_box()[3]]for y in[p.bounding_box()[1],p.bounding_box()[4]]for z in[p.bounding_box()[2],p.bounding_box()[5]]])for k,p in parts.items()};rb=np.array(rm.bounding_box());basecontacts=[]
 for k,p in parts.items():
  if k==key:continue
  vv=bounds[k];sep=np.maximum(np.maximum(vv.min(0)-rb[3:],rb[:3]-vv.max(0)),0)
  if np.linalg.norm(sep)>.15:continue
  gap=float(rm.min_gap(p,.15));inter=float((rm^p).volume());basecontacts.append(dict(part=k,gap_mm=gap,intersection_mm3=inter))
 base_ok=all(q['gap_mm']>=.08-1e-6 and q['intersection_mm3']<1e-6 for q in basecontacts)
 f0,o0=assembly.owners(base);profile=assembly.profile;poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',json.loads((B/'profiles/default_pose.json').read_text())['raw_deg'])]
 for raw,lim in profile['raw_limits_deg'].items():
  for name,val in zip(['min','max'],lim):
   pp=profile['neutral_raw_deg'].copy();pp[raw]=val;poses.append((raw+'/'+name,pp))
 rng=np.random.default_rng(22)
 for i in range(12):poses.append(('combined_'+str(i),{k:float(rng.uniform(*v))for k,v in profile['raw_limits_deg'].items()}))
 rows=[];flags=[];preexisting=[]
 for name,pose in poses:
  f,o=assembly.owners(pose)
  def transform(k):
   m=meta[k];return f[m['body']]@np.linalg.inv(f0[m['body']])if m['owner']=='rigid_frame'else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])])
  mine=transform(key);r=rm.transform(mine[:3,:]);bb=np.array(r.bounding_box());near=[]
  for k,p in parts.items():
   if k==key:continue
   other=transform(k);v=bounds[k]@other[:3,:3].T+other[:3,3];sep=np.maximum(np.maximum(v.min(0)-bb[3:],bb[:3]-v.max(0)),0)
   if np.linalg.norm(sep)>.08:continue
   moved=p.transform(other[:3,:]);gap=float(r.min_gap(moved,.08))
   if gap>=.08-1e-6:continue
   b=before.transform(mine[:3,:]);a=after.transform(mine[:3,:]);bi=float((b^moved).volume());ai=float((a^moved).volume());oldgap=float(b.min_gap(moved,.08));newgap=float(a.min_gap(moved,.08));q=dict(part=k,removed_gap_mm=gap,old_body_gap_mm=oldgap,new_body_gap_mm=newgap,before_intersection_mm3=bi,after_intersection_mm3=ai,same_rigid_motion=bool(np.max(abs(mine-other))<1e-6),pose=name)
   # Existing collision states are retained as diagnostics, never certified as reachable poses.
   if bi>=.01:preexisting.append(q)
   elif oldgap<.001 and gap<.001:flags.append(q)
   near.append(q)
  rows.append(dict(pose=name,near_removed_material=near))
 passed=base_ok and not flags;rep=dict(id=pid,label=sel['label'],parts_npz_sha256=sha,fit_and_pose_geometry_passed=passed,reference='Frozen O22F4_Compact actual body including prior reliefs',removed_volume_mm3=float(removed.volume()),removed_fraction=float(removed.volume()/reference.volume()),added_volume_mm3=float(added.volume()),body_components_unchanged=True,base_actual_neighbor_clearance_at_least_008mm=base_ok,base_neighbors=basecontacts,pose_count=len(poses),raw_axis_limits_changed=False,no_new_geometric_interference_at_any_rigid_pose=True,proof='The F5 body is strictly a subset of the frozen F4 body in the same rigid frame. This cannot add collisions. Base contacts retain at least 0.08 mm from the removed material; exact contacts in initially nonintersecting sampled poses are independently checked.',sampled_valid_pose_contact_changes=flags,preexisting_collision_samples=preexisting,pose_records=rows,structural_strength_or_fatigue_tested=False,scope='Geometric fit and motion checks, not a strength or fatigue equivalence proof. Combined samples with pre-existing collisions are diagnostic and are not asserted to be attainable.')
 put(out,rep);print('F5_FIT_POSE',pid,passed,'removed',round(float(removed.volume()),6),'poses',len(poses),'contact_flags',len(flags),flush=True);return rep
if __name__=='__main__':
 ids=sys.argv[1:]or[p.stem for p in(O/'selections').glob('*.json')if json.loads(p.read_text()).get('body_modified')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  fs={pool.submit(run,pid):pid for pid in ids}
  for f in concurrent.futures.as_completed(fs):
   try:f.result()
   except Exception:traceback.print_exc();print('FIT_ERROR',fs[f],flush=True)
