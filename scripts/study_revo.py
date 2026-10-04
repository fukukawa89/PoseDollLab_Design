"""Reproducible anatomical size study + fixed component constraints.
These profiles are ANATOMY references, not final mechanical/UE device profiles.
"""
from pathlib import Path
import sys, copy, math, csv, io
import numpy as np
from revo_common import *
sys.path.insert(0,str(HW/'cad'))
from model import fk

def anatomy(character,height):
    source=HW/f'mechanical_manifest/physical_{character}_44_revG_humanform_trial.json'
    p=copy.deepcopy(read(source));old=p['design_reference']['mesh_N_pose_surface_height_mm'];factor=height/old
    for node in p['nodes']:
        for key in ('parent_to_axis','axis_to_child'):
            node[key]['translation_m']=[v*factor for v in node[key]['translation_m']]
    p.update(profile_id=f'anatomy_{character}_revO_{height}mm',status='ANATOMY_ONLY_NOT_ASSEMBLABLE_NOT_DEVICE_CALIBRATION')
    p['notes_zh']=['仅缩放解剖骨长和角色参考，不缩放任何采购件、轴径、磁铁、接头或公差。','多轴关节实际偏置未冻结；不得将此文件作为已装配、已校准 UE 配置。']
    p['design_reference'].update(scale=.5*factor,mesh_N_pose_surface_height_mm=height,source_half_scale_height_mm=old,source_sha256=sha(source))
    p['design_reference']['neutral_floor_shift_mm']=[v*factor for v in p['design_reference']['neutral_floor_shift_mm']]
    return p

def family(aid):
    if aid.startswith(('hand_','ball_','head.','forearm_')):return 'S4'
    if aid.startswith(('waist.','chest.','thigh_','calf_')):return 'L6'
    return 'M6'

def network_budget():
    n=read(HW/'mechanical_manifest/network_revO.json');counts=[len(x['ports']) for x in n['nodes']]
    frames=sum(math.ceil(x/2) for x in counts)+6+1
    # Discrete-event CAN arbitration model: each regional node finishes its SPI
    # batch, then releases data frames. One pending frame per node, END after pairs.
    per_axis_us=700 # assumed bounded reading time; 640 us wire + ~60 us explicit delays, excludes unknown SDK overhead
    duration_us=135/500000*1e6
    ready={i+1:counts[i]*per_axis_us+duration_us for i in range(6)}
    pending={i+1:[0x200+(i+1)*16+g for g in range(math.ceil(counts[i]/2))]+[0x180+i+1] for i in range(6)}
    now=duration_us;trace=[];ends={}
    while any(pending.values()):
        eligible=[node for node,packets in pending.items() if packets and ready[node]<=now]
        if not eligible:
            now=min(ready[node] for node,packets in pending.items() if packets);continue
        node=min(eligible,key=lambda x:pending[x][0]);ident=pending[node].pop(0);start=now;now+=duration_us;ready[node]=now
        trace.append(dict(node=node,id=hex(ident),start_us=round(start),end_us=round(now)))
        if 0x181<=ident<=0x186:ends[str(node)]=round(now)
    save(VERIFY/'can_budget.json',dict(status='ANALYTICAL_ONLY_HARDWARE_TIMING_NOT_RUN',frames_per_cohort=frames,
         utilization_data_end_sync=frames*135*60/500000,deadline_us=14000,node_window_us=8000,
         optimistic_nonoverlap_upper_sum_us=max(counts)*per_axis_us+frames*duration_us,
         assumed_axis_read_us=per_axis_us,ideal_arbitration_completion_us=round(now),trace=trace,node_end_us=ends,
         excluded=['SDK scheduling and driver overhead','TX callback wake latency','100 ms epoch BOOT/ACK bursts','250 ms BOOT traffic','CAN errors/retries and transceiver propagation'],
         timing_verified=False,explanation='A nominal schedule is not a measured worst-case bound. Do not widen the 8/14 ms gates.'))
    # Engineering current allocations, not measured consumption or part guarantees.
    sensors=41*.015;mcus=6*.18;can=6*.015;buffers=41*.001
    load_w=3.3*(sensors+mcus+can+buffers);eta=.85
    options=[]
    for voltage in (5,12):
        for awg,res in [(24,.0842),(26,.1339),(28,.213)]:
            loop=2*res+.06
            # Constant power worst case at -5% supply: solve Vload=Vin - P/Vload*R.
            vin=voltage*.95;power=load_w/eta;disc=vin*vin-4*power*loop
            vload=(vin+math.sqrt(disc))/2 if disc>=0 else None
            current=power/vload if vload else None
            options.append(dict(supply_V=voltage,awg=awg,length_m=1,resistance_loop_ohm=loop,
                                connector_contact_allowance_ohm=.06,input_power_W=power,
                                current_A=current,load_voltage_at_minus5pct_V=vload,cable_loss_W=current**2*loop if current else None))
    save(VERIFY/'power_budget.json',dict(status='ALLOCATION_MODEL_NOT_ELECTRICAL_QUALIFICATION',node_3V3_load_budget_W=load_w,
         allocations_A={'six_MCU':mcus,'41_sensors':sensors,'six_CAN':can,'41_buffers':buffers},buck_efficiency_assumed=eta,options=options,
         provisional_baseline='5V / 24 AWG power pair; CAN pair separate; no generic USB connector on tether',
         NOT_RUN=['Peak/inrush/short-circuit and heat','Six internal protected branches','TVS clamp against regulator/TCAN limits','Connector temperature/bending life','USB backfeed test','Internal cable resistance'],
         legacy_12V_connection_allowed=False))

