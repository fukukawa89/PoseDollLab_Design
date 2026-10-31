"""Summarize active O6 receipts; failed mechanics remain failed; legacy receipts immutable."""
from pathlib import Path
import argparse,collections,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO6/runs/o6_20260924_r1';V=H/'verification/revO6/runs/o6_20260924_r1';UE=Path('E:/UnrealProjects/DollSimulation')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def name(p):return p.resolve().relative_to(R).as_posix()
def build():
 reports=[]
 for sub in ('joint_L6_final','joint_M4_validated','service','bilateral_search','backpack','backspace','daisy'):reports+=sorted((V/sub).glob('*.json'))
 reports+=[V/'power.json',G/'joint_L6_validated/manifest.json',G/'joint_M4_validated/manifest.json',G/'bilateral_search/layout_search.json']
 inputs={}
 def consume(d):
  if isinstance(d,list):
   for x in d:consume(x)
  elif isinstance(d,dict):
   for field,val in d.items():
    if field in ('input_sha256','source_sha256') and isinstance(val,dict):
     for n,h in val.items():
      p=Path(n);p=p if p.is_absolute() else R/p
      assert p.is_relative_to(R),(field,n)
      assert p.is_file() and sha(p)==h,('stale input',n)
      inputs[name(p)]=h
    else:consume(val)
 for p in reports:consume(read(p))
 joints=[]
 for family,folder,checks,generator,expected_life in [('L6','joint_L6_validated','joint_L6_final','compact_interfaces.py',52),('M4','joint_M4_validated','joint_M4_validated','small_joint.py',32)]:
  m=read(G/folder/'manifest.json');assert sha(H/'cad/revO6'/generator)==m['generator_sha256'];inputs[name(H/'cad/revO6'/generator)]=m['generator_sha256']
  assert len(m['parts'])==m['part_count']==58 and not m['nominal_intersections'];assert m['female_thread_guide_pocket_intersection_mm3']==0
  for guard in m['boolean_volume_guards']:
   if guard['operation']=='thread_tool':assert abs(guard['relative_difference'])<=guard['allowed_relative_difference']
   else:assert guard['pass'] and abs(guard['conservation_error_mm3'])<=guard['tolerance_mm3']
  for p in m['parts']:assert sha(G/folder/p['step_file'])==p['step_sha256'];inputs[name(G/folder/p['step_file'])]=p['step_sha256']
  ass=read(V/checks/'assembly.json');life=read(V/checks/'lifecycle.json');ret=read(V/checks/'retention_reverse.json')
  assert ass['part_coverage_complete'] and ass['status']=='PASS_SAMPLED_NOMINAL' and all(not x['intersections'] for x in ass['steps'])
  assert len(life['states'])==expected_life and life['status']=='PASS_SCOPED_LIFE_GEOMETRY' and all(not x['intersections'] for x in life['states'])
  assert ret['all_24_attempts_blocked'] and len(ret['shim_translation_stops'])==24
  dims=[b-a for a,b in zip(m['bounds_mm'][:3],m['bounds_mm'][3:])]
  joints.append({'family':family,'parts':m['part_count'],'modeled_mass_g':m['modeled_mass_g'],'outside_mm':dims,'assembly_status':ass['status'],'wear_compression_cases':len(life['states']),'single_axis_rotation_step_deg':5,'reverse_guide_geometric_interval_deg':ret['total_reverse_free_angle_interval_deg'],'guide_translation_stops':24,'support_span_mm':m['support_span_mm'],'force_precision_and_manufacturing_qualification':False})
 service=read(V/'service/service.json');assert len(service['families'])==2 and all(x['status']=='PASS_SINGLE_JOINT_AXIAL_APPROACH' for x in service['families'])
 bil=read(V/'bilateral_search/bilateral.json');assert len(bil['cases'])==100 and bil['status']=='FAIL'
 for c in bil['cases']:assert len(c['first_hit_per_module_pair'])+len(c['fully_checked_clear_module_pairs'])==153
 motion=[]
 for char in ('manny','quinn'):
  cases=[x for x in bil['cases'] if x['character']==char];bad=[x for x in cases if x['first_hit_per_module_pair']];pairs=collections.Counter((x['axis_a'],x['axis_b']) for c in bad for x in c['first_hit_per_module_pair'])
  motion.append({'character':char,'cases':len(cases),'clear_module_only_cases':len(cases)-len(bad),'failed_cases':len(bad),'frequent_colliding_pairs':[{'axes':list(k),'cases':n} for k,n in pairs.most_common(8)],'scope':bil['scope']})
 loads=read(V/'bilateral_search/loads.json');assert loads['mass_hard_limit_kg'] is None and loads['complete_body_mass_g'] is None
 power=read(V/'power.json');pack=read(V/'backpack/backpack_study.json');space=read(V/'backspace/back_reservation.json');back=read(V/'backspace/back_modules.json');assert len(back['cases'])==200 and back['status']=='FAIL'
 for c in back['cases']:assert len(c['first_hit_per_module'])+len(c['fully_checked_clear_modules'])==18
 variants=[]
 for variant in back['variants']:
  cases=[x for x in back['cases'] if x['variant']==variant['name']];variants.append({'name':variant['name'],'outside_mm':variant['outer_width_height_depth_mm'],'cases':len(cases),'failed_cases':sum(bool(x['first_hit_per_module']) for x in cases)})
 daisy=read(V/'daisy/results.json');assert daisy['single_bit_faults_rejected']==2080 and not daisy['capture_eligible'] and not daisy['connected_to_production_firmware'] and len(daisy['known_undetectable_counterexamples'])==3
 # View meshes are derived from the two active manifests, not an alternate CAD.
 mesh=read(G/'review_mesh.json')
 for obj in mesh['models']:assert obj['manifest_sha256']==sha(G/('joint_'+obj['family']+'_validated')/'manifest.json')
 legacy={}
 for script in ('seal_revo5.py','seal_revo5cn.py'):
  proc=subprocess.run([sys.executable,str(R/'scripts'/script),'--verify'],cwd=R,capture_output=True);assert proc.returncode==0,proc.stdout+proc.stderr
  result=json.loads(proc.stdout);assert result['verified'];legacy[script]=result
 lock=read(H/'verification/revO5/deliveries/o5_20260924_d1/FINAL_SOURCE_LOCK.json');ue={**lock['ue'],**lock['user_uncommitted_preserved']}
 for n,h in ue.items():assert sha(UE/n)==h,('UE changed',n)
 sources=sorted(set((H/'cad/revO6').glob('*.py'))|set((R/'scripts').glob('*revo6*.py'))|set((R/'Firmware/PoseDollFullBody/revO6').glob('*.py')))
 for p in sources:compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
 results={'schema':'o6-checked-digital-iteration-v1','baseline_design_commit':'451cbe0aa0c0b4016bee3da4d1dedc340a4c28f1','run':'o6_20260924_r1','overall_status':'RESEARCH_ITERATION_COMPLETE_FULL_MECHANISM_FAILED_NOT_RELEASED','joints':joints,'total_wear_compression_cases':sum(x['wear_compression_cases'] for x in joints),'service':'Two single-joint axial-tool approaches only; whole-arm service not qualified','bilateral_motion':motion,'arm_loads':[{'character':x['character'],'arm_mass_budget_g':x['arm_mass_budget_g'],'modeled_nine_module_mass_g':x['modeled_nine_module_mass_g'],'low_mu_catalog_force_insufficient_axes':[a['axis'] for a in x['axes'] if not a['low_mu_catalog_point_meets_budget']],'actual_maximum_spring_force_known':False} for x in loads['characters']],'back_reuse':{'selected_outer_mm':pack['selected_reuse_trial']['outer_mm'],'nominal_box_volume_cm3':pack['selected_reuse_trial']['box_volume_cm3'],'old_six_boxes_cm3':pack['old_six_box_total_cm3_excludes_power_and_support'],'nominal_box_reduction_fraction':pack['selected_nominal_box_reduction_fraction'],'complete_PCBA_qualified':False},'back_space_search':{'candidates':space['candidate_count'],'anatomy_only_clear_candidates':space['clear_candidate_count'],'goal_poses':space['goal_count'],'path_states_per_character':space['states_per_character'],'maximum_path_step_deg':space['maximum_interpolation_step_deg'],'selected_anatomy_only_target_mm':space['selected_thin_target']['outer_width_height_depth_mm'],'actual_module_audit':variants,'conclusion':'Both selected boxes conflict with current arm modules. No qualified motion-compatible central back PCB established.'},'DC1':{'single_bit_mutations_rejected':daisy['single_bit_faults_rejected'],'known_undetectable_counterexamples':daisy['known_undetectable_counterexamples'],'capture_eligible':False,'physical_wire_count_per_segment_including_power':6,'new_central_PCB_exists':False},'peak_current_conditional_allocation_A':power['sum_A'],'peak_current_verified':False,'legacy_seal_verification':legacy,'UE_and_user_preserved_files':len(ue),'user_configuration_preserved':True,'new_python_sources_syntax_checked':len(sources),'active_input_files_hash_checked':len(inputs),'evidence_sha256':{name(p):sha(p) for p in reports},'dependency_sha256':inputs,'physical_tested':False,'manufacturing_released':False,'full_body_height_mm':None,'full_body_mass_g':None,'mass_hard_limit_kg':None,'commit_or_push_performed':False,'next_digital_work':['Real shared multi-axis shoulder/clavicle support and output links; current 18-module layout fails motions','Coupled back electronics, neck/chest/skin and harness packaging after shoulder space is defined','Native central controller and fault-binding design only if DC1 or another backed topology is justified'],'requires_hardware_or_missing_supplier_data':['Spring curves and max force; friction/bond/wear/torque reversal','Bearing/taper/shim fits and loaded sliding','Signal integrity, chain identity/order/count, failure isolation, peaks/protection and crimps']}
 return results

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');a=ap.parse_args();result=build()
 if a.verify:assert read(V/'results.json')==result,'Current evidence differs from saved O6 result'
 else:save(V/'results.json',result)
 print(json.dumps({'evidence_consistent':True,'full_design_pass':False,'joints_scoped_cases':result['total_wear_compression_cases'],'bilateral_failed_cases':sum(x['failed_cases'] for x in result['bilateral_motion']),'back_actual_module_audit':result['back_space_search']['actual_module_audit'],'active_input_files_hash_checked':result['active_input_files_hash_checked'],'UE_preserved_files':result['UE_and_user_preserved_files'],'physical_tested':False,'manufacturing_released':False}))
if __name__=='__main__':main()
