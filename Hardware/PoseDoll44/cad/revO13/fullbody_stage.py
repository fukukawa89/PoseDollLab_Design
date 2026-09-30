"""Whole-body registry + actual shoulder/arm geometry in a 480 mm reference.
Gray anatomical links and torso/leg volumes are reservations, never print parts.
"""
from clavicle_trial import *
from parts_library import Parts
import math
from build_compact_hinge import make as compact_make
from refine_compact_wrists import transform_states
PAGE=H/'tutorials/full-doll'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def merged_profile(char):
 p=read(H/f'generated/revO3/runs/o3_20260924_r3/layouts/{char}/anatomy_profile.json')
 for side in ('l','r'):
  arm=read(OUT/f'clavicle_trial/{char}_{side}_profile.json')
  names={n['id']:n for n in arm['nodes'] if n['id'].startswith(tuple(f'{x}_{side}' for x in ('clavicle','upperarm','elbow','forearm','hand','hand_tip')))}
  p['nodes']=[names.get(n['id'],n) for n in p['nodes']]
 p['profile_id']=f'o13_{char}_fullbody_design_8mm_shoulder_offsets'
 p['status']='DESIGN_ONLY_NOT_DEVICE_CALIBRATION'
 return p
def segment(a,b,r=5):
 d=np.asarray(b)-a;l=np.linalg.norm(d)
 if l<1e-6:return None
 z=d/l;u=np.array([0,0,1.]) if abs(z[2])<.9 else np.array([1.,0,0]);x=np.cross(u,z);x/=np.linalg.norm(x);M=np.c_[x,np.cross(z,x),z]
 return pose(md.Manifold.cylinder(l,r,circular_segments=16),M,a)
def geometry_model(s):
 t=tri(s.simplify(.09));v,inv=np.unique(np.round(t.reshape(-1,3),4),axis=0,return_inverse=True)
 return {'v':v.tolist(),'f':inv.reshape(-1,3).tolist()}
