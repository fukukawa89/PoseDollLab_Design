"""Transparent quasi-static calculations on the delivered full-body solids.

Finite pose/path envelope, not FEA, impact qualification or physical test data.
Each PASS is conditional on the named material and friction specifications.
"""
from engineering import *
from rom_cases import examination_cases

DENSITY={'structure':.00124,'rotor':.00124,'shell':.00124,'friction':.00785,'metal':.00785,'bearing':.00785,'pcb':.002,'magnet':.0075,'connector':.0013}

def cases():
    q={n:p['angles'] for n,p in poses().items()}
    if (HERE/'load_envelope_angles.json').exists():q.update(load(HERE/'load_envelope_angles.json')['cases'])
    for n,p in examination_cases().items():
        q[n]=p['angles'];base=dict(p['angles']);base[p['axis']]=0
        steps=max(1,math.ceil(abs(p['value_deg'])/4))
        for i in range(steps):q[n+f'/scan/{i}']={**base,p['axis']:p['value_deg']*i/steps}
    pathfile=OUT/'verification/motion_task_paths.json'
    if pathfile.exists():
        paths=load(pathfile)
        if paths.get('geometry_sha256')==sha(OUT/'assembly_meshes.npz'):
            for p in paths.get('cases',[]):
                for i,state in enumerate(p.get('path') or []):q[f"path/{p['pose']}/{i}"]=state
    gridfile=OUT/'verification/joint_local_grids.json'
    if gridfile.exists():
        grid=load(gridfile)
        if grid.get('geometry_sha256')==sha(OUT/'assembly_meshes.npz'):
            for group in grid['groups']:
                for c in group['cases']:q['grid/'+','.join(group['axes'])+'/'+str(c['index'])]=c['angles']
    # Remove duplicates without dropping provenance of extrema.
    seen=set();unique=[]
    for name,state in q.items():
        key=tuple(sorted((k,round(float(v),8)) for k,v in state.items() if abs(v)>1e-9))
        if key not in seen:unique.append((name,state));seen.add(key)
    return unique

def channel_section(width,thickness=2,depth=7,hole_width=6.4,flanges=2):
    # Deliberately remove both complete M3 holes from every section. This
    # understates the real section modulus between the holes.
    rect=[(max(width-hole_width,.1)*thickness,thickness/2,(width-hole_width)*thickness**3/12)]
    rect += [(2*depth,thickness+depth/2,2*depth**3/12)]*flanges
    area=sum(a for a,c,I in rect);cent=sum(a*c for a,c,I in rect)/area
    inertia=sum(I+a*(c-cent)**2 for a,c,I in rect)
    modulus=inertia/max(cent,thickness+depth-cent)
    return dict(area_mm2=area,centroid_mm=cent,I_mm4=inertia,Z_mm3=modulus,full_holes_removed_from_every_section=True)

