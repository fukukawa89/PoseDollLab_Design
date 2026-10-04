"""Per-part COM ledger, support-reaction envelopes, friction and tolerance studies.
Analytical assumptions are data, never substituted for full CAD or physical gates.
"""
from revo2_evidence import *
import math,sys,copy
import numpy as np
import itertools
from study_revo import anatomy,family
sys.path.insert(0,str(HW/'cad/revE'))
from character_reference import reference_character,align
from model import fk,rotation
G=9.80665

def measure_character(name):
 c=reference_character(name);scale=480/c['height_mm'];c['vertices_mm']*=scale
 for n in c['points']:c['points'][n]*=scale
 for n in c['surfaces']:c['surfaces'][n]*=scale
 return c

def ledger(character,joint,old,boards):
 p=anatomy(character,480);T,A=fk(p,{});nodes={n['id']:n for n in p['nodes']};c=measure_character(character);rows=[]
 def add(pid,mat,owner,mass,world,source,unc=.3,scope='allocation'):
  local=np.linalg.inv(T[owner])@np.r_[world,1]
  rows.append({'part_id':pid,'material':mat,'owner':owner,'local_com_mm':local[:3].tolist(),'mass_g':float(mass),'mass_source':source,'uncertainty_fraction':unc,'scope':scope})
 for aid,a in A.items():
  if aid.startswith('pelvis.'):continue
  legacy_family=family(aid);parts=joint['parts'] if legacy_family=='L6' else old[legacy_family]
  basis=align([0,0,1],nodes[a['node']]['axis_local'])
  for part in parts:
   owner=a['node'] if part['owner']=='child' else nodes[a['node']]['parent']
   world=a['origin']+a['frame'][:3,:3]@basis@np.array(part['local_com_mm'])
   add(aid+'/'+part['part_id'],part['material'],owner,part['mass_g'],world,part['mass_source'],part['uncertainty_fraction'],'R2 CAD part on provisional axis transform' if legacy_family=='L6' else 'O1 mass reference; mechanism not assemblable')
 # Preserve all old unmodelled categories. Do not claim they disappear with new CAD.
 # The 100 g fastener allowance remains conservative until every other family is itemized.
 candidates=[(n,T[n['parent']][:3,3],T[n['id']][:3,3]) for n in p['nodes'] if n['parent'] and n['parent']!='device_base' and np.linalg.norm(T[n['parent']][:3,3]-T[n['id']][:3,3])>5]
 lengths=np.array([np.linalg.norm(b-a) for n,a,b in candidates]);total=lengths.sum()
 for n,a,b in candidates:
  frac=np.linalg.norm(b-a)/total;owner=n['parent'];mid=(a+b)/2
  for category,mass,material in [('frames_links',150,'mixed frame allowance'),('harness',90,'copper plus insulation'),('unresolved_fasteners_springs',100,'mixed hardware allowance')]:
   add(category+'/'+n['id'],material,owner,mass*frac,mid,'Retained named engineering allocation, distributed by segment length; not an actual routed or structural BOM',.5)
 for owner,mass in [('head',40),('foot_l',35),('foot_r',35),('hand_l',10),('hand_r',10)]:
  # Surface-derived volumetric distribution surrogate, never place a head mass exactly at its pivot.
  pts=c['surfaces'][owner];com=(pts.min(axis=0)+pts.max(axis=0))/2
  add('cover/'+owner,'printed shell allocation',owner,mass,com,'Head/hand/foot surface bounds centre at 480 mm; actual shell CAD COM pending',.35)
 for node,owner,mass,offset in [('N1','pelvis',15,[8,0,5]),('N2','chest',20,[-12,0,-15]),('N3_prox','chest',17,[12,20,0]),('N4_prox','chest',17,[12,-20,0]),('N3_distal','upperarm_l',9,[0,0,-35]),('N4_distal','upperarm_r',9,[0,0,-35]),('N5','thigh_l',20,[0,0,-35]),('N6','thigh_r',20,[0,0,-35])]:
  add('acquisition_pcba/'+node,'FR4/copper/components mixed allocation',owner,mass,T[owner][:3,3]+offset,'Eight PCBA allocation totals 127 g; supersedes 120 g six-PCBA allowance; bare PCB is only a subset',.35)
 add('power_distribution','mixed electrical protection','pelvis',35,T['pelvis'][:3,3]+[0,0,-10],'Retained protection/pelvis connector allocation',.5)
 add('two_new_interboard_links','copper/polymer/contact alloy','chest',12,T['chest'][:3,3],'Additional two 14-conductor interboard harnesses and mating pairs; estimate beyond legacy 90 g harness',.5)
 return p,c,rows