def main():
 PAGE.mkdir(parents=True,exist_ok=True)
 chosen=read(OUT/'clavicle_trial/motion.json')['candidate']
 lib=library();allstates=[];characters=[];models={}
 _,_,bare,packed=compact_make();lib.update({'compact_'+k:v for k,v in packed.items()})
 mounts=read(OUT/'compact_hinge/wrist_selected_endpoints.json')['mounts']
 carriers=np.load(OUT/'carriers/parts.npz')
 for char in ('manny','quinn'):
  for side in ('l','r'):lib[f'{char}_{side}/bridge']=Parts([from_tri(carriers[f'{char}_{side}_bridge'])])
 for key,g in lib.items():
  for i,s in enumerate(g.parts):models[f'{key}#{i}']=geometry_model(s)
 for char in ('manny','quinn'):
  p=merged_profile(char);save(f'fullbody/{char}_profile.json',p);T0,A0=fk(p,{})
  cap=read(H/f'mechanical_manifest/physical_{char}_41_capabilities.json')
  assert len(A0)==44 and set(A0)==set(cap['measured_axis_ids'])|set(cap['fixed_axis_values_rad'])
  slots=[]
  for n in p['nodes']:
   if 'axis_id' not in n:continue
   a=n['axis_id'];region=a.split('.')[0]
   isarm=region.startswith(('clavicle','upperarm','elbow','forearm','hand'))
   status='FIXED_PROTOCOL_SLOT' if a in cap['fixed_axis_values_rad'] else 'ACTUAL_NOMINAL_MODULES_PARTIAL_ASSEMBLY' if isarm else 'MECHANISM_NOT_YET_DETAIL_DESIGNED'
   slots.append({'axis':a,'status':status,'neutral_origin_mm':A0[a]['origin'].tolist(),'direction':A0[a]['direction'].tolist(),'self_hold_required':False,'self_hold_preferred':a not in cap['fixed_axis_values_rad']})
  ref=read(H/f'generated/revO3/runs/o3_20260924_r3/layouts/{char}/anatomy_profile.json');Tr,Ar=fk(ref,{})
  shifted={n:(T0[n][:3,3]-Tr[n][:3,3]).tolist() for n in ('upperarm_l.flex_frame','upperarm_r.flex_frame','hand_tip_l','hand_tip_r','head_tip','sole_l')}
  spine_gap=np.linalg.norm(A0['chest.yaw']['origin']-A0['waist.yaw']['origin'])
  # Copying an entire 73.5 mm shoulder mechanism into this interval cannot
  # be certified by treating its bounding box as empty. No redesign is forced by mass.
  characters.append({'character':char,'axis_slots':slots,'measured_slots':41,'fixed_slots':3,'arm_slots_with_reference_geometry':18,
    'neutral_anchor_delta_from_anatomy_mm':shifted,'waist_to_chest_center_distance_mm':float(spine_gap),
    'whole_shoulder_axial_envelope_mm':73.5,'spine_direct_reuse':'REQUIRES_DIFFERENT_PACKAGING; full shoulder axial envelope exceeds anatomical interval',
    'full_body_mass_g':None,'full_body_print_release':False})
  states=[s for s in read(OUT/'integrated_arm_states.json')['states'] if s['character']==char]
  neutral=next(st for st in states if st['pose']=='neutral')
  references=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']
  for name in ('sitting','crouch','head_tilt','hip_abduction','trunk_bend_twist','legs_crossed'):
   q=references[name];Tref,_=fk(p,q);D=Tref['chest']@np.linalg.inv(T0['chest'])
   objects=[{**o,'frame':(D@np.array(o['frame'])).tolist()} for o in neutral['objects']]
   states.append({'character':char,'pose':name,'requested_angles_deg':q,'objects':objects,'reference_only_pose':True})
  arm_checks={(r['character'],r['pose']):r['findings'] for r in read(OUT/'integrated_arms.json')['cases']}
  for state in states:
   T,A=fk(p,state['requested_angles_deg'])
   bones=[]
   for n in p['nodes']:
    if not n['parent'] or n['parent']=='device_base':continue
    a,b=T[n['parent']][:3,3],T[n['id']][:3,3]
    if np.linalg.norm(b-a)>1:
     bones.append({'id':n['id'],'a':a.tolist(),'b':b.tolist(),'radius':4 if n['id'].startswith(('hand','ball','toe')) else 6})
   objects=[]
   for o in state['objects']:
    objects += [{'key':f"{o['library']}#{i}",'frame':o['frame'],'label':o['id'],'role':'reserved_geometry' if o['library'].startswith('compact_') and i>=len(bare[o['library'].split('_')[1]].parts) else 'actual_geometry'} for i in range(len(lib[o['library']].parts))]
   # Display-only thin links deliberately do not imply missing carriers exist.
   allstates.append({'character':char,'pose':state['pose'],'q':state['requested_angles_deg'],'reference_only_pose':state.get('reference_only_pose',False),'objects':objects,'whole_arm_findings':arm_checks.get((char,state['pose']),[]),'bones':bones,
    'support_points':[T[n][:3,3].tolist() for n in ('pelvis','forearm_l','forearm_r')],
    'reference_only_regions':['neck/head','waist/chest','hips/legs/feet','structural carriers','PCBA/harness']})
 save('fullbody/registry.json',{'characters':characters,'scope':'All 44 semantic slots registered (41 measured + 3 fixed); arm modules are actual CAD but incomplete assembly, remaining mechanisms are anatomical references only.',
 'manual_support_allowed':True,'max_holding_torque_Nm':None,'full_body_manufacturing_released':False})
 save('fullbody/scenes.json',{'states':allstates})
 (PAGE/'models.js').write_text('window.O13_MODELS='+json.dumps(models,separators=(',',':'))+';',encoding='utf-8')
 (PAGE/'scenes.js').write_text('window.O13_SCENES='+json.dumps(allstates,separators=(',',':'))+';',encoding='utf-8')
 summary={'physical_feedback':read(H/'bench/observations/o12_20260929_user_feedback.json'),
  'requirements':read(H/'mechanical_manifest/requirements_revO13.json'),'registry':characters,
  'module_endpoints':read(OUT/'braked_module/target_motion.json'),
  'bilateral_endpoints':read(OUT/'clavicle_trial/motion.json'),
  'stock_assembly':read(OUT/'stock_assembly.json')}
 # Keep large detailed reports on disk; page receives compact counts.
 facts={'moduleCases':len(summary['module_endpoints']['cases']),'moduleFailures':sum(bool(x['findings']) for x in summary['module_endpoints']['cases']),
  'bilateralCases':len(summary['bilateral_endpoints']['cases']),'bilateralFailures':sum(bool(x['findings']) for x in summary['bilateral_endpoints']['cases']),
  'wholeArmCases':len(read(OUT/'integrated_arms.json')['cases']),'wholeArmFailures':sum(bool(r['findings']) for r in read(OUT/'integrated_arms.json')['cases']),'baselineWholeArmFailures':sum(bool(r['findings']) for r in read(OUT/'whole_arm_endpoints.json')['cases']),'unilateralCases':len(read(OUT/'compact_hinge/unilateral_endpoints.json')['cases']),'shoulderOffsetPerSideMm':8,'physicalCoupon':'用户报告装配与初步手感通过','springForceN':None,'torqueNm':None}
 save('summary.json',{'facts':facts,'feedback':summary['physical_feedback'],'body_registry':characters,'whole_body_released':False})
 (PAGE/'results.js').write_text('window.O13_RESULTS='+json.dumps(facts,ensure_ascii=False)+';',encoding='utf-8')
 core=[{'key':f'{key}#{i}','group':group,'label':key,'role':'actual_geometry'} for group,key in [('input','clav_input'),('ring','clav_ring'),('output','clav_output')] for i in range(len(lib[key].parts))]
 (PAGE/'core.js').write_text('window.O13_CORE='+json.dumps(core,separators=(',',':'))+';',encoding='utf-8')
 print('fullbody registry',len(characters),'scenes',len(allstates),'meshes',len(models),'model MB',(PAGE/'models.js').stat().st_size/1e6,flush=True)
if __name__=='__main__':main()
