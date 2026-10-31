"""Independent O22F6 R1 D01 supplement: fill both P095 flat-capped rod elbows.
The released F5/F6 files are read-only inputs. Digital checks do not imply a
physical strength, fatigue, or process qualification.
"""
from pathlib import Path
import sys,json,copy,shutil,itertools,argparse,time
import numpy as np
import o22f6_holeclear as h
from o22f6_final import RESTORE
BASE=h.B/'O22F6_PLA_Final'
OLDWORK=h.B/'diagnostics/O22F6_final_20261015'
WORK=h.B/'diagnostics/P095_elbow_20261016'
OUT=h.B/'O22F6R1_P095_Elbows'
PID='P095'
BENDS=[[13.8,-11.5,-3],[11.5,13.8,-3]]
RADIUS=1.8
SUFFIX='PLA_R1_P095_elbows'
def configure():
 h.OUT=OUT;h.WORK=WORK;h.PROJECT_SUFFIX=SUFFIX
 h.PRINT_SETTINGS_ID='O22-F6 R1 P095 elbows / A1 mini PLA 0.4'
 h.ORIGINAL_PROFILE_IDS=RESTORE;h.SCREEN_LABEL='r1elbows';h.TARGET_PART_IDS=None

def plate():return copy.deepcopy(next(p for p in json.loads((h.SRC/'manifest.json').read_text(encoding='utf8'))['plates'] if p['id']=='D01'))
def npzsolid(path):
 n=np.load(path);return h.solid(n['v'],n['f'])
def sweep_convex(s,delta):
 v=h.vf(s)[0];return h.md.Manifold.hull_points(np.vstack([v,v+np.array(delta)]))

def stage():
 configure();assert not (OUT/'RELEASED.json').exists(),'Never overwrite released revision'
 p=plate();ids=sorted({i['id']for i in p['items']})
 for sub in ['parts','design','projects','verification']:(OUT/sub).mkdir(parents=True,exist_ok=True)
 for pid in ids:
  for sub,ext in [('parts','.npz'),('design','.json')]:shutil.copy2(BASE/sub/(pid+ext),OUT/sub/(pid+ext))
  for sub in ['guards','initial']:
   (WORK/sub).mkdir(parents=True,exist_ok=True);ext='.npz' if sub=='guards' else '.json';shutil.copy2(OLDWORK/sub/(pid+ext),WORK/sub/(pid+ext))
 shutil.copy2(OLDWORK/'profile_overrides.json',WORK/'profile_overrides.json')
 n=dict(np.load(BASE/'parts/P095.npz'));before=h.solid(n['v'],n['f']);fin=h.solid(n['fin_v'],n['fin_f']);teeth=h.solid(n['teeth_v'],n['teeth_f'])
 H=np.array(json.loads((WORK/'initial_localization.json').read_text())['local_to_print_matrix'])
 balls=[h.md.Manifold.sphere(RADIUS,96).translate(v).transform(H[:3]) for v in BENDS]
 after=before+h.union(balls);added=h.union(balls)-before
 # Preserve each fin's continuous downward exit while keeping a 0.35 mm
 # nominal gap around the new body, including any material above the bend.
 clearance=[h.md.Manifold.sphere(RADIUS+.35,96).translate(v).transform(H[:3]) for v in BENDS]
 exclusion=h.union([sweep_convex(s,[0,0,60])for s in clearance])
 newfin=fin-exclusion
 assert abs((newfin-fin).volume())<1e-6
 assert (newfin^after).volume()<1e-6
 assert len(h.material_components(after))==1
 assert len(h.material_components(after+newfin+teeth))==1
 assert all(c.bounding_box()[2]<1e-5 and c.slice(.05).area()>.005 for c in h.material_components(newfin))
 assert all((c^newfin).volume()>.001 and (c^after).volume()>.001 for c in h.material_components(teeth))
 # A subset of each original fin keeps its old-body and fin/fin exits.
 # Test continuous new-body obstruction explicitly, not discrete samples.
 swept_additions=h.union([sweep_convex(s,[0,0,60])for s in balls])
 assert (newfin^swept_additions).volume()<1e-6
 guard=npzsolid(WORK/'guards/P095.npz');assert (added^guard).volume()<1e-6
 n['v'],n['f']=h.vf(after);n['fin_v'],n['fin_f']=h.vf(newfin)
 n['r1_added_body_v'],n['r1_added_body_f']=h.vf(added)
 np.savez_compressed(OUT/'parts/P095.npz',**n)
 rows=[];srcrow=next(r for r in json.loads((h.SRC/'manifest.json').read_text())['rows'] if r['id']=='P095');gp=np.load(h.SRC/'verification/parts/P095/f5_fin_groups.npz');groups=[]
 for j,g in enumerate(srcrow['fin_bodies'],1):
  assert g['removal_vector']==[0.,0.,-1.]
  oldgroup=h.solid(gp[f'g{j}_v'],gp[f'g{j}_f']);newgroup=oldgroup^newfin;groups.append(newgroup)
  rows.append(dict(id=g['id'],removed_mm3=max(0.,float((oldgroup-newgroup).volume())),remaining_mm3=float(newgroup.volume()),continuous_downward_exit=True))
 grouped=h.union(groups);assert abs((newfin-grouped).volume())+abs((grouped-newfin).volume())<1e-5
 rep=dict(id=PID,status='pending_native_checks',source_npz_sha256=h.sha(BASE/'parts/P095.npz'),revised_npz_sha256=h.sha(OUT/'parts/P095.npz'),cause='Original two flat-ended cylindrical rods meet without a rounded elbow fill',elbow_count=2,rod_diameter_mm=3.6,round_joint_radius_mm=1.8,source_local_bend_centres_mm=BENDS,local_to_print_matrix=H.tolist(),added_body_mm3=float(added.volume()),removed_body_mm3=max(0.,float((before-after).volume())),added_body_in_fastener_envelopes_mm3=max(0.,float((added^guard).volume())),bounds_unchanged=bool(np.allclose(before.bounding_box(),after.bounding_box(),atol=1e-8)),body_components=1,fin_body_overlap_mm3=max(0.,float((newfin^after).volume())),support_fin_material_removed_mm3=float((fin-newfin).volume()),tooth_vertices_and_faces_identical=True,extra_tooth_body_contact_mm3=float((teeth^added).volume()),nominal_fin_clearance_at_elbows_mm=.35,minimum_global_fin_body_gap_capped_at_05_mm=float(newfin.min_gap(after,.5)),all_fins_bed_rooted=True,whole_print_components=1,continuous_downward_fin_exit=True,continuous_exit_proof='Each fin is a subset of the verified F5 fin. Exact continuous upward convex sweeps of both added elbow balls have zero intersection with the revised fins, so every fin has the same downward exit after all teeth are cut. Existing fin/fin sequence is preserved by subset.',fin_groups=rows,existing_hole_support_exception_retained=True,physical_print_tested=False,strength_or_fatigue_tested=False)
 h.put(WORK/'revision_geometry.json',rep)
 d=json.loads((BASE/'design/P095.json').read_text());d.update(body_change_reference='O22F6_PLA_Final',body_changed=True,part_body_modified_from_F4=True,body_f4_faces_identical=False,body_rigid_transform_only=False,f6_status='R1_pending_native_checks',native_pending=True,f6r1_elbow_revision=rep,body_change=dict(kind='rounded_rod_elbow_fill',radius_mm=1.8,added_mm3=rep['added_body_mm3'],removed_mm3=rep['removed_body_mm3']),physical_print_tested=False)
 h.put(OUT/'design/P095.json',d)
 unchanged=[]
 for pid in ids:
  if pid!=PID:assert h.sha(OUT/f'parts/{pid}.npz')==h.sha(BASE/f'parts/{pid}.npz')
  unchanged.append(dict(id=pid,changed=pid==PID,before_sha256=h.sha(BASE/f'parts/{pid}.npz'),after_sha256=h.sha(OUT/f'parts/{pid}.npz')))
 h.put(WORK/'scope.json',dict(plate='D01',instances=len(p['items']),types=len(ids),only_changed_part=PID,rows=unchanged))
 print('STAGED',json.dumps({k:v for k,v in rep.items()if k not in ['fin_groups','local_to_print_matrix','continuous_exit_proof']},ensure_ascii=False),flush=True)