def support_study(p,rows):
 poses=read(HW/'mechanical_manifest/revO_pose_cases.json')['cases'];parents={n['id']:n['parent'] for n in p['nodes']}
 def descendant(n,root):
  while n is not None:
   if n==root:return True
   n=parents[n]
  return False
 cases=[('hand_pelvis_'+n,a,'hand_pelvis',np.eye(3)) for n,a in poses.items() if n not in ('left_side_lying','right_side_lying','prone')]
 cases += [('double_foot',{},'double_foot',np.eye(3)),('single_foot',{'thigh_r.flex':40,'calf_r.flex':60},'single_foot',np.eye(3)),('seated',poses.get('sitting',{}),'seated',np.eye(3)),('kneeling',poses['kneeling'],'kneeling',np.eye(3)),('left_side_lying',{},'lying',rotation([1,0,0],-90)),('right_side_lying',{},'lying',rotation([1,0,0],90)),('prone',{},'lying',rotation([0,1,0],90))]
 loads={a:{'axis_id':a,'max_abs_gravity_contact_Nm':0,'case':None} for a in p['axis_order'][3:]};reports=[]
 for cname,pose,mode,R in cases:
  T,A=fk(p,pose);mp=np.array([R@(T[m['owner']]@np.r_[m['local_com_mm'],1])[:3] for m in rows]);kg=np.array([m['mass_g']/1000 for m in rows]);weight=kg.sum()*G;com=np.average(mp,axis=0,weights=kg)
  contacts=[]
  def patch(owner,dx=15,dy=9,offset=None):
   origin=T[owner][:3,3]+(np.array(offset) if offset is not None else 0)
   for x,y in [(-dx,-dy),(-dx,dy),(dx,-dy),(dx,dy)]:contacts.append({'owner':owner,'point':R@(origin+[x,y,0])})
  if mode in ('double_foot','single_foot'):
   patch('foot_l',18,9,[12,0,-8])
   if mode=='double_foot':patch('foot_r',18,9,[12,0,-8])
  elif mode=='seated':patch('pelvis',18,18,[0,0,-15]);patch('foot_l',18,9,[12,0,-8]);patch('foot_r',18,9,[12,0,-8])
  elif mode=='kneeling':patch('calf_l',8,10);patch('calf_r',8,10);patch('foot_l',10,8);patch('foot_r',10,8)
  elif mode=='lying':
   for owner in ('head','chest','pelvis','upperarm_l','upperarm_r','thigh_l','thigh_r','foot_l','foot_r'):patch(owner,8,8)
  feasible=True;Aeq=None;beq=None
  if contacts:
   Aeq=np.array([[1]*len(contacts),[q['point'][0]/1000 for q in contacts],[q['point'][1]/1000 for q in contacts]])
   beq=np.array([weight,weight*com[0]/1000,weight*com[1]/1000]);reaction_vertices=[]
   # Linear support problem has three equality constraints. Enumerating
   # nonnegative basic solutions gives exact extrema over the assumed patches.
   for ids in itertools.combinations(range(len(contacts)),3):
    matrix=Aeq[:,ids]
    if abs(np.linalg.det(matrix))<1e-12:continue
    force=np.linalg.solve(matrix,beq)
    if np.min(force)<-1e-7:continue
    full=np.zeros(len(contacts));full[list(ids)]=np.maximum(force,0);reaction_vertices.append(full)
   reactions=np.array(reaction_vertices);feasible=bool(reaction_vertices)
  reports.append({'case':cname,'mode':mode,'static_contact_equilibrium':'FEASIBLE_ASSUMED_CONTACT_PATCHES' if feasible and contacts else ('HAND_REACTION_WRENCH_ASSUMED' if not contacts else 'FAIL_COM_OUTSIDE_CONTACT_SUPPORT'),'contact_points':[{**q,'point':q['point'].tolist()} for q in contacts],'COM_world_mm':com.tolist(),'ground_shape_contact':'NOT_RUN_ACTUAL_SHELL_AND_CONTACT_HEIGHTS_MISSING','pose_deg':pose})
  for aid,a in A.items():
   if aid not in loads:continue
   origin=R@a['origin'];direction=R@a['direction'];mask=np.array([descendant(m['owner'],a['node']) for m in rows]);gravity=np.cross((mp[mask]-origin)/1000,np.column_stack([np.zeros(sum(mask)),np.zeros(sum(mask)),-kg[mask]*G])).sum(axis=0)
   base=float(direction@gravity);lo=hi=base
   if contacts and feasible:
    coefficients=np.array([float(direction@np.cross((q['point']-origin)/1000,[0,0,1])) if descendant(q['owner'],a['node']) else 0 for q in contacts])
    moments=reactions@coefficients;lo=base+float(moments.min());hi=base+float(moments.max())
   if feasible and max(abs(lo),abs(hi))>loads[aid]['max_abs_gravity_contact_Nm']:loads[aid].update(max_abs_gravity_contact_Nm=max(abs(lo),abs(hi)),case=cname,signed_interval_Nm=[lo,hi])
 for aid,q in loads.items():
  torque=q['max_abs_gravity_contact_Nm'];grip=.03 if aid.startswith(('head.','hand_','ball_')) else .06;cable=.01 if grip==.03 else .02;hold=1.5*(torque+cable);reff=2/3*(.012**3-.0042**3)/(.012**2-.0042**2);preload=hold/(2*.08*reff)
  q.update(cable_torque_assumption_Nm=cable,required_holding_Nm=hold,two_face_L6_required_preload_low_mu_N=preload,grip_distance_m=grip,operating_force_against_gravity_N=(hold*.22/.08+torque+cable)/grip,operating_force_with_gravity_N=max(0,(hold*.22/.08-torque-cable)/grip),friction_coefficient_uncertainty=[.08,.22],coefficient_ratio_is_not_static_dynamic_ratio=True)
  q['catalog_candidates']={'S4_O1_exploratory_one_face_100N':hold<=.08*100*.005942857,'M6_O1_exploratory_one_face_220N':hold<=.08*220*.008,'L6_R2_two_face_326N':preload<=326}
  q['selected_manufacturing_family']=None;q['selection_status']='BLOCKED_OTHER_FAMILIES_NOT_ASSEMBLABLE_AND_PHYSICAL_PRECISION_NOT_RUN'
 return list(loads.values()),reports

