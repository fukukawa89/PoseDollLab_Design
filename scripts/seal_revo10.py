"""Seal scoped O10 results; preserve explicit failures and empty observations."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,math
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO10/runs/o10_20260926_r1';DEST=G/'evidence_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Non-finite JSON '+x)))
def hpath(n):return H/n.replace('\\','/')
def upstream():
 results={}
 for v in (7,8,9):
  r=subprocess.run([sys.executable,'-X','utf8',str(R/f'scripts/seal_revo{v}.py'),'--verify'],cwd=R,capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;results[str(v)]=json.loads(r.stdout)
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
 if a.verify:
  data=read(DEST);bad=[n for n,h in data['repository_files_sha256'].items() if not (R/n).is_file() or sha(R/n)!=h];old=upstream();print(json.dumps({'verified':not bad,'checked_hashes':len(data['repository_files_sha256']),'errors':bad,'upstream':old,'physical_tested':False,'full_joint_pass':False,'full_body_pass':False,'manufacturing_released':False}));raise SystemExit(bool(bad))
 assert not DEST.exists(),'Existing seal is immutable; use a new run for later work.'
 old=upstream();files={Path(__file__),H/'docs/O10_JOINT_AND_TEST.zh-CN.md',H/'docs/REVIEW_REQUEST_REVO10.zh-CN.md'}
 for root in (H/'cad/revO10',G,H/'bench/revO10',H/'tutorials/design-lab'):
  files.update(p for p in root.rglob('*') if p.is_file() and p!=DEST and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.log'))
 for group in ('geometry','mass','methods','clavicle'):
  report=read(G/f'verification_{group}.json');assert report['complete']
  for row in report['processes']:
   assert row['exit_code']==0
   for name,digest in row['input_sha256'].items():assert sha(hpath(name))==digest,('stale process input',row['script'],name);files.add(hpath(name))
 y=read(G/'face_brake/continuous_yokes.json');assert y['status']=='CERTIFIED_NOMINAL_YOKE_PAIR_ONLY' and y['required_mm']==.6 and y['area_deg2']==10976 and not y['failed_cells'] and not y['unknown_cells']
 for name,digest in y['input_sha256'].items():assert sha(hpath(name))==digest,('stale continuous input',name);files.add(hpath(name))
 f=read(G/'face_brake/build.json');assert f['generator_sha256']==sha(H/'cad/revO10/build_face_brake.py');assert f['reference_thread_mesh_sha256']==sha(G/'face_brake/threads.npz');assert len(f['parts'])==28 and all(v['volume_mm3']>0 and v['solid_components']==1 for v in f['parts'].values())
 th=read(G/'face_brake/threads.json');assert th['generator_sha256']==sha(H/'cad/revO10/build_axle_threads.py') and th['nominal_intersection_mm3']<1e-6 and max(r['intersection_mm3'] for r in th['helical_withdrawal'])<1e-4
 target=read(G/'braked_module/target_motion.json');assert target['complete'] and len(target['cases'])==204 and not any(c['findings'] for c in target['cases'])
 for name,digest in target['input_sha256'].items():assert sha(hpath(name))==digest,('stale target',name)
 fixed=read(G/'face_brake/fixed_part_audit.json');assert fixed['input_sha256']==sha(G/'face_brake/parts.npz') and fixed['checked_pairs']==561 and not fixed['findings']
 tools=read(G/'face_brake/assembly_tools.json');assert len(tools['threaded_axles'])==4 and all(not t['findings'] for t in tools['straight_2p5mm_AF_tool_sweeps']);assert max(r['ring_intersection_mm3'] for a in tools['threaded_axles'] for r in a['helical_withdrawal'])<1e-4
 grid=read(G/'face_brake/boolean_motion.json');assert len(grid['cases'])==82 and grid['source_sha256']==sha(G/'face_brake/parts.npz');interior=[c for c in grid['cases'] if abs(c['alpha'])<28 and abs(c['beta'])<98];assert len(interior)==45 and all(not c['findings'] for c in interior);assert grid['cases'][-1]['alpha']==75 and grid['cases'][-1]['beta']==75 and grid['cases'][-1]['findings']
 clav=read(G/'clavicle_trial/motion.json');failed=[c for c in clav['cases'] if c['findings']];assert clav['complete'] and len(clav['cases'])==102 and len(failed)==2 and all(c['pose']=='clavicle_l.protract_20' for c in failed)
 reg=read(G/'method_regression.json');assert reg['status']=='PASS' and reg['test_observations_are_synthetic'] and not reg['hardware_tested']
 web=read(H/'tutorials/design-lab/verification/checks.json');assert web['status']=='PASS' and not web['errors']
 provenance=read(H/'tutorials/design-lab/assets/provenance.json')
 for name,digest in provenance['inputs_sha256'].items():assert sha(hpath(name))==digest,('stale page data',name);files.add(hpath(name))
 bench=read(H/'bench/revO10/plan.json');blank=read(H/'bench/revO10/measurement_template.json');assert blank['sample_id'] is None and blank['measured_axial_force_N'] is None and not bench['hardware_tested'];assert bench['source_load_sha256']==sha(G/'face_axis_loads.json') and not bench['nominal_stack_volume_findings']
 for part in read(H/'bench/revO10/step_export.json')['parts']:assert sha(H/'bench/revO10'/(part['part']+'.step'))==part['sha256'] and part['roundtrip_volume_error_mm3']<1e-6
 for rel in ('verification/revO7/delivery/DELIVERY_MANIFEST.json','generated/revO8/runs/o8_20260925_r1/evidence_manifest.json','generated/revO9/runs/o9_20260926_r1/evidence_manifest.json'):files.add(H/rel)
 summary={'yoke_pair_continuous_box_deg':[[-28,28],[-98,98]],'yoke_nominal_clearance_lower_bound_mm':.6,'certified_angle_cells':len(y['certified_cells']),'full_module_target_endpoints':204,'full_module_endpoint_failures':0,'unmerged_fixed_part_pairs':561,'reference_axle_withdrawal_positions':sum(len(a['helical_withdrawal']) for a in tools['threaded_axles']),'straight_tool_sweeps':4,'clavicle_trial_endpoints':102,'clavicle_trial_failed_endpoints':2,'new_method_regression_groups':len(reg['cases']),'web_check_groups':len(web['checks']),'single_site_material_test_min_hold_Nm':bench['required_single_site_min_hold_Nm']}
 result={'schema':'o10-scoped-design-and-test-input-v1','run_id':'o10_20260926_r1','status':'SCOPED_DIGITAL_RESULTS_LOCKED_MATERIAL_TEST_INPUT_NEEDED','summary':summary,'upstream_verification':old,'repository_files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'preserved_failures':[{'character':x['character'],'pose':x['pose'],'findings':x['findings']} for x in failed],'historical_not_acceptance':['rejected/ records checker/model failures, including invalid NaN mass data and superseded CAD reference thread STEP','finite_twist/ and internal_stops/ are earlier load-unqualified compact candidates','face_brake/initial*, signed_distance_rejected.json and quick_motion reports are history, not current acceptance','physical_axis_loads.json is the earlier compact module demand study; current is face_axis_loads.json'],'scope':'Hash integrity and scoped nominal checks only. Full joint continuous motion, full torso/arm connection, wires, fields, tolerances, structural loads, friction, wear and hardware communication remain open. Coupon testing informs dimensions; it neither replaces remaining digital work nor clears known collisions.','physical_tested':False,'full_joint_pass':False,'full_body_pass':False,'manufacturing_released':False}
 DEST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(files),'summary':summary},ensure_ascii=False))
if __name__=='__main__':main()