def fit():
 configure();import build_revo22_assembly as a
 scratch=WORK/'assembly';scratch.mkdir(parents=True,exist_ok=True)
 for name in ['sensor_fit.json','end_axis_fit.json','sensor_cassettes.npz','end_axis_parts.npz']:
  shutil.copy2(h.B/'mechanical'/name,scratch/name)
 a.D=scratch;a.b.D=scratch;parts,meta,base,*_=a.model()
 d=json.loads((BASE/'design/P095.json').read_text());key=d['part'];A=np.array(meta[key]['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1
 bed=next(x['bed']for x in json.loads((h.B/'print_batch/manifest.json').read_text())['rows']if x['id']==PID)
 T=h.H(d['orientation']['matrix'],d['orientation']['source_translation_mm'])@h.H(bed['rotation'],bed['translation_mm'])@np.linalg.inv(A)
 n=np.load(OUT/'parts/P095.npz');added=h.solid(n['r1_added_body_v'],n['r1_added_body_f']);before=npzsolid(BASE/'parts/P095.npz');Ti=np.linalg.inv(T);bb=np.array(added.bounding_box());corners=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))));world_corners=corners@Ti[:3,:3].T+Ti[:3,3]
 f0,o0=a.owners(base);profile=a.profile
 poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',json.loads((h.B/'profiles/default_pose.json').read_text())['raw_deg'])]
 for rawkey,lim in profile['raw_limits_deg'].items():
  for label,val in zip(['min','max'],lim):
   pp=profile['neutral_raw_deg'].copy();pp[rawkey]=val;poses.append((rawkey+'/'+label,pp))
 local=next(j['raw_ids']for j in profile['joints']if j['id']=='thigh_l')
 for i,vals in enumerate(itertools.product(*[np.linspace(*profile['raw_limits_deg'][k],5) for k in local])):
  pp=profile['neutral_raw_deg'].copy();pp.update(dict(zip(local,vals)));poses.append(('thigh_grid_'+str(i),pp))
 rng=np.random.default_rng(20261016)
 for i in range(64):poses.append(('combined_'+str(i),{k:float(rng.uniform(*v))for k,v in profile['raw_limits_deg'].items()}))
 bounds={k:np.array(list(itertools.product(*zip(s.bounding_box()[:3],s.bounding_box()[3:]))))for k,s in parts.items()}
 inv_frames={k:np.linalg.inv(v)for k,v in f0.items()};inv_owners={k:np.linalg.inv(v)for k,v in o0.items()};cache={};rows=[];flags=[];mins=[];checks=0;preexisting=[]
 for ix,(name,raw) in enumerate(poses):
  f,o=a.owners(raw);transforms={}
  def tr(k):
   m=meta[k];token=('f',m['body']) if m['owner']=='rigid_frame' else('o',m['module'],m['owner'])
   if token not in transforms:transforms[token]=f[m['body']]@inv_frames[m['body']]if token[0]=='f' else o[(m['module'],m['owner'])]@inv_owners[(m['module'],m['owner'])]
   return transforms[token]
  mine=tr(key);im=np.linalg.inv(mine);wc=world_corners@mine[:3,:3].T+mine[:3,3];lo=wc.min(0);hi=wc.max(0);near=[]
  for k,p in parts.items():
   if k==key:continue
   other=tr(k);v=bounds[k]@other[:3,:3].T+other[:3,3];sep=np.maximum(np.maximum(v.min(0)-hi,lo-v.max(0)),0)
   if np.linalg.norm(sep)>.6:continue
   rel=im@other;token=(k,tuple(np.round(rel,8).flat))
   if token not in cache:
    moved=p.transform((T@rel)[:3,:]);intrusion=max(0.,float((added^moved).volume()));gap=float(added.min_gap(moved,.6));old_overlap=max(0.,float((before^moved).volume())) if intrusion>1e-6 or gap<.05 else 0.;cache[token]=dict(part=k,added_intersection_mm3=intrusion,gap_capped_at_06_mm=gap,old_body_intersection_mm3=old_overlap)
   rec=dict(cache[token],pose=name);near.append(rec);checks+=1
   if rec['added_intersection_mm3']>1e-6 or rec['gap_capped_at_06_mm']<.05:
    if rec['old_body_intersection_mm3']>.01:preexisting.append(rec)
    else:flags.append(rec)
   mins.append(rec)
  rows.append(dict(pose=name,nearby_checks=near))
  if ix%80==0:print('FIT_PROGRESS',ix+1,'/',len(poses),'unique',len(cache),'flags',len(flags),flush=True)
 invalid_poses={r['pose']for r in preexisting};excluded_flags=[r for r in flags if r['pose']in invalid_poses];flags=[r for r in flags if r['pose']not in invalid_poses];valid_mins=[r for r in mins if r['pose']not in invalid_poses]
 rep=dict(id=PID,source_revised_npz_sha256=h.sha(OUT/'parts/P095.npz'),pose_count=len(poses),local_joint_grid='5 equally spaced values for each of the four thigh_l axes, 625 combinations',random_combined_poses=64,single_axis_endpoints=True,geometry_new_interferences=flags,preexisting_collision_pose_pairs=preexisting,excluded_poses=sorted(invalid_poses),excluded_pose_count=len(invalid_poses),examined_poses_without_detected_preexisting_collision=len(poses)-len(invalid_poses),new_contacts_in_already_infeasible_poses=excluded_flags,passed=not flags,unique_relative_neighbor_checks=len(cache),total_near_neighbor_checks=checks,minimum_checked_clearance_mm=min([r['gap_capped_at_06_mm']for r in valid_mins],default=.6),closest=sorted(valid_mins,key=lambda r:r['gap_capped_at_06_mm'])[:20],pose_records=rows,scope='Added material only checked against every modeled other assembly part, including modeled hardware and electronics. 0.05 mm clearance gate. Sampled poses are not a proof of continuous combined motion. Any pose with a demonstrated existing body penetration above 0.01 mm3 is infeasible and is excluded as a whole, with all evidence retained. No claim of collision freedom for excluded poses or continuous combined motion. The 0.05 mm clearance gate applies to all remaining sampled poses.',physical_strength_or_fatigue_tested=False)
 h.put(WORK/'fit_and_pose.json',rep);print('FIT_DONE',rep['passed'],rep['pose_count'],rep['minimum_checked_clearance_mm'],len(flags),flush=True)
 assert rep['passed']

def build():configure();return h.build_plate(plate())
def screen():configure();return h.screen_plate(plate())
def holes():
 configure();import o22f6_deposited_holes as dh
 dh.OUT=OUT;dh.WORK=WORK;dh.PROJECT_SUFFIX=SUFFIX;return dh.check(plate())
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['stage','fit','build','screen','holes']);args=ap.parse_args();globals()[args.action]()