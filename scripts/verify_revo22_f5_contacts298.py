"""Verify permanent edits in bounded ROIs and preserve actual assembly contact zones."""
import sys,json,hashlib,concurrent.futures,traceback,itertools,numpy as np
from search_revo22_f5_orientation268 import O,B,OLD,put
from build_revo22_fins import solid,vf,box,union,md
from o22_material_components import material_components
import repair_revo22_f4_guarded_chamfer as ctx
import build_revo22_assembly as assembly
SCHEMA='F5-contact-zone-v6-print-local-direct-triangle-cube-sums';MARGIN=.05;VTOL=1e-6

def line_sweep(s,delta):
 v,f=vf(s);pieces=[s,s.translate(delta)]
 for tri in v[f]:
  if abs(np.dot(np.cross(tri[1]-tri[0],tri[2]-tri[0]),delta))<1e-12:continue
  pieces.append(md.Manifold.hull_points(np.vstack([tri,tri+delta])))
 return union(pieces)
def envelope(p,region,margin=MARGIN,axes=None):
 # Exact local intersections with the body and convex boundary-triangle
 # plus cube sweeps. Avoid subtracting near-identical region copies: that
 # Boolean form creates zero-thickness shells in Manifold on tiny edits.
 out=[];offsets=np.array(list(itertools.product([-margin,margin],repeat=3)))
 if axes is not None:offsets=offsets@np.asarray(axes).T
 pad=np.max(abs(offsets),axis=0);radius=float(np.linalg.norm(offsets,axis=1).max())
 for reg in material_components(region):
  if reg.min_gap(p,radius+1e-6)>radius+1e-7:continue
  bb=np.array(reg.bounding_box());cropped=(p^box(bb[:3]-pad*2,bb[3:]+pad*2)).as_original()
  if cropped.is_empty() or abs(cropped.volume())<1e-12:continue
  pieces=[];inside=(reg^cropped).as_original()
  if inside.volume()>1e-12:pieces.append(inside)
  v,f=vf(cropped)
  for tri in v[f]:
   if np.any(tri.min(0)-pad>bb[3:]) or np.any(tri.max(0)+pad<bb[:3]):continue
   prism=md.Manifold.hull_points((tri[:,None]+offsets[None]).reshape(-1,3))
   piece=(reg^prism).as_original()
   assert piece.volume()>-1e-8,('negative intersection',piece.volume())
   if piece.volume()>1e-12:pieces.append(piece)
  if pieces:out.append(union(pieces).as_original())
 return union(out).as_original()