def main():
    cfg=read(HW/'mechanical_manifest/desktop_revO.json');joints=read(VERIFY/'joint_study.json')
    boards={p:read(HW/f'electronics/revO/node_{p}port/layout.json') for p in (3,6,7,9)}
    poses=read(HW/'mechanical_manifest/keyposes_degrees.json')
    additions={
      'hands_low_behind':{'upperarm_l.flex':-30,'upperarm_r.flex':-30,'elbow_l.flex':55,'elbow_r.flex':55},
      'one_hand_up_back':{'upperarm_l.flex':-25,'upperarm_l.twist':65,'elbow_l.flex':130},
      'touch_back_head':{'upperarm_l.flex':150,'elbow_l.flex':115,'upperarm_l.twist':-35},
      'kneeling':{'thigh_l.flex':30,'thigh_r.flex':30,'calf_l.flex':130,'calf_r.flex':130},
      'trunk_bend_twist':{'waist.pitch':35,'chest.pitch':25,'waist.yaw':30,'chest.yaw':20},
      'shoulder_extend_internal':{'upperarm_l.flex':-35,'upperarm_l.twist':60},
      'legs_together':{},'legs_crossed':{'thigh_l.abduct':-10,'thigh_r.abduct':-10,'thigh_l.flex':15},
      'left_side_lying':{},'right_side_lying':{},'prone':{}}
    poses.update(additions)
    save(HW/'mechanical_manifest/revO_pose_cases.json',{'cases':poses,'scope':'Targets only. Side-lying/prone require world support/contact/tether model; empty angle dict does NOT prove lying clearance.','path_sampling_initial_max_step_deg':5,'near_contact_required_step_deg':1,'continuous_proof':False})
    rows=[];viewdata={}
    for character in cfg['anatomy']['characters']:
        for height in cfg['anatomy']['study_heights_mm']:
            p=anatomy(character,height);T,A=fk(p,{})
            key=f'{character}_{height}';folder=OUT/'layouts'/key;folder.mkdir(parents=True,exist_ok=True)
            save(folder/'anatomy_profile.json',p)
            measure={}
            for side in ('l','r'):
                for label,a,b in [('upperarm','upperarm','elbow'),('forearm','elbow','hand'),('thigh','thigh','calf'),('shin','calf','foot')]:
                    measure[f'{label}_{side}_mm']=float(np.linalg.norm(T[f'{a}_{side}'][:3,3]-T[f'{b}_{side}'][:3,3]))
            measure['shoulder_span_mm']=float(np.linalg.norm(T['upperarm_l'][:3,3]-T['upperarm_r'][:3,3]))
            measure['hip_span_mm']=float(np.linalg.norm(T['thigh_l'][:3,3]-T['thigh_r'][:3,3]))
            # Axial placement lower-bound study with 18+14 mm shoulder/elbow ends
            # and 12 mm service travel. Does not certify lateral fit.
            constraints=[]
            for side in ('l','r'):
                for board,segment,node in [(9,'upperarm','N3' if side=='l' else 'N4'),(7,'thigh','N5' if side=='l' else 'N6')]:
                    available=measure[f'{segment}_{side}_mm']-18-14
                    need=boards[board]['board_mm'][1]
                    constraints.append(dict(check=f'{node}_{segment}_{side}_axial_service',status='FAIL' if need>available else 'PASS_THIS_1D_CHECK_ONLY',
                        segment_length_mm=measure[f'{segment}_{side}_mm'],joint_end_reserve_mm=32,available_mm=available,required_mm=need,
                        deficit_mm=max(0,need-available),part=f'node_{board}port/{boards[board]["name"]}',process='Same rigid segment; 12 mm unplug travel is normal to PCB, evaluated separately, NOT added along the limb',
                        not_proven=['Cross-section fit','Mating plug locks','Cable path','Joint sweep']))
            # Each co-centred multi-axis anatomy group requires a new nested mechanism.
            # Never silently turn these ideal coincident axes into overlapping "assembled" solids.
            unresolved=['Shoulder/hip/wrist concentric axes need noninterfering nested carriers',
                        'N3/N4 may need split controller/fanout or relocation within a rigid torso segment',
                        'N1/N2 rigid-segment volume and 6-branch power distribution not finalized',
                        'Final mating plug STEP, cable bend and maintenance paths',
                        'Final head/foot/cover/fastener geometry and measured total mass']
            masses=[]
            for n in p['nodes']:
                aid=n.get('axis_id')
                if aid and not aid.startswith('pelvis.'):
                    masses.append(dict(owner=n['id'],mass_g=joints[family(aid)]['modeled_mass_g_excluding_spring_fasteners_plug'],source='Modeled joint solid subset; spring/fasteners/plug excluded'))
            # Named engineering allocations included in budget, never mass measurements.
            allocations={'springs_and_fasteners':100,'internal_harness_and_tether_supported_stub':90,'six_node_PCBAs':120,'frames_and_links':150,'printed_head_feet_guards':130,'power_distribution_protection_and_pelvis_connector':35}
            joint_mass=sum(q['mass_g'] for q in masses)
            budget={'joint_modeled_subset_g':joint_mass,'unmodeled_allocations_g':allocations,'total_allocation_g':joint_mass+sum(allocations.values()),'target_g':1200,'status':'DESIGN_BUDGET_NOT_FULL_CAD_MASS'}
            # Load estimate includes allocations placed explicitly; no false full-body load pass.
            for owner,g in [('pelvis',90),('chest',125),('head',40),('upperarm_l',55),('upperarm_r',55),('thigh_l',65),('thigh_r',65),('foot_l',40),('foot_r',40)]:
                masses.append(dict(owner=owner,mass_g=g,source='Allocated non-joint mass point; not real CAD COM'))
            # Correct remaining allocation to pelvis so every allocated gram appears once.
            missing=sum(allocations.values())-sum(m['mass_g'] for m in masses if m['source'].startswith('Allocated'))
            if missing:masses.append(dict(owner='pelvis',mass_g=missing,source='Allocated balance'))
            parents={n['id']:n['parent'] for n in p['nodes']}
            def desc(child,ancestor):
                while child is not None:
                    if child==ancestor:return True
                    child=parents[child]
                return False
            loadrows={aid:{'axis_id':aid,'max_gravity_Nm':0,'pose':None,'family':family(aid)} for aid in p['axis_order'][3:]}
            pose_limit_fail=[]
            limits={a['id']:np.degrees(a['limits_rad']) for a in p['axes']}
            for pname,angles in poses.items():
                for aid,v in angles.items():
                    if not limits[aid][0]<=v<=limits[aid][1]:pose_limit_fail.append(dict(pose=pname,axis=aid,angle_deg=v,limits_deg=limits[aid].tolist()))
                PT,PA=fk(p,angles)
                for aid,l in loadrows.items():
                    a=PA[aid];torque=np.zeros(3)
                    for m in masses:
                        if desc(m['owner'],a['node']):
                            torque+=np.cross((PT[m['owner']][:3,3]-a['origin'])/1000,[0,0,-m['mass_g']/1000*9.80665])
                    tau=abs(float(np.dot(a['direction'],torque)))
                    if tau>l['max_gravity_Nm']:l.update(max_gravity_Nm=tau,pose=pname)
            for aid,l in loadrows.items():
                grip=.03 if family(aid)=='S4' else .06
                cable=.01 if family(aid)=='S4' else .02 # sensitivity assumption, unmeasured
                l.update(cable_torque_assumed_Nm=cable,required_hold_with_1p5_margin_Nm=1.5*(l['max_gravity_Nm']+cable),grip_distance_assumed_m=grip)
                l['breakaway_force_if_sized_to_low_mu_N']=l['required_hold_with_1p5_margin_Nm']*(.22/.08)/grip
                l['required_preload_at_low_mu_N']=l['required_hold_with_1p5_margin_Nm']/(.08*joints[l['family']]['effective_friction_radius_m'])
            worst=max(loadrows.values(),key=lambda x:x['required_hold_with_1p5_margin_Nm'])
            row=dict(character=character,reference_height_mm=height,status='LAYOUT_BLOCKED_CURRENT_COMPONENT_ARRANGEMENT',
                     complete_body_height_mm=None,complete_body_mass_g=None,measurements=measure,constraints=constraints,
                     mass_budget=budget,load_scope='Analytical allocation + joint solid subset on ideal anatomy. Not final CAD COM. Cable torque assumed. No load pass.',
                     worst_budget_axis=worst,loads=list(loadrows.values()),target_pose_limit_failures=pose_limit_fail,unresolved=unresolved,
                     motion_path_check='NOT_RUN',magnetic_interference_test='NOT_RUN',physical_tested=False,manufacturing_released=False)
            save(folder/'study.json',row);rows.append(row)
            # Neutral reference skeleton and board positions are visibly labelled layout proposals.
            nodes={n['id']:T[n['id']][:3,3].tolist() for n in p['nodes']}
            links=[{'a':nodes[n['parent']],'b':nodes[n['id']],'name':n['id']} for n in p['nodes'] if n['parent'] and np.linalg.norm(T[n['parent']][:3,3]-T[n['id']][:3,3])>1]
            nodeposes={}
            for name,owner,count in [('N1','pelvis',3),('N2','chest',6),('N3','upperarm_l',9),('N4','upperarm_r',9),('N5','thigh_l',7),('N6','thigh_r',7)]:
                xyz=T[owner][:3,3].copy();xyz[0]+=5;xyz[2]-=boards[count]['board_mm'][1]/2+18
                nodeposes[name]={'center':xyz.tolist(),'ports':count,'dims':[11.2,40,boards[count]['board_mm'][1]],'status':'POSITION_PROPOSAL_NOT_ASSEMBLED','owner':owner}
            viewdata[key]={'nodes':nodes,'links':links,'axes':[{'id':aid,'position':a['origin'].tolist(),'direction':a['direction'].tolist(),'family':family(aid)} for aid,a in A.items() if not aid.startswith('pelvis.')],'boards':nodeposes,'study':row}
            save(folder/'layout_scene.json',viewdata[key])
            print(key,'N3 board/service shortfall',round(constraints[0]['deficit_mm'],2),'mm; budget',round(budget['total_allocation_g'],1),'g',flush=True)
    save(OUT/'layout_data.json',viewdata)
    save(VERIFY/'size_tradeoff.json',{'candidates':rows,'selected_manufacturable_height_mm':None,'detailed_design_anchor_mm':480,
                                   'selection_reason':'No candidate passes full assembly, motions, power and service gates. Failure is of this component arrangement, NOT proof of an absolute size minimum.',
                                   'larger_candidates_scope':'520/550 are comparison-only; no default promotion to a bigger body.'})
    network_budget()

if __name__=='__main__':main()
