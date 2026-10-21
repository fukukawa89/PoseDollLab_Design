"""Assess small permanent print fillets against O22 hardware, service voids and sampled poses."""
from pathlib import Path
import sys,json,numpy as np,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from verify_revo22_f4_body_change import check as assess_removed,H
from o22_reference_mesh import reference_mesh
from build_revo22_fins import solid,union,box,protected
import repair_revo22_f4_guarded_chamfer as ctx
import build_revo22_assembly as assembly
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';B=O.parent

def check(pid,label):
 st=time.time();folder=O/'candidates'/pid/label;result=assess_removed(pid,label);d=json.loads((folder/'design'/f'{pid}.json').read_text());n=np.load(folder/'parts'/f'{pid}.npz');parts,key,T=ctx.context(d,pid);parts,meta,base,*_=ctx.CACHE;rv,rf=reference_mesh(n,d);old=solid(rv@np.array(d['orientation']['matrix']).T+np.array(d['orientation']['source_translation_mm']),rf);new=solid(n['v'],n['f']);rois=union([box(r['local_bounds_mm'][:3],r['local_bounds_mm'][3:]) for r in d['body_change'].get('additions',[])]);added=(new-old)^rois;assert abs(added.volume()-(new-old).volume())<1e-5,'Undeclared added material';aw=added.transform(np.linalg.inv(T)[:3,:]);vols=next((v['volumes'] for v in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects'] if v['part']==key),[]);ban=protected(vols).transform(np.c_[d['orientation']['matrix'],d['orientation']['source_translation_mm']]);void_overlap=float((added^ban).volume());f0,o0=assembly.owners(base);profile=assembly.profile;poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',json.loads((B/'profiles/default_pose.json').read_text())['raw_deg'])]
 for raw,limits in profile['raw_limits_deg'].items():
  for side,val in zip(['min','max'],limits):
   q=profile['neutral_raw_deg'].copy();q[raw]=val;poses.append((raw+'/'+side,q))
 rng=np.random.default_rng(22)
 for j in range(12):poses.append(('combined_'+str(j),{k:float(rng.uniform(*v)) for k,v in profile['raw_limits_deg'].items()}))
 boxes={k:np.array([[x,y,z] for x in [s.bounding_box()[0],s.bounding_box()[3]] for y in [s.bounding_box()[1],s.bounding_box()[4]] for z in [s.bounding_box()[2],s.bounding_box()[5]]]) for k,s in parts.items()};offsets=np.array([[x,y,z] for x in [-.2,0,.2] for y in [-.2,0,.2] for z in [-.2,0,.2]]);probes={};checks=[]
 for name,pose in poses:
  f,o=assembly.owners(pose);trans={k:f[m['body']]@np.linalg.inv(f0[m['body']]) if m['owner']=='rigid_frame' else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])]) for k,m in meta.items() if k in parts};a=aw.transform(trans[key][:3,:]);bb=np.array(a.bounding_box());hits=[]
  for other,s in parts.items():
   if other==key:continue
   v=boxes[other]@trans[other][:3,:3].T+trans[other][:3,3];sep=np.maximum(np.maximum(v.min(0)-bb[3:],bb[:3]-v.max(0)),0)
   if np.linalg.norm(sep)>.36:continue
   moved=s.transform(trans[other][:3,:]);gap=float(a.min_gap(moved,.36))
   if gap>.35:continue
   if other not in probes:probes[other]=union([s.translate(v) for v in offsets])
   overlap=float((a^probes[other].transform(trans[other][:3,:])).volume())
   if overlap>1e-6:hits.append({'part':other,'gap_mm':gap,'new_material_in_02mm_neighbor_envelope_mm3':overlap,'new_overlap_mm3':float((a^moved).volume())})
  checks.append({'pose':name,'new_material_clearance_violations':hits})
 rejected=[{'pose':p['pose'],**h} for p in checks for h in p['new_material_clearance_violations']];identity=max(abs((old-old).volume()),abs((new-new).volume()));result.update(addition_validation={'added_volume_mm3':float(added.volume()),'declared_additions':d['body_change'].get('additions',[]),'protected_service_void_overlap_mm3':void_overlap,'neighbor_margin_mm':.2,'pose_count':len(poses),'pose_checks':checks,'new_clearance_violations':rejected,'all_sampled_additions_clear':not rejected,'body_boolean_identity_error_mm3':identity},no_new_geometric_collision_at_any_rigid_pose=False,proof_scope='The subtractive portion cannot introduce rigid interference. Added permanent print fillets are separately checked against protected service voids and every actual neighboring solid expanded by 0.2 mm at the listed base, neutral, default, individual axis limits and 12 deterministic combined poses. This is sampled kinematic verification, not a proof over all coupled continuous poses and not a strength or fatigue test.',pose_qualification_scope='Original axes, joint centers and limits are unchanged. No new material may enter another part or its 0.2 mm clearance envelope in any listed pose; no preexisting-collision exception is made for added material. Continuous coupled motion and physical loads have not been tested.')
 result['fit_and_pose_geometry_passed']=result['frozen_print_source_exactly_verified'] and result['body_component_count_unchanged'] and result['all_other_base_contacts_clear'] and not result['sampled_contact_changes_at_nonintersecting_baseline_poses'] and not rejected and void_overlap<1e-6 and identity<1e-6
 result['elapsed_s']+=time.time()-st;(folder/'verification/body_change_fit_and_pose.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('ADDITIVE_FIT',pid,label,result['fit_and_pose_geometry_passed'],'violations',len(rejected),'void',void_overlap,flush=True);return result
if __name__=='__main__':check(*sys.argv[1:])