def main():
    parts,z,solids=read_assembly();mass={n:0. for n in NODES};moment={n:np.zeros(3) for n in NODES}
    for p in parts:
        m=p['volume_mm3']*p.get('density_g_mm3',DENSITY[p['role']]);mass[p['frame']]+=m;moment[p['frame']]+=m*np.array(p['mass_centroid_mm'])
    wire_mass=0.
    if (OUT/'harness/mass_lumps.json').exists():
        h=load(OUT/'harness/mass_lumps.json');assert h['geometry_sha256']==sha(OUT/'assembly_meshes.npz'),'Stale harness mass'
        for p in h['lumps']:
            m=p['mass_g'];mass[p['frame']]+=m;moment[p['frame']]+=m*np.array(p['local_mm']);wire_mass+=m
    subtree=dict(mass)
    for n in reversed(PROFILE['nodes']):
        if n['parent']:subtree[n['parent']]+=subtree[n['id']]
    interfaces={j['axis_id']:j for j in load(OUT/'profiles/joint_interfaces.json')}
    bearingcentres={}
    for p in parts:
        if p['role']=='bearing':bearingcentres.setdefault(bearing_axis(p['name']),[]).append((p['frame'],np.mean(np.array(p['bounds_mm']),axis=0)))
    result={a['id']:dict(axis=a['id'],downstream_solid_mass_g=subtree[a['id']],gravity_Nm=0.,bending_Nm=0.,bearing_reaction_N=0.,worst_hold_pose=None,worst_bearing_pose=None) for a in PROFILE['axes']}
    allcases=cases();factor=1.25*1.5
    for ci,(name,state) in enumerate(allcases):
        F=frames(state);sums={n:F[n][:3,:3]@moment[n]+mass[n]*F[n][:3,3] for n in NODES}
        for n in reversed(PROFILE['nodes']):
            if n['parent']:sums[n['parent']]+=sums[n['id']]
        for a in PROFILE['axes']:
            key=a['id'];o=F[key][:3,3];axis=F[key][:3,:3]@np.array(a['axis']);fg=np.array([0,0,-subtree[key]*9.80665/1000]);torque=np.cross((sums[key]-subtree[key]*o)/1e6,[0,0,-9.80665])
            axial=abs(float(np.dot(torque,axis)));r=result[key]
            if axial>r['gravity_Nm']:r['gravity_Nm']=axial;r['worst_hold_pose']=name
            if key in interfaces:
                j=interfaces[key];bc=bearingcentres[key];centre=np.mean([F[fr][:3,:3]@point+F[fr][:3,3] for fr,point in bc],axis=0)
                mb=torque+np.cross((o-centre)/1000,fg);bend=float(np.linalg.norm(mb-axis*np.dot(mb,axis)));radial=float(np.linalg.norm(fg-axis*np.dot(fg,axis)))
                reaction=radial/2+bend*1000/j['bearing_span_mm'];r['bending_Nm']=max(r['bending_Nm'],bend)
                if reaction>r['bearing_reaction_N']:r['bearing_reaction_N']=reaction;r['worst_bearing_pose']=name
        if ci%250==0:print('LOAD CASE',ci,'/',len(allcases),flush=True)
    ground=load(OUT/'verification/standing_ground_loads.json')
    assert ground['geometry_sha256']==sha(OUT/'assembly_meshes.npz'),'Stale standing loads'
    for g in ground['joint_loads']:
        r=result[g['axis']];r['ground_joint_force_N']=g['joint_force_N']
        for key,posekey in [('gravity_Nm','worst_hold_pose'),('bearing_reaction_N','worst_bearing_pose')]:
            if g[key]>r[key]:r[key]=g[key];r[posekey]='ground/'+str(g[posekey])
        r['bending_Nm']=max(r['bending_Nm'],g['bending_Nm'])
    checks=[]
    for a in PROFILE['axes']:
        key=a['id'];r=result[key];target=r['gravity_Nm']*factor;r['hold_target_Nm']=target;r['design_bending_Nm']=r['bending_Nm']*factor
        if key in interfaces:
            j=interfaces[key];ri=j['friction_inner_loaded_radius_mm'];ro=j['friction_od_mm']/2;reff=2/3*(ro**3-ri**3)/(ro**2-ri**2);force=max(10,target*1000/(2*.08*reff))
            pad_area=math.pi*(ro**2-ri**2)
            if 'cartridge_hex_radius_mm' in j:
                theta=np.linspace(-math.pi/6,math.pi/6,32768,endpoint=False)+math.pi/196608
                rad=np.minimum(ro,j['cartridge_hex_radius_mm']*math.sqrt(3)/2/np.cos(theta))
                pad_area=float(math.pi*np.mean(rad**2-ri**2))
                reff=float((2/3)*np.mean(rad**3-ri**3)/np.mean(rad**2-ri**2))
                force=max(10,target*1000/(2*.08*reff))
            d=j['bearing_diameter_mm'];thread=j['thread_diameter_mm'];As={2:2.07,3:5.03,4:8.78,6:20.1}[thread];boltcount=2 if 'pressure_web_width_mm' in j else 1
            bolt_sf=450*As*boltcount/max(force,1e-12)
            bearing_sf=(225 if d==4 else 292)/max(r['bearing_reaction_N']*factor,1e-12)
            shaft_d=d-.03  # Minimum journal after the specified 0.02 mm nominal diametral clearance.
            shaft_bend=32*r['design_bending_Nm']*1000/(math.pi*shaft_d**3);shaft_shear=16*target*1000/(math.pi*shaft_d**3)
            # Cross-drilled section: explicit Kt=3 screening, not a smooth-shaft
            # calculation disguised as a drilled-shaft check.
            shaft_axial=force/As if boltcount==1 else 0
            vm=math.sqrt((shaft_axial+3*shaft_bend)**2+3*(3*shaft_shear)**2)
            shaft_yield=j['shaft_min_yield_MPa'];shaft_sf=shaft_yield/max(vm,1e-12)
            pull=max(10,subtree[key]/1000*9.80665*1.25*3,r.get('ground_joint_force_N',0)*1.25*3)
            pin_d=(3 if d==6 else 2);pin_rating={1.5:1000,2:2000,3:4500}[pin_d]
            pin_force=target*1000/(d/2);pin_sf=pin_rating/max(pin_force,1e-12)
            retention_sf=1000/pull if boltcount==2 or key=='lumbar_yaw' else 450*As/pull
            pressure=force/pad_area
            capspan=max(0,ro-j['cap_supported_radius_mm']);cap_th=j['cap_thickness_mm'];cap_sigma=j.get('cap_Kt',1)*force*capspan/(2*math.pi*j['cap_supported_radius_mm']*(cap_th**2/6))
            row=dict(**r,interface=j['id'],assumed_min_mu=.08,friction_faces=2,effective_radius_mm=reff,required_clamp_N=force,force_per_screw_N=force/boltcount,thread_proof_factor=bolt_sf,design_bearing_reaction_N=r['bearing_reaction_N']*factor,bearing_static_factor=bearing_sf,shaft_Kt=3,shaft_required_yield_MPa=2*vm,shaft_procurement_min_yield_MPa=shaft_yield,shaft_factor=shaft_sf,torque_pin_diameter_mm=pin_d,torque_pin_double_shear_factor=pin_sf,axial_handling_pull_N=pull,axial_retention_factor=retention_sf,friction_pressure_MPa=pressure,cap_bending_stress_MPa=cap_sigma,cap_yield_factor=230/max(cap_sigma,1e-12))
            row['cap_yield_factor']=j.get('cap_min_yield_MPa',230)/max(cap_sigma,1e-12);row['cap_min_yield_MPa']=j.get('cap_min_yield_MPa',230);row['cap_Kt']=j.get('cap_Kt',1)
            criteria=dict(thread=bolt_sf>=2,bearing=bearing_sf>=1.5,shaft=shaft_sf>=2,torque_pin=pin_sf>=2,axial_retention=retention_sf>=3,cap=row['cap_yield_factor']>=2)
            if boltcount==2:
                sec=channel_section(j['pressure_web_width_mm'],depth=j['pressure_return_depth_mm'],hole_width=6.4+j.get('structural_link_clearance_width_mm',0),flanges=j.get('pressure_return_count_at_relief',2));stress=j.get('pressure_plate_Kt',1)*force*j['pressure_bolt_arm_mm']/sec['Z_mm3'];deflection=force*j['pressure_bolt_arm_mm']**3/(3*200000*sec['I_mm4'])
                row.update(channel_section=sec,plate_bending_stress_MPa=stress,plate_yield_factor=j.get('pressure_plate_min_yield_MPa',230)/max(stress,1e-12),plate_min_yield_MPa=j.get('pressure_plate_min_yield_MPa',230),plate_Kt=j.get('pressure_plate_Kt',1),plate_deflection_mm=deflection,metal_spacer_stress_MPa=force/2/(math.pi*(2.75**2-1.6**2)))
                criteria['plate']=row['plate_yield_factor']>=2;criteria['deflection']=deflection<=.04
                # Tangential support through two metal spacers, then printed
                # bosses. Both bosses per face are included; no 0.2 mm bridge.
                reaction=target*1000/(2*j['pressure_bolt_arm_mm']);boss= reaction/(5.5*5)
                row['guide_boss_bearing_stress_MPa']=boss;criteria['guide_boss']=boss<=8
                hexr=j['output_hex_radius_mm'];eng=j['output_hex_engagement_mm'];socket_stress=3*target*1000/(3*hexr*eng*(hexr*math.sqrt(3)/2))
                row['output_socket_factored_bearing_stress_MPa']=socket_stress;criteria['output_socket']=socket_stress<=8
            else:
                hexr=j['cartridge_hex_radius_mm'];eng=j['output_hex_engagement_mm'];socket_stress=3*target*1000/(3*hexr*eng*(hexr*math.sqrt(3)/2))
                row['output_socket_factored_bearing_stress_MPa']=socket_stress;criteria['output_socket']=socket_stress<=8
            row['loaded_pad_area_mm2']=pad_area;row['pad_material']='cold-rolled 304 flat steel washer, Rp0.2 >=230 MPa';row['pad_compressive_allowable_MPa']=115;criteria['pad_pressure']=pressure<=115
            row['criteria']=criteria;row['status']='PASS_CONDITIONAL' if all(criteria.values()) else 'FAIL';checks.append(row)
        else:
            # S1 spherical wrist: conservative 7 mm contact lever arm; physical
            # coefficient remains an assumption. New upstream mass is excluded
            # correctly because it is not carried by the wrist.
            force=target/(.08*.007);pull=max(10,subtree[key]/1000*9.80665*1.25*3);neck=32*target*1000/(math.pi*6**3)
            criteria=dict(screw=450*5.03*2/max(force,1e-12)>=2,neck=neck<=8,lip=pull/(2*3*1.08)<=8)
            checks.append(dict(**r,interface='S1_W',assumed_min_mu=.08,conservative_effective_radius_mm=7,required_clamp_N=force,axial_handling_pull_N=pull,neck_bending_stress_MPa=neck,assumed_min_lip_area_mm2=6.48,lip_stress_MPa=pull/6.48,criteria=criteria,status='PASS_CONDITIONAL' if all(criteria.values()) else 'FAIL'))
    put(OUT/'verification/preload_retention_loads.json',dict(status='PASS_CONDITIONAL' if all(r['status']=='PASS_CONDITIONAL' for r in checks) else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),case_count=len(allcases),standing_case_count=ground['accepted_standing_samples'],solid_mass_g=sum(mass.values()),harness_mass_g=wire_mass,mass_with_allowance_g=sum(mass.values())*1.25,external_payload_g=0,pelvis_supported=False,load_boundaries=['Manual torso support during arbitrary pose adjustment (no stand socket)','Nonnegative ground reactions in accepted flat-floor standing configurations'],gravity_factor=factor,material_source='reference/engineering_sources.json',rows=checks,scope='Quasi-static self-weight plus explicit harness mass. Envelope combines manually torso-supported configurations and independently balanced free-standing ground reactions. Same-frame solid overlaps and full bearing envelopes overcount mass. No actual measurement, impact, fatigue, lifetime or complete continuous-configuration proof. Screw torque is intentionally not inferred from clamp force.',assumptions=['Friction coefficient >=0.08 must be measured for the selected dry steel washer pair. Brake pads are specified as flat cold-rolled 304 washers, minimum yield 230 MPa; compressive allowable 115 MPa. Spherical wrist liners retain their separate S1 material assumption.','Custom shafts require certified minimum yield 750 MPa after machining; lumbar flexion requires 940 MPa. Ordinary annealed 304 rods do not meet these requirements.','Printed allowable 8 MPa and modulus 1500 MPa are design assumptions, not filament qualification.','Metal plates specified cold-rolled 304 minimum yield 230 MPa; spring-pin strength applies only to the referenced grade/specification.']))
    print('LOAD FAILURES',[(r['axis'],[k for k,v in r['criteria'].items() if not v]) for r in checks if r['status']=='FAIL'],flush=True)

if __name__=='__main__':main()

