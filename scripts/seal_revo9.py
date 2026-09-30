"""Seal the O9 core-motion evidence without releasing hardware or full assembly."""
import argparse,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO9/runs/o9_20260926_r1';DEST=G/'evidence_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');args=ap.parse_args()
 if args.verify:
  d=read(DEST);bad=[n for n,h in d['repository_files_sha256'].items() if not (R/n).is_file() or sha(R/n)!=h];print(json.dumps({'verified':not bad,'checked_hashes':len(d['repository_files_sha256']),'errors':bad,'physical_tested':False,'full_joint_pass':False,'full_body_pass':False,'manufacturing_released':False}));sys.exit(bool(bad))
 y=read(G/'continuous_yoke_workspace.json');other=read(G/'continuous_other_core_pairs.json');paths=read(G/'bounded_mapping.json');audit=read(G/'path_audit.json');grid=read(G/'core_motion_grid.json');assembly=read(G/'assembly_path.json');tool=read(G/'restricted_tool_access.json');web=read(H/'tutorials/motion-lab/verification/checks.json')
 assert y['status']=='CERTIFIED_SCOPED_NOMINAL_YOKE_WORKSPACE' and y['required_mm']==.6 and y['interval_area_deg2']==12000 and not y['failed_cells'] and not y['unknown_cells']
 assert other['status']=='COMPLETE' and len(other['pairs'])==6 and all(p['status']=='CERTIFIED_CONTINUOUS_SCOPED_PAIR' for p in other['pairs'])
 for report in (y,other):
  for rel,digest in report['input_receipt_sha256'].items():assert sha(H/rel)==digest,('stale input receipt',rel)
 assert len(paths['characters'])==4 and all(g['pass']==51 and g['fail']==0 for g in paths['characters'])
 assert all(p['max_matrix_error']<1e-8 for g in paths['characters'] for p in g['paths'])
 assert audit['total_retained_targets']==204 and audit['sampled_rotations']==8088 and audit['continuous_angle_linear_segments']==7884
 assert len(grid['cases'])==64 and sum(p['status']=='CLEAR_DISCRETE_CORE' for p in grid['cases'])==63
 assert grid['cases'][-1]['status']=='FAIL' and (grid['cases'][-1]['alpha_deg'],grid['cases'][-1]['beta_deg'])==(75,75)
 assert sum(len(s['cases']) for s in assembly['stages'])==123 and all(p['status']=='CLEAR_DISCRETE_ASSEMBLY' for s in assembly['stages'] for p in s['cases'])
 assert len(tool['tools'])==4 and all(p['clear_pose_in_working_rectangle'] is not None for p in tool['tools'])
 reg={name:read(G/(name+'.json')) for name in ('continuous_method_regression','journal_method_regression','rigid_collision_regression_final')};assert all(p['status']=='PASS' for p in reg.values());assert web['status']=='PASS'
 for x in read(H/'tutorials/motion-lab/assets/provenance.json')['inputs']:assert sha(H/x['path'])==x['sha256'],('stale page asset',x['path'])
 sys.path.insert(0,str(H/'cad/revO9'))
 import numpy as np
 from relieve_cup import relieved
 from extend_forks import topology,volume
 import struct
 def read_stl(p):
  b=p.read_bytes();n=struct.unpack('<I',b[80:84])[0];assert len(b)==84+50*n
  dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')]);return np.frombuffer(b,dtype=dtype,count=n,offset=84)['vertices'].astype(float)
 folder=G/'cup_relief_L3_R0p35';expected=relieved(3,.35);saved=dict(np.load(folder/'core_meshes.npz'));roundtrips=[]
 for name,t in expected.items():
  assert np.array_equal(t,saved[name]),('generator differs from exported candidate',name)
  p=folder/(name+'.stl');m=read_stl(p);check=topology(m);assert not any(check[k] for k in ('boundary_edges','nonmanifold_edges','zero_area_faces'))
  delta=abs(volume(m)-volume(t));assert delta<.001,(name,delta);roundtrips.append({'file':p.relative_to(R).as_posix(),'topology':check,'volume_roundtrip_error_mm3':delta})
 files={Path(__file__),H/'docs/O9_MOTION_VALIDATION.zh-CN.md',H/'docs/TANGIBLE_2014_2016_REUSE.zh-CN.md',H/'cad/model.py',H/'generated/revO8/runs/o8_20260925_r1/evidence_manifest.json'}
 for d in (H/'cad/revO9',G,H/'tutorials/motion-lab'):
  files.update(p for p in d.rglob('*') if p.is_file() and p!=DEST and '__pycache__' not in p.parts and p.suffix not in ('.log','.pyc'))
 for report in (y,other):files.update(H/p for p in report['input_receipt_sha256'])
 files.update(H/x['path'] for x in read(H/'tutorials/motion-lab/assets/provenance.json')['inputs'])
 old=H/'generated/revO7/runs/o7_20260924_r1/bilateral_current';files.add(old/'layout_search.json');files.update(old.glob('*_profile.json'))
 files.update((H/'cad/revO8').glob('*.py'));g8=H/'generated/revO8/runs/o8_20260925_r1';files.update(g8.rglob('*.npz'));files.update([g8/'shoulder_mapping.json',g8/'fastened_core/report.json'])
 summary={'yoke_continuous_angle_box_deg':[[-30,30],[-100,100]],'yoke_nominal_clearance_lower_bound_mm':.6,'yoke_certificate_cells':len(y['certified_cells']),'other_continuous_moving_pairs':6,'retained_pose_targets':204,'sampled_rotations':8088,'continuous_candidate_path_segments':7884,'max_checked_midpoint_rotation_deviation_deg':audit['max_midpoint_rotation_deviation_deg'],'discrete_core_pass_fail':[63,1],'assembly_positions':123,'restricted_straight_tool_access_cases':4,'regression_groups':{k:len(v['cases']) for k,v in reg.items()},'web_check_groups':len(web['checks'])}
 d={'schema':'revo9-motion-evidence-v1','run_id':'o9_20260926_r1','status':'SCOPED_CORE_DIGITAL_VALIDATION_COMPLETE_FULL_ASSEMBLY_OPEN','summary':summary,'repository_files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'selected_candidate':'cup_relief_L3_R0p35','stl_roundtrip_checks':roundtrips,'experimental_history_not_used_for_acceptance':['allocation_phi_grid_experiment.json: uniform phi grid misses near-singular valid decompositions','bounded_mapping_alpha30.json: earlier allocation without alpha limit margin','continuous_core_pairs.py and initial/uncapped logs: generic interval refinement experiments; final moving-pair proof is verify_journal_sweeps.py','clearance_rectangle_probe.json and extension_midangle_counterexample.json retain insufficiency witnesses'], 'open_digital_work':['Physical stops and finite external twist joints','Continuous restrained cable route, strain relief and wire bending','Full PCBA, housings, shoulder and arm joint assembly','Body motion and complete component mass/load accounting'],'scope':'Hashes lock stored evidence. Continuous core geometry does not qualify manufacturing tolerances, holding torque, wear, sensor accuracy, unrestricted movement or full-body fit. Process coupons are optional independent experiments, not a prerequisite for remaining digital work.','physical_tested':False,'mechanical_stops_modeled':False,'wiring_qualified':False,'full_joint_pass':False,'full_body_pass':False,'manufacturing_released':False}
 DEST.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(files),'summary':summary},ensure_ascii=False))
if __name__=='__main__':main()