def main():
 verify,out=run_paths();joint=read(verify/'joint.json');old=read(verify/'legacy_mass_reference.json');boards=read(verify/'electronics.json');chars={}
 for ch in ('manny','quinn'):
  p,c,rows=ledger(ch,joint,old,boards);loads,supports=support_study(p,rows);total=sum(q['mass_g'] for q in rows);unc=sum(q['mass_g']*q['uncertainty_fraction'] for q in rows)
  chars[ch]={'reference_height_mm':480,'status':'ANALYTICAL_MASS_AND_LOAD_STUDY_NOT_FULL_ASSEMBLY','mass_properties':rows,'total_budget_g':total,'worst_sum_uncertainty_g':unc,'target_g':1200,'target_status':'PASS_BUDGET_ONLY' if total+unc<=1200 else 'FAIL_BUDGET_OR_UNCERTAINTY','actual_complete_CAD_mass_g':None,'load_rows':loads,'support_cases':supports,'joint_basis':'O1 family assignment retained only to compare mass; final family selected per-axis is explicitly unset','COM_transform_scope':'Actual single-part COMs mapped into provisional ideal anatomy; multi-axis offsets unbuilt','head_pitch_check':next(q for q in loads if q['axis_id']=='head.pitch')}
  save(out/'layouts'/ch/'anatomy_profile.json',p)
  save(out/'layouts'/ch/'scene.json',{'nodes':{n:matrix[:3,3].tolist() for n,matrix in fk(p,{})[0].items()},'surface_vertices_mm':c['vertices_mm'][::3].tolist(),'mass_COMs':[{k:q[k] for k in ('part_id','mass_g','owner','local_com_mm','scope')} for q in rows]})
  print(ch,'mass budget',round(total,2),'head pitch Nm',round(chars[ch]['head_pitch_check']['max_abs_gravity_contact_Nm'],4),'L6 insufficient',[q['axis_id'] for q in loads if q['two_face_L6_required_preload_low_mu_N']>326],flush=True)
 save(verify/'mass_properties_revO2.json',{'characters':chars,'mass_sources':['BRep volume and material density','Separate component-class estimates for sensor solids','Explicit retained allowances for all unmodelled assemblies'],'body_only':True,'external_G0_mass_included':False,'external_tether_supported_stub_included':True,'physical_weighing':'NOT_RUN'})
 F=326;thread_area=math.pi*27.4*3.5*.5*.6;reff=2/3*(12**3-4.2**3)/(12**2-4.2**2)
 path=joint['nominal_force_path'];forbidden=('measurement_shaft','thrust_rear','thrust_front','sensor_pcba')
 strength={'status':'CONDITIONAL_CALCULATIONS_NOT_QUALIFIED','preload_N':F,'preload_path_excludes_axial_locator':not any(any(x in v for x in forbidden) for v in path),'thread_shear_effective_area_mm2':thread_area,'thread_shear_stress_MPa':F/thread_area,'thread_allowable_assumed_MPa':40,'thread_margin_assumed':40*thread_area/F,'thread_60deg_radial_force_N':F*math.tan(math.pi/6),'female_thread_in_one_piece_cup':True,'cup_mounts_carry_torque_not_brake_preload':True,'four_M2_mount_shear_at_low_mu_torque_N_each':(2*.08*F*reff/1000)/(4*math.hypot(.0123,.0071)),'housing_root_hoop_approx_MPa':(F*math.tan(math.pi/6)/(math.pi*28*4))*14/.97,'cap_conservative_four_strip_bending_MPa':6*(F/4)*8.7/(5*4**2),'cap_allowable_assumed_MPa':70,'face_pressure_MPa':F/(math.pi*(12**2-4.2**2)),'two_face_holding_at_mu08_Nm':2*.08*F*reff/1000,'two_face_torque_at_mu22_Nm':2*.22*F*reff/1000,'catalog_spring_mass_g':4*.310,'modeled_spring_mass_g':sum(x['mass_g'] for x in joint['parts'] if x['part_id'].startswith('disc_spring_')),'materials_and_thread_load_share':'Conservative proposed allowables and load-share assumptions; no certified stock/material or thread standard fit qualification','required_followups':['Cartridge clamp preload, cup register fits, axial M2 mounts and matched-bore deformation','Actual cap/plate annular FEA and washer bearing stress','Lining compression/creep and friction coefficient measured in both directions','Positive drive-key bearing/shear/backlash and axial drag while carrying torque','Thread stripping/pullout and cap locking tests at worst tolerance/temperature']}
 tolerances={'status':'PROPOSED_TOLERANCE_BUDGET_SUPPLIER_NOT_QUALIFIED','bearing_span_mm':14,'shaft_diameter_mm':[5.994,6.000],'finished_split_bush_bore_mm':[6.020,6.024],'diametral_clearance_mm':[.020,.030],'geometric_clearance_tilt_deg':math.degrees(math.atan(.03/14)),'coaxial_error_allowance_mm':.010,'clearance_plus_coaxial_tilt_deg':math.degrees(math.atan(.04/14)),'readout_accuracy_claim':False,'axial_endplay_nominal_mm':.05,'paired_shelf_position_tolerance_mm':.005,'each_ground_thrust_thickness_tolerance_mm':.003,'collar_width_tolerance_mm':.003,'axial_endplay_worst_mm':[.031,.069],'loose_generic_machining_endplay_mm':[-.045,.145],'generic_fit_status':'FAIL_BINDING_POSSIBLE','drive_key_nominal_tangential_lost_motion_mm':.008,'drive_key_nominal_lost_motion_deg':math.degrees(.008/3.05),'old_separate_keys_nominal_lost_motion_deg':math.degrees(.032/3.05),'drive_key_status':'INTEGRAL_DRIVE_RIBS_NOMINAL_ONLY_MATCHED_SLOT_TOLERANCE_AND_WEAR_NOT_QUALIFIED'  ,'cap_guide_relief_axial_clearance_mm':.4,'proposed_total_lining_wear_allowance_mm':.6,'wear_adjustment_turns':.6/.75,'min_thread_engagement_mm_over_free_to_worn':3.5,'cap_lock_increment_mm':.75/12,'manufacturing_requirements':['Register cartridge halves on the cup, clamp and line bore as one marked assembly','Ground thrust shims and collar inspection; do not rely on nominal POM print thickness','Inspect thread runout and bore roundness under bolt torque'],'not_run':['Thermal expansion of actual material batches','Friction lining wear/load-height curve','Sensor gap variation under preload and reversing side load']}
 sensor_A=41*.015;MCU_A=6*.18;CAN_A=6*.015;buffer_A=45*.001
 load_W=3.3*(sensor_A+MCU_A+CAN_A+buffer_A);rows=[]
 for awg,ohms_m in [(24,.0842),(26,.1339),(28,.213)]:
  R=2*ohms_m+.06;P=load_W/.85;Vin=4.75;disc=Vin*Vin-4*P*R
  V=(Vin+math.sqrt(disc))/2 if disc>=0 else None;I=P/V if V else None
  rows.append({'awg':awg,'loop_length_m':2,'contact_allowance_ohm':.06,'input_power_W':P,'load_voltage_V':V,'current_A':I,'wire_loss_W':I*I*R if I else None})
 save(verify/'power_budget.json',{'status':'ALLOCATION_MODEL_NOT_POWER_QUALIFICATION','supply_baseline_V':5,'legacy_12V_allowed':False,'internal_MCU_count':6,'internal_acquisition_PCBs':8,'sensor_count':41,'LVC125_packages':45,'current_allocations_A_3V3':{'sensors':sensor_A,'MCUs':MCU_A,'CAN':CAN_A,'buffers':buffer_A},'total_3V3_load_W':load_W,'tether_cases':rows,'four_port_remote_branch_A':4*(.015+.001),'interboard_power_pins':2,'interboard_ground_pins':5,'physical_tested':False,'not_run':['Regulator startup/peak/short-circuit, protected six branches and TVS clamp verification','Mated contact ratings, heating and flex life','LVC125 power-off backfeed/tri-state behaviour','USB backfeed and G0 isolation','Actual cable length/resistance and radio/MCU peak current']})
 save(verify/'mechanics_analysis.json',{'strength':strength,'tolerances':tolerances,'preload_path':path,'independent_axial_locator':joint['shaft_axial_locator_path'],'load_path_note':'Topological nominal CAD paths; constraints alone do not establish stiffness or load capacity. Sliding key parasitic forces remain unmeasured.','physical_tested':False,'V1':'PARTIAL_NOMINAL_PATHS_PROVEN_CONDITIONAL_STRENGTH','V3':'NOT_RUN_PHYSICAL'})
if __name__=='__main__':main()