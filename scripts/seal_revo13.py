"""Freeze final O13 files and explicit report dependencies, retaining open gates.
This is a final consistency snapshot, not a reconstruction of missing per-read
logs in exploratory runs and never a manufacturing release.
"""
from pathlib import Path
import json,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO13/runs/o13_20260929_r1';DEST=G/'evidence_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def upstream():
 r=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/seal_revo12.py'),'--verify'],cwd=R,capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;return json.loads(r.stdout)
def main():
 old=upstream()
 if '--verify' in sys.argv:
  m=read(DEST);bad=[n for n,v in m['repository_files_sha256'].items() if not (R/n).is_file() or sha(R/n)!=v]
  print(json.dumps({'verified':not bad,'files':len(m['repository_files_sha256']),'errors':bad,'upstream_O12_verified':old['verified'],'coupon_feedback':'PASS_USER_REPORTED','full_body_manufacturing_released':False}));raise SystemExit(bool(bad))
 assert not DEST.exists(),'Create a new run after sealing.'
 observation=read(H/'bench/observations/o12_20260929_user_feedback.json');req=read(H/'mechanical_manifest/requirements_revO13.json')
 assert observation['assembly_and_initial_hand_feel_gate']=='PASS_USER_REPORTED' and observation['measured_holding_torque_Nm'] is None and not observation['full_joint_tested']
 assert req['manual_external_support_allowed'] and req['mass_hard_limit_kg'] is None and req['spring_force_N'] is None and not req['reuse_210N_O11_reference'] and not req['full_body_manufacturing_released']
 core=read(G/'printed_core/build.json');assert not core['assembled_findings'] and core['generator_sha256']==sha(H/'cad/revO13/build_printed_core.py')
 assert all(core['parts'][n]['solid_components']==1 for n in ('C01','C02','C14','C15'))
 c=read(G/'braked_module/target_motion.json');assert c['complete'] and len(c['cases'])==204 and not any(r['findings'] for r in c['cases'])
 c=read(G/'clavicle_trial/motion.json');assert c['complete'] and len(c['cases'])==102 and not any(r['findings'] for r in c['cases'])
 c=read(G/'sampled_paths.json');assert c['complete'] and len(c['cases'])==102 and c['interior_samples']==3894 and not any(r['findings'] for r in c['cases'])
 c=read(G/'whole_arm_endpoints.json');assert sum(bool(r['findings']) for r in c['cases'])==10
 c=read(G/'compact_hinge/unilateral_endpoints.json');assert len(c['cases'])==136 and c['failed_endpoints']==0
 c=read(G/'carriers/endpoints.json');assert c['complete'] and c['failed_endpoints']==0 and set(c['single_printed_components'].values())=={1}
 c=read(G/'integrated_arms.json');assert c['complete'] and len(c['cases'])==102 and c['failed_endpoints']==6 and c['selected_back_box']['shift_down_mm']==8 and c['selected_back_box']['failed_endpoints']==0
 c=read(G/'integrated_loads.json');assert c['complete'] and c['full_body_mass_g'] is None
 for g in c['characters']:
  assert g['unmodeled_downstream_allowance_g']==144
  assert all(v['measured_hold_Nm'] is None and not v['self_holding_is_hard_gate'] for v in g['physical_axes'].values())
 c=read(G/'fullbody/registry.json');assert not c['full_body_manufacturing_released'] and all(g['measured_slots']==41 and g['fixed_slots']==3 and len(g['axis_slots'])==44 for g in c['characters'])
 ui=read(G/'page_checks.json');assert ui['status']=='PASS' and not ui['errors'] and not ui['badResponses'] and ui['core']['parts']==44 and ui['mobile']['scrollWidth']<=ui['mobile']['width'] and all(x['status']==200 for x in ui['links'])
 assert read(G/'delivery_checks.json')['status']=='PASS' and read(G/'method_checks.json')['count']==7
 checked=[]
 for n in ['stock_assembly.json','braked_module/target_motion.json','clavicle_trial/motion.json','whole_arm_endpoints.json','sampled_paths.json','loads.json','integrated_loads.json','page_checks.json']:
  d=read(G/n)
  for rel,digest in d.get('input_sha256',d.get('inputs_sha256',{})).items():
   p=R/rel if (R/rel).is_file() else H/rel;assert p.is_file() and sha(p)==digest,('changed report dependency',n,rel);checked.append({'report':n,'path':p.relative_to(R).as_posix(),'sha256':digest})
 files={Path(__file__),H/'docs/O13_FULL_DOLL_PROGRESS.zh-CN.md',H/'docs/REVIEW_REQUEST_REVO13.zh-CN.md',H/'bench/observations/o12_20260929_user_feedback.json',H/'mechanical_manifest/requirements_revO13.json',H/'generated/revO12/runs/o12_20260926_r1/evidence_manifest.json'}
 for root in (H/'cad/revO13',H/'bench/revO13',H/'tutorials/full-doll',G):files.update(p for p in root.rglob('*') if p.is_file() and p!=DEST and '__pycache__' not in p.parts and p.suffix not in ('.log','.tmp'))
 m={'schema':'o13-final-consistency-snapshot-v1','status':'USER_COUPON_PASS_DIGITAL_DESIGN_ADVANCED_OPEN_FULL_BODY_GATES','upstream':old,'explicit_dependencies_checked':checked,'repository_files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'snapshot_scope':'Final file consistency and explicit dependencies; exploratory runs do not all log each file read. Not manufacturing acceptance.','coupon_assembly_user_reported_pass':True,'full_joint_physical_tested':False,'actual_spring_force_N':None,'holding_torque_Nm':None,'open_combined_pose_failures':6,'full_body_manufacturing_released':False}
 DEST.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(files),'explicit_dependencies':len(checked),'status':m['status'],'upstream_O12_verified':old['verified']}))
if __name__=='__main__':main()
