"""Positive retention fault cases, preload fit budgets and ideal observability.

These are calculations on the saved solids. They do not turn the S1 physical
test assumption into test data, and do not authorize manufacturing.
"""
from validate import *


def retention(parts,ss):
    byname={p['name']:(p,s) for p,s in zip(parts,ss)}
    loads={r['axis']:r for r in load(OUT/'verification/preload_retention_loads.json')['rows']}
    rows=[];print_by_frame={}
    for p,s in zip(parts,ss):
        if p['role'] in ['structure','rotor','shell']:print_by_frame.setdefault(p['frame'],[]).append(moved(s,F0[p['frame']]))
    print_by_frame={fr:union(shapes) for fr,shapes in print_by_frame.items()}
    for j in load(OUT/'profiles/joint_interfaces.json'):
        pre=j['id'];h2='pressure_web_width_mm' in j;axis=np.array(j['axis_world']);r=loads[j['axis_id']]
        fixed_names=[pre+'_pressure_-1',pre+'_pressure_1'] if h2 else [pre+'_compression_cartridge']
        rotor_names=[pre+'_rotor_cap_-1',pre+'_rotor_cap_1'] if h2 else [pre+'_rear_thrust_cap',pre+'_keyed_output_cap']
        fixed=union(moved(byname[n][1],F0[byname[n][0]['frame']]) for n in fixed_names)
        moving=union(moved(byname[n][1],F0[byname[n][0]['frame']]) for n in rotor_names)
        # Deliberately omit friction pads, bearing seats, adhesive and the locknut
        # from the stopping geometry. Only positively keyed metal caps remain.
        directions=[]
        for sg in [-1,1]:
            stopped=None
            for travel in np.arange(.2,6.01,.2):
                overlap=(moving.translate(axis*sg*travel)^fixed).volume()
                if overlap>.02:
                    stopped=dict(direction=sg,first_sampled_stop_mm=float(travel),preceding_clear_sample_mm=float(travel-.2),metal_intersection_mm3=float(overlap));break
            directions.append(stopped)
        pull=r['axial_handling_pull_N'];d=j['bearing_diameter_mm'];pin_d=3 if d==6 else 2
        capkey=(4.4 if d==6 else 3.3) if h2 else (5 if d==6 else 3.5)
        engagement=(j['cap_thickness_mm']-.1)
        cap_key_stress=(r['hold_target_Nm']*1000/2)/(3*capkey*engagement*(capkey*math.sqrt(3)/2))
        if h2:
            shoulder_area=3*math.sqrt(3)/2*(j['output_hex_radius_mm']**2-capkey**2)
            shoulder_stress=r['required_clamp_N']/shoulder_area
            closure='Two M3 metal tie screws, steel channel plates, steel face washers, stepped hex core and two keyed caps; FDM and bearing end faces bypassed.'
        else:
            shoulder_area=None;shoulder_stress=0
            closure='Headed shaft with integral rear hex, rear cap, steel face washer, hex compression cartridge, steel washer, cross-pinned output cap, washer and metal locknut.'
        thin=j['axis_id'] in ['lumbar_yaw','l_hip_flex','r_hip_flex'];thread=j['thread_diameter_mm'];pitch=j['thread_pitch_mm'];height=(3.2 if thread==6 else 2.2) if thin else (4 if h2 else (5 if thread==4 else 6))
        pitch_d=thread-.649519*pitch;thread_area=.5*math.pi*pitch_d*max(height-.3,0);strip_capacity=thread_area*(450/math.sqrt(3))
        screwload=r['required_clamp_N']/(2 if h2 else 1)
        # Machined sleeve length ±0.05, bearing width upper deviation +0.03,
        # end-face flatness 0.05; H2 includes the calculated plate deflection.
        relief=j['bearing_axial_relief_mm'];min_relief=relief-.05-.03-.05-r.get('plate_deflection_mm',0)
        bond_area=math.pi*j['bearing_outer_mm']*4;bond_factor=(2*bond_area/pull) if not h2 else None
        criteria=dict(positive_stop_both_directions=all(x is not None for x in directions),cap_key=cap_key_stress<=115,metal_shoulder=shoulder_stress<=115,nut_strip=strip_capacity/max(screwload,1e-9)>=2,bearing_end_relief=min_relief>=.2)
        fixed_capture=None
        if not h2:
            engagement=j['fixed_capture_printed_engagement_per_end_mm'];bearing_stress=pull/(2*1.5*engagement)
            fixed_capture=dict(pin_diameter_mm=1.5,printed_engagement_per_end_mm=engagement,axial_pull_N=pull,printed_pin_bearing_stress_MPa=bearing_stress,pin_shear_factor=1000/pull,nominal_axial_play_mm=.1,hex_torque_bypass_slot=True)
            criteria['fixed_socket_capture']=bearing_stress<=8 and 1000/pull>=3
        else:
            engagement=j['hub_capture_engagement_per_end_mm'];pin=j['hub_capture_pin_diameter_mm'];bearing_stress=pull/(2*pin*engagement)
            fixed_capture=dict(component='rotating printed hub',pin_diameter_mm=pin,printed_engagement_per_end_mm=engagement,axial_pull_N=pull,printed_pin_bearing_stress_MPa=bearing_stress,nominal_axial_play_mm=.1,hex_torque_bypass_slot=True)
            criteria['printed_hub_capture']=bearing_stress<=8
        criteria['printed_preload_bypass']=j['printed_preload_face_recess_mm']-.15-.05-.05-.05>=.049
        probe=[]
        face_names=[n for n in byname if n.startswith(pre+('_friction_' if h2 else '_face_pad_'))]
        if h2:face_names+=rotor_names
        for name in face_names:
            p,s=byname[name];world=moved(s,F0[p['frame']]);fixed_frame=byname[fixed_names[0]][0]['frame'];frames_to_test=[j['axis_id']] if name in rotor_names and h2 else list({fixed_frame,j['axis_id']})
            for fr in frames_to_test:
                if fr not in print_by_frame:continue
                for sg in [-1,1]:probe.append(dict(face=name,printed_frame=fr,axial_displacement_mm=.30*sg,intersection_mm3=(world.translate(axis*.30*sg)^print_by_frame[fr]).volume()))
        criteria['actual_printed_face_clearance']=max(x['intersection_mm3'] for x in probe)<1e-5
        if not h2:criteria['bearing_bond_axial']=bond_factor>=3
        rows.append(dict(axis=j['axis_id'],interface=pre,status='PASS_CONDITIONAL' if all(criteria.values()) else 'FAIL',criteria=criteria,closure_path=closure,fixed_socket_capture=fixed_capture,actual_printed_face_probes=probe,printed_face_nominal_recess_mm=j['printed_preload_face_recess_mm'],failure_scenario='Zero brake friction/preload; pads, locknut and bearing/adhesive stops ignored. Transverse torque pin and keyed metal caps remain installed.',fixed_stop_parts=fixed_names,moving_stop_parts=rotor_names,stops=directions,axial_pull_N=pull,cap_key_stress_MPa=cap_key_stress,metal_shoulder_area_mm2=shoulder_area,metal_shoulder_stress_MPa=shoulder_stress,thread_engagement_height_mm=height,thread_strip_factor=strip_capacity/max(screwload,1e-9),nominal_bearing_axial_relief_mm=relief,worst_budgeted_bearing_relief_mm=min_relief,bearing_bond_factor=bond_factor,bond_allowable_MPa=2 if not h2 else None,lock_method='Thin metal nut + removable thread-lock + positive end pin' if thin else 'Nylon locking nut; transverse output pin remains the positive separation stop',journal_nominal_diameter_mm=d-.02,journal_tolerance_mm=[d-.03,d-.01],catalogue_bearing_bore_mm=d))
    # W capture is positive geometry: D4.8 guide head cannot pass a 2.94 slot.
    # Count two guides and two cup edges per guide. Dimension tolerance reduces
    # radial head overlap from 0.93 to 0.73; never use the old assumed 1.08 value.
    wrists=[]
    for side in ['l','r']:
        pull=max(loads[side+'_wrist_flex']['axial_handling_pull_N'],loads[side+'_wrist_deviation']['axial_handling_pull_N'])
        overlap=(4.8-2.94)/2-.2;area=2*2*2.25*overlap
        actual=[]
        for suffix in ['Wguide_-1','Wguide_1','W06','W07','Wpreload_-8','Wpreload_8','palm_screw','palm_nut']:
            name=side+'_'+suffix;actual.append(dict(part=name,present=name in byname))
        stress=pull/area
        wrists.append(dict(side=side,status='PASS_CONDITIONAL' if stress<=8 and all(x['present'] for x in actual) else 'FAIL',parts=actual,head_diameter_mm=4.8,slot_width_mm=2.94,budgeted_radial_capture_mm=overlap,cup_wall_mm=2.25,minimum_capture_area_mm2=area,pull_N=pull,capture_bearing_stress_MPa=stress,allowable_MPa=8,scope='Positive guide-head/slot and keyed-palm M2 capture. S1 fit success is an explicit unmeasured design assumption. Guide screws require the actual stated shoulder and head dimensions; commercial fit remains incoming inspection.'))
    put(OUT/'verification/closure_faults_and_tolerances.json',dict(status='PASS_CONDITIONAL' if all(x['status']=='PASS_CONDITIONAL' for x in rows+wrists) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),joints=rows,wrists=wrists,scope='Geometric positive-stop tests and quasi-static material/tolerance budgets. Axial translation here is a deliberate disassembly fault test, never an operating joint-centre adjustment. Does not measure breakaway torque, creep, wear, nut reuse or vibration retention. End-retention pins must not be omitted.'))
    print('CLOSURE FAILS',[(r.get('axis',r.get('side')),r.get('criteria')) for r in rows+wrists if r['status']=='FAIL'],flush=True)