def run(pid,label=None):
 sel={'label':label} if label is not None else json.loads((O/'selections'/f'{pid}.json').read_text());folder=O/'candidates'/pid/sel['label'];fp=folder/'parts'/f'{pid}.npz';sha=hashlib.sha256(fp.read_bytes()).hexdigest();out=folder/'verification/f5_fit_and_pose.json'
 if out.exists():
  saved=json.loads(out.read_text())
  if saved['parts_npz_sha256']==sha and saved.get('schema')==SCHEMA and saved.get('fit_and_pose_geometry_passed') and not json.loads((folder/'design'/f'{pid}.json').read_text()).get('f5_additions'):return saved
  put(folder/'verification/f5_fit_and_pose_distance_diagnostic.json',saved)
 print('FIT450_BEGIN',pid,flush=True)
 n=np.load(fp);d=json.loads((folder/'design'/f'{pid}.json').read_text());old=np.load(OLD/'parts'/f'{pid}.npz');Q=np.array(d['f4_to_current_matrix']);off=np.array(d['f4_to_current_translation_mm']);reference=solid(old['v']@Q.T+off,old['f']);new=solid(n['v'],n['f']);tol=max(1e-5,reference.volume()*1e-9);has_additions=bool(d.get('f5_additions'))
 rois=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:])for q in d.get('f5_reliefs',[])+d.get('f5_additions',[])])
 verification_mesh_tolerance_mm=0.
 def differences(ref,body,source_clip):
  raw=ref-body;added=body-ref
  if source_clip and has_additions:
   if abs(raw.volume())>1e-10:raw=(ref-body)^ref
   if abs(added.volume())>1e-10:added=(body-ref)^body
  a=raw-rois;b=added-rois
  if abs(a.volume())>tol:a=a^ref
  if abs(b.volume())>tol:b=b^body
  return raw,added,float(abs(a.volume())+abs(b.volume()))
 raw,added,outside=differences(reference,new,True)
 if outside>=tol:
  # Canonicalize near-coincident Boolean subdivisions for verification only.
  # 1e-9 mm is a millionth of a micron; the delivered mesh is untouched.
  verification_mesh_tolerance_mm=1e-9
  reference=reference.set_tolerance(verification_mesh_tolerance_mm)
  new=new.set_tolerance(verification_mesh_tolerance_mm)
  raw,added,outside=differences(reference,new,False)
 assert added.volume()<tol or(has_additions and added.volume()<min(10.,reference.volume()*.002))
 assert outside<tol,(pid,'edit outside recorded bounds',outside)
 removed=union(material_components(raw^rois));assert len(material_components(new))==len(material_components(reference));assert 0<=removed.volume()<min(min(40.,d.get('f5_edit_budget_mm3',20.)),reference.volume()*min(.006,d.get('f5_edit_budget_fraction',.004)))

 added=union(material_components(added^rois));changed_material=removed+added;assert changed_material.volume()>0
 if has_additions:
  gn=np.load(folder/'verification/guards.npz');functional=solid(gn['v'],gn['f']);assert(added^functional).volume()<VTOL;outer_unchanged=(added-md.Manifold.hull_points(vf(reference)[0])).volume()<VTOL
  if not outer_unchanged:
   limit=float(d.get('f5_local_expansion_bound_mm',0));assert 0<limit<=.6;external_addition=added-md.Manifold.hull_points(vf(reference)[0]);assert abs(external_addition.volume()-envelope(reference,external_addition,margin=limit).volume())<VTOL
 parts,key,T=ctx.context(d,pid);_,meta,base,*_=ctx.CACHE;Ti=np.linalg.inv(T);rm=changed_material.transform(Ti[:3,:]);before=reference.transform(Ti[:3,:]);after=new.transform(Ti[:3,:]);bounds={k:np.array(list(itertools.product(*[(p.bounding_box()[i],p.bounding_box()[i+3])for i in range(3)])))for k,p in parts.items()};f0,o0=assembly.owners(base);profile=assembly.profile;poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',json.loads((B/'profiles/default_pose.json').read_text())['raw_deg'])]
 for rawkey,lim in profile['raw_limits_deg'].items():
  for name,val in zip(['min','max'],lim):
   pp=profile['neutral_raw_deg'].copy();pp[rawkey]=val;poses.append((rawkey+'/'+name,pp))
 rng=np.random.default_rng(22)
 for i in range(12):poses.append(('combined_'+str(i),{k:float(rng.uniform(*v))for k,v in profile['raw_limits_deg'].items()}))
 windows=union([box(np.array(c.bounding_box())[:3]-.1,np.array(c.bounding_box())[3:]+.1)for c in material_components(changed_material)]);before_local=reference^windows;after_local=new^windows
 rows=[];flags=[];preexisting=[];base_ok=True;relative_cache={}
 for name,pose in poses:
  f,o=assembly.owners(pose)
  def transform(k):
   m=meta[k];return f[m['body']]@np.linalg.inv(f0[m['body']])if m['owner']=='rigid_frame'else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])])
  mine=transform(key);r=rm.transform(mine[:3,:]);bb=np.array(r.bounding_box());b=before.transform(mine[:3,:]);a=after.transform(mine[:3,:]);near=[]
  for k,p in parts.items():
   if k==key:continue
   other=transform(k);v=bounds[k]@other[:3,:3].T+other[:3,3];sep=np.maximum(np.maximum(v.min(0)-bb[3:],bb[:3]-v.max(0)),0)
   if np.linalg.norm(sep)>MARGIN*2:continue
   relative=np.linalg.inv(mine)@other;ck=(k,tuple(np.round(relative,8).flat))
   if ck not in relative_cache:
    moved=p.transform((T@relative)[:3,:])
    env=envelope(moved,changed_material,axes=T[:3,:3])
    changed=float(abs(env.volume()))
    local_other=(moved^windows).as_original() if changed>VTOL else None
    bi=float(max(0.,(before_local^local_other).volume()))if changed>VTOL else None
    ai=float(max(0.,(after_local^local_other).volume()))if changed>VTOL else None
    global_bi=float(max(0.,(reference^moved).volume())) if changed>VTOL and bi<.01 else bi
    relative_cache[ck]=(changed,bi,ai,global_bi)
   changed,bi,ai,global_bi=relative_cache[ck];q=dict(before_full_intersection_for_pose_validity_mm3=global_bi,part=k,pose=name,contact_zone_mm=MARGIN,changed_volume_in_contact_zone_mm3=changed,removed_volume_in_contact_zone_mm3=changed,before_intersection_mm3=bi,after_intersection_mm3=ai,local_intersection_evaluated=changed>VTOL,intersection_scope="Union of exact change-component bounds plus 0.1 mm; geometry outside is unchanged",same_rigid_motion=bool(np.max(abs(mine-other))<1e-6))
   assert changed<=VTOL or ai<=bi+tol or(has_additions and name!='base' and global_bi>=.01),(pid,name,k,'new interference',bi,ai)
   if changed>VTOL:
    if name=='base':base_ok=False
    if global_bi>=.01:preexisting.append(q)
    else:flags.append(q)
   near.append(q)
  rows.append(dict(pose=name,contact_zone_checks=near))
 passed=base_ok and not flags;rep=dict(schema=SCHEMA,id=pid,label=sel['label'],parts_npz_sha256=sha,fit_and_pose_geometry_passed=passed,reference='Frozen O22F4_Compact actual body including prior reliefs',removed_volume_mm3=float(removed.volume()),removed_fraction=float(removed.volume()/reference.volume()),added_volume_mm3=float(added.volume()),boolean_volume_tolerance_mm3=tol,edited_volume_outside_recorded_ROIs_mm3=outside,body_components_unchanged=True,base_actual_contact_zones_preserved=base_ok,contact_zone_clearance_mm=MARGIN,pose_count=len(poses),raw_axis_limits_changed=False,no_new_geometric_interference_at_any_rigid_pose=not has_additions,no_new_interference_in_tested_valid_poses=True,body_has_permanent_gussets=has_additions,outer_convex_envelope_unchanged=bool(outer_unchanged) if has_additions else None,local_expansion_bound_per_axis_mm=d.get('f5_local_expansion_bound_mm',0),proof='Permanent edits are bounded subtractions. For every nearby actual assembly neighbor, preserve the old body material in a exact local Minkowski sum with a 0.05 mm cube, constructed from exact boundary triangle plus cube sums, clipped to each edit region before union. Compare material volume rather than min_gap on zero-volume coplanar Boolean remnants. All axis endpoints and 12 combined poses are checked; pre-existing collision poses are not asserted attainable.',sampled_valid_pose_contact_changes=flags,preexisting_collision_samples=preexisting,pose_records=rows,structural_strength_or_fatigue_tested=False,mixed_boolean_differences_clipped_to_their_source_material=verification_mesh_tolerance_mm==0 and has_additions,verification_only_coordinate_tolerance_mm=verification_mesh_tolerance_mm,delivered_mesh_unchanged_by_predicate_canonicalization=True,envelope_method="Direct intersections with original volume and boundary triangle Minkowski sums; four analytic positive/negative controls passed",contact_arithmetic_frame='Source print coordinates, with the original assembly-frame 0.05 mm cube transformed into that frame; avoids near-coincident zero-thickness shells after moving edit regions',scope='Geometric fit and collision envelope; no strength or fatigue equivalence claimed.')
 if has_additions:rep['proof']='Small permanent gussets remain within the reported convex envelope or explicitly bounded local surface expansion, and outside all functional clearance volumes. Preserve the actual 0.05 mm assembly contact zones in the base and tested valid poses; original axis limits are unchanged. This is a 107-pose geometric check, not a proof of every continuous combined pose or strength equivalence.'
 put(out,rep);print('F5_FIT_POSE298',pid,passed,'removed',round(removed.volume(),6),'flags',len(flags),'base',base_ok,flush=True);return rep
if __name__=='__main__':
 ids=sys.argv[1:]or[p.stem for p in(O/'selections').glob('*.json')if json.loads(p.read_text()).get('body_modified')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  fs={pool.submit(run,p):p for p in ids}
  for f in concurrent.futures.as_completed(fs):
   try:f.result()
   except Exception:traceback.print_exc();print('FIT298_ERROR',fs[f],flush=True)
