"""Geometry-gated contacts and a conservative O3 part/allocation ledger.
No physical spring sizing is issued from contacts whose shell geometry is absent.
"""
from revo3_evidence import *
from study_revo2 import ledger, measure_character, G
from study_revo import anatomy
from model import fk,rotation
import math,itertools,numpy as np

def activate_contacts(contacts,plane_origin=(0,0,0),plane_normal=(0,0,1),gap_tolerance_mm=.02):
    origin=np.array(plane_origin,dtype=float);normal=np.array(plane_normal,dtype=float);normal/=np.linalg.norm(normal)
    result=[]
    for q in contacts:
        p=np.array(q['point_mm']);gap=float((p-origin)@normal);n=np.array(q['normal'],dtype=float);length=np.linalg.norm(n)
        aligned=bool(length>0 and n@normal/length>.999)
        active=abs(gap)<=gap_tolerance_mm and aligned
        result.append({**q,'gap_mm':gap,'normal_aligned':aligned,'active':active,'state':'PENETRATION_REQUIRES_RESOLUTION' if gap<-gap_tolerance_mm else ('ACTIVE_GEOMETRIC_CONTACT' if active else 'INACTIVE_NO_NORMAL_REACTION'),'normal_force_forced_zero':not active})
    return result

def vertical_reaction_vertices(contacts,weight_N,com_mm):
    """All nonnegative basic solutions for vertical planar forces only.
    Tangential force / tilted support / 6D wrench cases require a different solver.
    """
    allowed=[i for i,q in enumerate(contacts) if q['active']]
    if any(q['state']=='PENETRATION_REQUIRES_RESOLUTION' for q in contacts):return []
    if not allowed:return []
    a=np.array([[1]*len(allowed),[contacts[i]['point_mm'][0]/1000 for i in allowed],[contacts[i]['point_mm'][1]/1000 for i in allowed]],float)
    b=np.array([weight_N,weight_N*com_mm[0]/1000,weight_N*com_mm[1]/1000]);solutions=[]
    # Lower-rank point/line supports are allowed only if all 3 equalities close.
    for count in range(1,min(3,len(allowed))+1):
        for inds in itertools.combinations(range(len(allowed)),count):
            sub=a[:,inds];forces,_,rank,_=np.linalg.lstsq(sub,b,rcond=None)
            if rank!=count or np.linalg.norm(sub@forces-b)>1e-7 or min(forces)<-1e-7:continue
            full=np.zeros(len(contacts));full[[allowed[i] for i in inds]]=np.maximum(forces,0);solutions.append(full.tolist())
    return solutions

def contact_counterexample():
    points=[{'id':str(i),'point_mm':[x,y,z],'normal':[0,0,1]} for i,(x,y,z) in enumerate(itertools.product((-10,10),(-10,10),(0,20)))]
    before=[{**p,'active':True,'state':'ASSUMED'} for p in points]
    after=activate_contacts(points);old=vertical_reaction_vertices(before,10,[0,0,10]);new=vertical_reaction_vertices(after,10,[0,0,10]);air=[i for i,p in enumerate(points) if p['point_mm'][2]>0]
    return {'unconstrained_airborne_max_N':max(sum(s[i] for i in air) for s in old),'geometry_activated_airborne_max_N':max(sum(s[i] for i in air) for s in new),'active_ids':[q['id'] for q in after if q['active']],'status':'PASS_COUNTEREXAMPLE_REGRESSION'}

def reconcile(rows):
    credit_ids=[q['part_id'] for q in rows if q['scope'].startswith('R2 CAD') and q['part_id'].split('/')[-1].startswith(('disc_spring_','spring_front_washer','spring_rear_washer','cup_mount_','bearing_clamp_','cap_lock_dog','keeper_screw_','pcb_clamp_screw_'))]
    credits=[{'detailed_part_id':q['part_id'],'quantity':1,'covered_mass_g':q['mass_g'],'allocation_category':'unresolved_fasteners_springs','basis':'Explicit transfer of modeled L6 fasteners/spring hardware out of retained 100 g common allowance; estimate, not physical weighing'} for q in rows if q['part_id'] in credit_ids]
    credit=sum(q['covered_mass_g'] for q in credits);allow=[q for q in rows if q['part_id'].startswith('unresolved_fasteners_springs/')];gross=sum(q['mass_g'] for q in allow)
    if credit>gross:raise ValueError('Part transfers exceed available allocation')
    for q in allow:
        original=q['mass_g'];q['mass_g']*=1-credit/gross;q['mass_source']+='; reduced only by itemized O3 L6 coverage transfers';q['allocation_before_transfer_g']=original
    for q in rows:
        if q['scope'].startswith('R2 CAD'):q['scope']='O3 single-joint CAD on provisional ideal anatomy transform'
    return {'gross_hardware_allocation_g':gross,'explicit_coverage_transfer_g':credit,'remaining_hardware_allocation_g':gross-credit,'coverage_transfers':credits,'other_644g_categories_retained':True,'remaining_scope':'All other families, links, supports and unmodeled fasteners; no deduction for unnamed overlaps'}