def sensors(parts):
    rows=[]
    for j in load(OUT/'profiles/joint_interfaces.json'):
        pre=j['id'];axis=np.array(j['axis_world']);mg=next(p for p in parts if p['name']==pre+'_magnet');pcb=next(p for p in parts if p['name']==pre+'_pcb')
        world=lambda p:(F0[p['frame']]@np.r_[p['mass_centroid_mm'],1])[:3]
        c=world(mg);point=world(pcb);delta=point-c
        radial=j.get('sensor_layout')=='radial' or pre in ['lumbar_humeral','l_humeral','r_humeral','l_hip_pitch','r_hip_pitch']
        if not radial:delta=axis*np.dot(delta,axis);point=c+delta
        rr=delta/np.linalg.norm(delta);A=3*np.outer(rr,rr)-np.eye(3);u=np.cross(axis,[0,0,1] if abs(axis[2])<.9 else [0,1,0]);u/=np.linalg.norm(u);v=np.cross(axis,u);C=A@np.c_[u,v];sv=np.linalg.svd(C,compute_uv=False)
        error=0
        for degree in np.linspace(-180,180,721):
            t=math.radians(degree);observed=C@np.array([math.cos(t),math.sin(t)]);xy=np.linalg.lstsq(C,observed,rcond=None)[0];angle=math.degrees(math.atan2(xy[1],xy[0]));error=max(error,abs((angle-degree+180)%360-180))
        rows.append(dict(axis=j['axis_id'],sensor='TMAG5170 three-axis reservation',layout='radial' if radial else 'on-axis IC, possibly off-centre on full PCB',magnet_center_mm=c,ic_design_center_mm=point,separation_mm=float(np.linalg.norm(delta)),ideal_min_singular_value=float(sv[-1]),ideal_condition_number=float(sv[0]/sv[-1]),max_ideal_angle_error_deg=error,samples=721,status='PASS_IDEAL_MODEL' if sv[-1]>.1 and error<1e-9 else 'FAIL'))
    wrist=[]
    for side in ['l','r']:
        count=0;err=0
        for f in np.linspace(-65,70,55):
            for d in np.linspace(-20,30,26):
                m=(rot([1,0,0],d)@rot([0,1,0],f))[:3,:3]@np.array([0,0,1]);ff=math.degrees(math.asin(m[0]));dd=math.degrees(math.atan2(-m[1],m[2]));err=max(err,abs(ff-f),abs(dd-d));count+=1
        wrist.append(dict(side=side,samples=count,max_ideal_error_deg=err,min_jacobian_singular_value=math.cos(math.radians(70)),status='PASS_IDEAL_MODEL' if err<1e-9 else 'FAIL'))
    put(OUT/'verification/sensor_observability.json',dict(status='PASS_IDEAL_MODEL' if all(x['status']=='PASS_IDEAL_MODEL' for x in rows+wrist) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),single_axis=rows,spherical_wrist=wrist,raw_scalar_channels=42,physical_dof=40,required_magnetization='Single-axis shaft magnets must be diametrically magnetized. Wrist magnet direction follows the two constrained spherical angles.',source='https://www.ti.com/lit/ds/symlink/tmag5170.pdf',scope='Analytic dipole rank and inverse-angle test, including off-axis gain/offset mixing. It proves observability in the ideal model only. Routed native carrier and sensor boards are checked separately; this ideal magnetic model does not derive sensor accuracy from PCB DRC. Steel/magnets, other magnets, calibration residuals, saturation, noise, wiring flex and actual accuracy need bench verification. No measured sensor performance is claimed.'))
    print('SENSOR IDEAL',len(rows),len(wrist),'PASS',flush=True)


if __name__=='__main__':
    p,z,s=read_assembly();retention(p,s);sensors(p)
