"""Reconcile current O7 evidence. A consistent package is not a released design."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO7/runs/o7_20260924_r1';V=H/'verification/revO7/runs/o7_20260924_r1';UE=Path('E:/UnrealProjects/DollSimulation')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def name(p):return p.resolve().relative_to(R).as_posix()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def build():
 reports=[G/'LP6_current/manifest.json',G/'bilateral_current/layout_search.json',*[V/'LP6_current'/f for f in ['assembly.json','lifecycle.json','retention_reverse.json']],V/'L6_preload/lifecycle.json',V/'M4_preload/lifecycle.json',V/'pose_audit.json',V/'bilateral_current/bilateral.json',V/'loads.json',V/'back_coarse.json',V/'back_exact_targets.json',V/'back_paths/back_paths.json',V/'thread_regression.json',V/'hardware_boundary.json',V/'bench_import_tests.json',V/'bench_import.json',H/'bench/revO7/plan.json',H/'bench/revO7/coupons/manifest.json']
 inputs={}
 def consume(d):
  if isinstance(d,list):
   for x in d:consume(x)
  elif isinstance(d,dict):
   for field,value in d.items():
    if field in ('input_sha256','source_sha256') and isinstance(value,dict):
     for n,h in value.items():
      p=Path(n);p=p if p.is_absolute() else R/p;p=p.resolve();assert p.is_relative_to(R) and p.is_file() and sha(p)==h,('stale evidence input',n);inputs[name(p)]=h
    else:consume(value)
 for p in reports:
  d=read(p);assert d.get('status')!='RUNNING_INCOMPLETE',p;consume(d)
 m=read(G/'LP6_current/manifest.json');assert m['part_count']==len(m['parts'])==75 and not m['nominal_intersections'];assert sha(H/'cad/revO7/pancake_joint.py')==m['generator_sha256'];assert len(m['pcb_support_contact'])==2 and min(x['nominal_contact_area_mm2'] for x in m['pcb_support_contact'])>2.5
 for q in m['boolean_volume_guards']:
  if q['operation']=='thread_tool':assert abs(q['relative_difference'])<q['allowed_relative_difference']
  else:assert q['pass']
 assert len([q for q in m['boolean_volume_guards'] if q['operation']=='female_actual_material_removed_after_bore'])==3
 for row in m['parts']:
  p=G/'LP6_current'/row['step_file'];assert sha(p)==row['step_sha256'];inputs[name(p)]=sha(p)
 ass=read(V/'LP6_current/assembly.json');life=read(V/'LP6_current/lifecycle.json');ret=read(V/'LP6_current/retention_reverse.json')
 assert ass['status']=='PASS_SAMPLED_NOMINAL' and ass['part_coverage_complete'] and len(ass['steps'])==69 and len(ass['rotation'])==73 and all(not x['hits'] for x in ass['steps']+ass['rotation'])
 assert life['status']=='PASS_SCOPED_NOMINAL_GEOMETRY' and len(life['states'])==37 and all(not x['hits'] for x in life['states'])
 assert all(.3625-1e-8<=h<=.55 for x in life['states'] for h in x['spring_height_by_station_mm'])
 assert ret['all_translation_attempts_blocked'] and len(ret['six_direction_retention_at_0p2mm'])==30
 prior=[]
 for fam,n in [('L6',52),('M4',32)]:
  q=read(V/(fam+'_preload/lifecycle.json'));assert len(q['states'])==n and q['new_overtravel_states']==0 and all(not x['intersections'] for x in q['states']);prior.append({'family':fam,'states':n,'old_states_over_nominal_work_point':q['old_states_past_catalog_nominal_deflection'],'new_states_over_nominal_work_point':0})
 bil=read(V/'bilateral_current/bilateral.json');assert bil['status']=='FAIL' and len(bil['cases'])==102
 for c in bil['cases']:assert len(c['first_hit_per_module_pair'])+len(c['fully_checked_clear_module_pairs'])==153
 motion=[{'character':c,'states':51,'failed_states':sum(x['character']==c and bool(x['first_hit_per_module_pair']) for x in bil['cases'])} for c in ('manny','quinn')]
 back=read(V/'back_paths/back_paths.json');assert back['status']=='PASS_SAMPLED_EMPTY_RESERVATION_ONLY' and back['path_states_total']==1700 and back['goals_total']==102 and all(x['module_guard_failure_states']==x['capsule_guard_failure_pairs']==0 for x in back['cases'])
 bench=read(V/'bench_import_tests.json');assert bench['status']=='PASS_SOFTWARE_ONLY' and bench['count']==23 and read(V/'bench_import.json')['status']=='AWAITING_HARDWARE'
 plan=read(H/'bench/revO7/plan.json');assert plan['loads_sha256']==sha(V/'loads.json') and plan['source_sha256']==sha(R/'scripts/prepare_revo7_bench.py')
 for row in read(H/'bench/revO7/coupons/manifest.json')['parts']:
  p=H/'bench/revO7/coupons'/row['file'];assert sha(p)==row['sha256'];inputs[name(p)]=sha(p)
 mesh=read(G/'review_mesh.json')
 for obj in mesh['models']:
  p=(G/'LP6_current/manifest.json') if obj['family']=='LP6' else (H/'generated/revO6/runs/o6_20260924_r1/joint_L6_validated/manifest.json');assert obj['manifest_sha256']==sha(p)
 legacy={}
 for script in ['seal_revo5.py','seal_revo5cn.py','seal_revo6.py']:
  q=subprocess.run([sys.executable,str(R/'scripts'/script),'--verify'],cwd=R,capture_output=True);assert q.returncode==0,q.stdout+q.stderr;legacy[script]=json.loads(q.stdout);assert legacy[script]['verified']
 lock=read(H/'verification/revO5/deliveries/o5_20260924_d1/FINAL_SOURCE_LOCK.json');ue={**lock['ue'],**lock['user_uncommitted_preserved']}
 for n,h in ue.items():assert sha(UE/n)==h,('UE/user file changed',n)
 codes=sorted([p for p in (H/'cad/revO7').glob('*.py') if not p.name.startswith('diagnose')]+list((R/'scripts').glob('*revo7*.py')))
 for p in codes:compile(p.read_text(encoding='utf-8-sig'),str(p),'exec');inputs[name(p)]=sha(p)
 loads=read(V/'loads.json');pose=read(V/'pose_audit.json')
 return {'schema':'o7-digital-and-bench-evidence-v1','run':'o7_20260924_r1','overall_status':'DIGITAL_CANDIDATES_AWAITING_MATERIAL_TESTS_FULL_BODY_FAILED_NOT_RELEASED','joint':{'family':'LP6','parts':75,'outside_mm':[m['bounds_mm'][i+3]-m['bounds_mm'][i] for i in range(3)],'modeled_mass_g':m['modeled_mass_g'],'support_span_mm':m['support_span_mm'],'assembly_steps':69,'sampled_rotation_positions':73,'wear_compression_mismatch_states':37,'retention_attempts':30,'pcb_contact_area_mm2':[x['nominal_contact_area_mm2'] for x in m['pcb_support_contact']],'production_tolerances_strength_force_balance_and_tools_qualified':False},'bounded_O6_preload_checks':prior,'bilateral_motion':motion,'old_100_failed_states':sum(x['pose']!='arms_crossed_asymmetric_candidate' and bool(x['first_hit_per_module_pair']) for x in bil['cases']),'old_O6_failed_states':46,'out_of_range_legacy_states_retained':len(pose['out_of_range_states']),'asymmetric_crossed_candidates_still_fail_real_modules':True,'back_reservation':{'outer_width_height_depth_mm':back['target']['outer_width_height_depth_mm'],'local_bounds_mm':back['target']['local_bounds_mm'],'path_states':1700,'goal_count':102,'guard_mm':.5,'max_step_deg':5,'native_central_PCBA_exists':False,'empty_box_only':True,'whole_body_motion_qualified':False},'arm_mass_budgets_g':[c['arm_mass_budget_g'] for c in loads['characters']],'coupon_specs':4,'bench_import_mutation_checks':23,'hardware_results':'AWAITING_HARDWARE','legacy_seals':legacy,'UE_and_user_files_preserved':len(ue),'O7_python_sources_compiled':len(codes),'active_inputs_hash_checked':len(inputs),'evidence_sha256':{name(p):sha(p) for p in reports},'dependency_sha256':inputs,'physical_tested':False,'manufacturing_released':False,'whole_body_height_verified':False,'whole_body_mass_measured':False,'mass_hard_limit_kg':None,'next_step':'Traceable material coupons and spring load-height measurements, then loaded joint/force-balance tests and multiaxis redesign. See bench/revO7/README.zh-CN.md.','commit_or_push_performed':False}
def main():
 a=argparse.ArgumentParser();a.add_argument('--verify',action='store_true');o=a.parse_args();d=build()
 if o.verify:assert read(V/'results.json')==d,'Saved O7 result differs from active evidence'
 else:save(V/'results.json',d)
 print(json.dumps({k:d[k] for k in ['overall_status','active_inputs_hash_checked','bilateral_motion','back_reservation','UE_and_user_files_preserved','hardware_results']}))
if __name__=='__main__':main()