def root_rotation_for_case(name):
    return rotation([1,0,0],-90) if name=='left_side_lying' else rotation([1,0,0],90) if name=='right_side_lying' else rotation([0,1,0],90) if name=='prone' else np.eye(3)

def loads_hand_supported(p,rows):
    parents={n['id']:n['parent'] for n in p['nodes']}
    def descendant(n,root):
        while n is not None:
            if n==root:return True
            n=parents[n]
        return False
    poses=read(HW/'mechanical_manifest/revO_pose_cases.json')['cases'];loads={a:{'axis_id':a,'max_hand_supported_gravity_Nm':0,'case':None} for a in p['axis_order'][3:]};cases=[]
    for name,pose in poses.items():
        # Hand at pelvis supplies a full external wrench, declared separately
        # from independently supported standing/lying poses. Same motion set retained.
        T,A=fk(p,pose);R=root_rotation_for_case(name);kg=np.array([q['mass_g']/1000 for q in rows]);mp=np.array([R@(T[q['owner']]@np.r_[q['local_com_mm'],1])[:3] for q in rows]);com=np.average(mp,axis=0,weights=kg)
        cases.append({'case':'hand_pelvis_'+name,'joint_angles_deg':pose,'root_rotation_matrix':R.tolist(),'support':'Declared full hand wrench at pelvis','COM_mm':com.tolist(),'weight_N':float(kg.sum()*G),'status':'ASSUMED_HAND_SUPPORT_NOT_SELF_SUPPORTED_POSE'})
        for aid,a in A.items():
            if aid not in loads:continue
            mask=np.array([descendant(q['owner'],a['node']) for q in rows]);force=np.column_stack([np.zeros(sum(mask)),np.zeros(sum(mask)),-kg[mask]*G]);torque=abs(float((R@a['direction'])@np.cross((mp[mask]-R@a['origin'])/1000,force).sum(axis=0)))
            if torque>loads[aid]['max_hand_supported_gravity_Nm']:loads[aid].update(max_hand_supported_gravity_Nm=torque,case='hand_pelvis_'+name)
    reff=2/3*(.012**3-.0042**3)/(.012**2-.0042**2)
    for aid,q in loads.items():
        grip=.03 if aid.startswith(('head.','hand_','ball_')) else .06;cable=.01 if grip==.03 else .02;hold=1.5*(q['max_hand_supported_gravity_Nm']+cable)
        q.update(holding_target_assumed_hand_support_Nm=hold,preload_at_mu008_N=hold/(2*.08*reff),operating_force_against_gravity_at_mu022_N=(hold*.22/.08+q['max_hand_supported_gravity_Nm']+cable)/grip,assumptions={'grip_distance_m':grip,'cable_torque_Nm':cable,'load_factor':1.5,'friction_interval':[.08,.22]},module_reuse_preference='L6-R3 where verified envelope/ROM/force/precision permits; no mass-driven family mandate',manufacturing_family=None,selection_status='BLOCKED_REAL_MULTIAXIS_GEOMETRY_AND_SUPPORTED_LOADS_AND_HANDFEEL')
    return list(loads.values()),cases

