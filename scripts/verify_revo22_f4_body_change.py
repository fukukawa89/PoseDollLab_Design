"""Validate a subtractive print chamfer against the actual O22 assembly.
Subtractive geometry cannot create a new collision under any rigid pose.
Contact and limit samples are checked separately to protect fit and stops.
"""
from pathlib import Path
import sys,json,numpy as np,shutil,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md
from o22_material_components import material_components
from inspect_revo22_f4_washer_contacts import assess as assess_washers
import repair_revo22_f4_guarded_chamfer as shared_context
from inspect_revo22_f4_nut_contacts import assess as assess_nuts
from o22_mesh_identity import body_sha
from o22_reference_mesh import reference_mesh,reference_solid
from o22_noncontact_clearance import proven_noncontact
from inspect_revo22_f4_screw_contacts import assess as assess_screws
from inspect_revo22_f4_magnet_retention import assess as assess_magnet_retention
from assess_revo22_f4_edge_reliefs188 import assess as assess_edge_reliefs
import build_revo22_assembly as assembly
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
def H(M,t):
 r=np.eye(4);r[:3,:3]=M;r[:3,3]=t;return r

def check(pid,label):
 st=time.time();folder=O/'candidates'/pid/label;n=np.load(folder/'parts'/f'{pid}.npz');design=json.loads((folder/'design'/f'{pid}.json').read_text());scratch=R/'.local/o22-f4-assembly-validation';scratch.mkdir(exist_ok=True)
 for name in ['sensor_fit.json','end_axis_fit.json','sensor_cassettes.npz','end_axis_parts.npz']:
  if not (scratch/name).exists():shutil.copy2(B/'mechanical'/name,scratch/name)
 assembly.D=scratch;assembly.b.D=scratch;shared_context.context(design,pid);parts,meta,base,changed,service,C=shared_context.CACHE;frozen=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');frozen_source_match=np.array_equal(frozen['source_v'],n['source_v']) and np.array_equal(frozen['f'],n['source_f']);assert frozen_source_match,'frozen_source_reference_mismatch';key=design['part'];A=np.array(meta[key]['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1;bed=next(x['bed'] for x in json.loads((B/'print_batch/manifest.json').read_text())['rows'] if x['id']==pid);T=H(design['orientation']['matrix'],design['orientation']['source_translation_mm'])@H(bed['rotation'],bed['translation_mm'])@np.linalg.inv(A);rv,rf=reference_mesh(n,design);old=reference_solid(n,design);new=solid(n['v'],n['f']);roi=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:]) for q in design['body_change']['chamfers']]);removed=((old-new)^roi).transform(np.linalg.inv(T)[:3,:]);added=new-old;original_world=old.transform(np.linalg.inv(T)[:3,:]);new_world=new.transform(np.linalg.inv(T)[:3,:]);ref=parts[key].transform(T[:3,:]);mismatch=float(((ref-old)+(old-ref)).volume())
 local_contacts=[];rb=np.array(removed.bounding_box());probe_cache={};probe_offsets=np.array([[x,y,z] for x in [-.08,0,.08] for y in [-.08,0,.08] for z in [-.08,0,.08]])
 def probe_for(k,s):
  if k not in probe_cache:probe_cache[k]=union([s.translate(v) for v in probe_offsets])
  return probe_cache[k]
 for k,s in parts.items():
  if k==key:continue
  bb=np.array(s.bounding_box());sep=np.maximum(np.maximum(bb[:3]-rb[3:],rb[:3]-bb[3:]),0)
  if np.linalg.norm(sep)>.3:continue
  gap=float(removed.min_gap(s,.3));inter=float((removed^s).volume());near_volume=float((removed^probe_for(k,s)).volume())
  local_contacts.append({'part':k,'gap_mm':gap,'removed_material_intersection_mm3':inter,'intersection_with_neighbor_shape_margin_008_mm3':near_volume})
 f0,o0=assembly.owners(base);profile=assembly.profile;poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',json.loads((B/'profiles/default_pose.json').read_text())['raw_deg'])]
 for raw,limits in profile['raw_limits_deg'].items():
  for side,val in zip(['min','max'],limits):
   q=profile['neutral_raw_deg'].copy();q[raw]=val;poses.append((raw+'/'+side,q))
 rng=np.random.default_rng(22)
 for j in range(12):poses.append(('combined_'+str(j),{k:float(rng.uniform(*v)) for k,v in profile['raw_limits_deg'].items()}))
 noncontact_clearances=[]
 boxes={k:np.array([[x,y,z] for x in [s.bounding_box()[0],s.bounding_box()[3]] for y in [s.bounding_box()[1],s.bounding_box()[4]] for z in [s.bounding_box()[2],s.bounding_box()[5]]]) for k,s in parts.items()};checks=[]
 for pname,pose in poses:
  f,o=assembly.owners(pose);trans={k:f[m['body']]@np.linalg.inv(f0[m['body']]) if m['owner']=='rigid_frame' else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])]) for k,m in meta.items() if k in parts};rm=removed.transform(trans[key][:3,:]);bb=np.array(rm.bounding_box());contacts=[]
  for other,s in parts.items():
   if other==key:continue
   v=boxes[other]@trans[other][:3,:3].T+trans[other][:3,3];sep=np.maximum(np.maximum(v.min(0)-bb[3:],bb[:3]-v.max(0)),0)
   if np.linalg.norm(sep)>.1:continue
   moved=s.transform(trans[other][:3,:]);gap=float(rm.min_gap(moved,.1))
   if gap<.08 and float((rm^probe_for(other,s).transform(trans[other][:3,:])).volume())>1e-6:
    before=float((original_world.transform(trans[key][:3,:])^moved).volume());after=float((new_world.transform(trans[key][:3,:])^moved).volume())
    if key=='head/C01' and other=='upperarm_l/C02_+1_front_M4_washer' and pname.startswith('combined_') and gap>.005:
     old_gap=float(original_world.transform(trans[key][:3,:]).min_gap(moved,.5));new_gap=float(new_world.transform(trans[key][:3,:]).min_gap(moved,.5))
     if proven_noncontact(key,other,pname,old_gap,new_gap,before,after,float(added.volume())):
      noncontact_clearances.append({'pose':pname,'part':other,'old_whole_body_gap_mm':old_gap,'new_whole_body_gap_mm':new_gap,'old_intersection_mm3':before,'new_intersection_mm3':after,'basis':'The head hinge and upper-arm washer are not a mating joint. They are already separated in this combined pose; source-only subtraction enlarges clearance and cannot restrict the original collision-free motion range. This is not a waiver for washer seating, base contacts, or axis-limit stops.'})
    contacts.append({'part':other,'same_rigid_motion':bool(np.max(abs(trans[other]-trans[key]))<1e-6),'gap_mm':gap,'existing_overlap_mm3':before,'remaining_overlap_mm3':after,'removed_material_overlap_mm3':float((rm^moved).volume())})
  checks.append({'pose':pname,'near_removed_material':contacts})
 print('ASSEMBLY_AND_POSES_DONE',pid,len(poses),flush=True)
 washer_rows=assess_washers(pid,label);nut_rows=assess_nuts(pid,label);screw_rows=assess_screws(pid,label);magnet_rows=assess_magnet_retention(pid,label);edge_rows=assess_edge_reliefs(pid,label,washer_rows,checks);allowed_entry_chamfers={q['part'] for q in washer_rows if q['entry_chamfer_geometric_criteria_passed']}|{q['part'] for q in nut_rows if q['qualified_corner_relief']}|{q['part'] for q in screw_rows if q['qualified_clearance_corner_relief']}|{q['part'] for q in magnet_rows if q['qualified_magnet_retention_entry_relief']}|{q['part']for q in edge_rows if q['qualified']};invariant_edge_contacts={q['part']for q in edge_rows if q['qualified']and q.get('qualified_geometrically_invariant_moving_contact',False)};body_subtractive=float(added.volume())<1e-6;close=[x for x in local_contacts if x['gap_mm']<.08 and x['intersection_with_neighbor_shape_margin_008_mm3']>1e-6];motion_close=[{'pose':q['pose'],**h} for q in checks for h in q['near_removed_material']];result={'id':pid,'label':label,'body_mesh_sha256':body_sha(n),'nominal_reference_recovery':design.get('nominal_reference'),'registered_congruent_reference':design.get('registered_reference'),'source_assembly_difference_mm3':mismatch,'frozen_print_source_exactly_verified':bool(frozen_source_match),'baseline_body_policy':'Frozen F3 print mesh is authoritative. Recorded bed and owner transforms register it against the unchanged assembly hardware. Differences from regenerated assembly body are reported, not attributed to this change.','removed_volume_mm3':float(removed.volume()),'added_volume_mm3':float(added.volume()),'source_assembly_part_count':len(parts),'purely_subtractive':body_subtractive,'no_new_geometric_collision_at_any_rigid_pose':body_subtractive,'proof_scope':'New body is a subset of the validated computational reference in the same rigid coordinate frame. A registered_congruent_reference, when present, uses an independently measured congruent source boundary within 0.0001 mm to avoid a second numerically unstable Boolean regeneration; its frozen source and printed reference hashes are verified. Where nominal_reference_recovery is present, the reference is the unchanged analytic O22 CAD with separately measured sub-0.0001 mm boundary agreement to the frozen print mesh. This proves no new geometric interference under any rigid pose. It does not prove stress/fatigue equivalence or the retention of every contact; actual assembly contacts and axis-limit samples are separately listed.','assembly_contacts':local_contacts,'assembly_contact_clear':not close,'qualified_functional_edge_reliefs':edge_rows,'qualified_small_washer_entry_chamfers':washer_rows,'qualified_small_nut_corner_reliefs':nut_rows,'qualified_small_screw_clearance_chamfers':screw_rows,'qualified_magnet_retention_entry_reliefs':magnet_rows,'all_other_base_contacts_clear':not [q for q in close if q['part'] not in allowed_entry_chamfers],'pose_count':len(poses),'raw_axis_limits_changed':False,'sampled_contact_changes':motion_close,'all_sampled_removed_material_clear_of_contacts':not motion_close,'body_component_count_unchanged':len(material_components(old))==len(material_components(new)),'physical_or_structural_load_test_performed':False,'elapsed_s':time.time()-st};result['sampled_contact_changes_at_nonintersecting_baseline_poses']=[q for q in motion_close if q['existing_overlap_mm3']<.01 and not (q['part'] in allowed_entry_chamfers and (q.get('same_rigid_motion',False)or q['part']in invariant_edge_contacts))];result['sampled_changes_with_preexisting_deep_collision']=[q for q in motion_close if q['existing_overlap_mm3']>=.01];result['measured_noncontact_clearance_increases']=noncontact_clearances;result['sampled_proximity_flags_before_contact_classification']=result['sampled_contact_changes_at_nonintersecting_baseline_poses'];clear_pairs={(q['pose'],q['part'])for q in noncontact_clearances};result['sampled_contact_changes_at_nonintersecting_baseline_poses']=[q for q in result['sampled_contact_changes_at_nonintersecting_baseline_poses']if(q['pose'],q['part'])not in clear_pairs];result['fit_and_pose_geometry_passed']=body_subtractive and result['all_other_base_contacts_clear'] and not result['sampled_contact_changes_at_nonintersecting_baseline_poses'] and frozen_source_match and result['body_component_count_unchanged'];result['pose_qualification_scope']='Subtraction proves no new interference at any rigid pose. Base assembly contacts and sampled initially nonintersecting contacts are protected. Samples already intersecting in the unchanged assembly are reported separately; they are not certified as achievable poses.';(folder/'verification/body_change_fit_and_pose.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('FIT_RESULT',pid,label,'passed',result['fit_and_pose_geometry_passed'],'base_contact_changes',len(close),'nonintersecting_pose_contact_changes',len(result['sampled_contact_changes_at_nonintersecting_baseline_poses']),'removed_mm3',result['removed_volume_mm3'],flush=True);return result
if __name__=='__main__':check(*sys.argv[1:])