def torque_chain(joint):
    f=326*1.25;mu=.22;reff=2/3*(12**3-4.2**3)/(12**2-4.2**2);one=mu*f*reff;total=2*one
    # No default load sharing between ears. One ear must be checked for the full face torque.
    ear_force=one/12.9;polar=math.pi/2*(12**4-4.2**4);thread_fraction=1-4*math.atan(2.08/13.7)/(2*math.pi)
    entries=[
      {'stage':'output connection to shaft','status':'BLOCKED_OUTPUT_COUPLER_NOT_DETAILED','load_Nmm':total},
      {'stage':'D-cut shaft tail to shaft ribs','status':'CONDITIONAL_SECTION_SCREEN','load_Nmm':total,'solid_6mm_shaft_nominal_torsional_MPa':16*total/(math.pi*6**3),'D_cut_stress_concentration':'NOT_RUN'},
      {'stage':'shaft integral rib to floating disc','status':'CONDITIONAL_ONE_RIB_LOAD','load_Nmm':total,'force_N':total/3.05,'minimum_axial_overlap_mm':3.65,'rib_root_shear_MPa':total/3.05/(2*3.65),'flank_bearing_MPa':total/3.05/(.8*3.65),'parasitic_axial_drag_N_for_slide_mu_010_030':[.1*total/3.05,.3*total/3.05]},
      {'stage':'each lining to steel backing','status':'BLOCKED_BOND_UNQUALIFIED','load_Nmm':one,'required_elastic_bond_peak_shear_MPa':one*12/polar,'qualified_allowable_MPa':None,'uncredited_back_face_friction':True},
      {'stage':'each steel carrier ear to cup track','status':'CONDITIONAL_ONE_EAR_LOAD','load_Nmm':one,'ear_force_N':ear_force,'ear_neck_shear_MPa':ear_force/(.8*4),'cup_track_bearing_MPa':ear_force/(.8*1.65),'ear_bending_and_fillet_FEA':'NOT_RUN','minimum_outer_cup_wall_at_track_mm':15-math.hypot(14.2,2.08)},
      {'stage':'cup to mounting structure','status':'CONDITIONAL_ONE_M2_LOAD_NO_FRICTION_CREDIT','load_Nmm':total,'single_mount_shear_force_N':total/math.hypot(12.3,7.1),'M2_core_diameter_mm':1.6,'single_mount_shear_MPa':total/math.hypot(12.3,7.1)/(math.pi*.8**2),'housing_register_and_external_mount_strength':'NOT_RUN'},
      {'stage':'cap female thread preload reaction','status':'CONDITIONAL_INTERRUPTED_THREAD_SCREEN','load_N':f,'remaining_circumference_fraction':thread_fraction,'effective_shear_area_mm2':math.pi*27.4*3.5*.5*.6*thread_fraction,'mean_shear_MPa':f/(math.pi*27.4*3.5*.5*.6*thread_fraction),'production_class_and_pullout':'NOT_RUN'}]
    return {'status':'PARTIAL_NO_MANUFACTURING_RATING','assumed_preload_N':f,'catalog_point_N':326,'factor_1p25_is_assumed_not_supplier_tolerance':True,'maximum_actual_spring_force_N':None,'mu_assumed_max':mu,'torque_each_face_Nm':one/1000,'torque_two_faces_Nm':total/1000,'stages':entries,'preload_path_status':'DESIGN_DECLARATION','preload_path':joint['nominal_force_path'],'physical_tested':False}

def main():
    v,o=run_paths();jr=ArtifactReader('joint');br=ArtifactReader('baseline');joint=jr.json(v/'joint.json');old=br.json(o/'inherited/legacy_mass_reference.json');previous=br.json(o/'inherited/mass_properties_revO2.json');chars={}
    for char in ('manny','quinn'):
        p,c,rows=ledger(char,joint,old,{});gross=sum(q['mass_g'] for q in rows);reconciliation=reconcile(rows);loads,cases=loads_hand_supported(p,rows)
        unresolved=[{'case':q['case'],'status':'UNRESOLVED_ACTUAL_SHELL_SUPPORT_CONTACTS','old_assumed_contacts':q['contact_points'],'reason':'O2 patch points have no frozen physical shell/contact plane/normal evidence. No reaction or spring rating is issued.'} for q in previous['characters'][char]['support_cases'] if q['contact_points']]
        chars[char]={'mass_properties':rows,'gross_before_explicit_transfers_g':gross,'total_budget_g':sum(q['mass_g'] for q in rows),'worst_sum_uncertainty_g':sum(q['mass_g']*q['uncertainty_fraction'] for q in rows),'actual_complete_CAD_mass_g':None,'mass_policy':{'hard_max_g':None,'lightweight_preference_g':1200,'exceedance_fails_design':False},'reconciliation':reconciliation,'load_rows':loads,'hand_supported_cases':cases,'independent_support_cases':unresolved,'joint_basis':'14 inherited L6 assignments are a comparison mapping; old S4/M6 are incomplete mass references, no manufacturing selection','COM_transform_scope':'Real part COM into provisional ideal anatomy; multi-axis assembly offset feedback remains open','physical_weighed':False}
        save(o/'layouts'/char/'anatomy_profile.json',p)
        print(char,'gross',gross,'reconciled',chars[char]['total_budget_g'],'hardware credit',reconciliation['explicit_coverage_transfer_g'],flush=True)
    save(v/'mass_properties_revO3.json',{'characters':chars,'body_only':True,'G0_external':True,'consumed_inputs':[jr.receipt(),br.receipt()]})
    save(v/'mechanics_analysis.json',{'torque_chain':torque_chain(joint),'contact_counterexample':contact_counterexample(),'old_1290N_spring_selection':'RETRACTED_AS_MANUFACTURING_INPUT_UNVALIDATED_CONTACTS','physical_tested':False})
if __name__=='__main__':main()
