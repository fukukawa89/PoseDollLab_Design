"""New E mass/load budget and inherited UE mapping, with explicit changed wrists."""
from verify import *
import importlib

def patch_modules():
    import strength,standing,engineering,bone_alignment
    for m in list(sys.modules.values()):
        file=getattr(m,'__file__','') or ''
        if 'cad' in file and 'revO24D' in file and Path(file).name!='fullbody.py':
            for k,val in dict(OUT=OUT,PROFILE=PROFILE,NODES=NODES,F0=F0,FA=FA,frames=frames).items():
                if hasattr(m,k):setattr(m,k,val)
            if hasattr(m,'DENSITY'):m.DENSITY['spring']=.00785
    return strength,standing,bone_alignment

def main():
    context();strength,standing,bone=patch_modules()
    # Geometry is read once as actual production bodies to avoid same-material
    # double-counting of overlapping construction features.
    prod=load(OUT/'production_assembly.json')['parts'];zz=np.load(OUT/'production_meshes.npz')
    for p in prod:
        p.setdefault('density_g_mm3',.00785 if 'steel' in p.get('material','').lower() else strength.DENSITY[p['role']])
    solids=[md.Manifold(md.Mesh64(np.array(zz[str(p['i'])+'v'],dtype=np.float64,copy=True,order='C'),np.array(zz[str(p['i'])+'f'],dtype=np.uint64,copy=True,order='C'))) for p in prod]
    # Stock inspection routines rely on feature names for bearing identification,
    # so use unique material masses with redistributed feature mass, not renamed IDs.
    parts,z,ss=context().read_assembly();by={p['name']:p for p in parts};mapping=load(OUT/'production_parts.json')
    struct=[p for p in parts if p['role'] in ['structure','rotor','shell']]
    for p in struct:p['volume_mm3']=0
    for body in mapping['structural_parts']:
        owner=by[body['source_features'][0]];fr=body['frame'];pr=next(p for p in prod if p['name']==body['part_number'])
        local=np.linalg.inv(F0[owner['frame']])@F0[fr]@np.r_[pr['mass_centroid_mm'],1]
        # One owner may own several separate physical bodies; preserve total first moment.
        old=owner['volume_mm3'];new=body['volume_mm3'];prev=np.array(owner['mass_centroid_mm'])
        owner['mass_centroid_mm']=((old*prev+new*local[:3])/(old+new)).tolist();owner['volume_mm3']+=new
    def read_mass():return parts,z,ss
    strength.read_assembly=read_mass;standing.read_assembly=read_mass
    # Harness carried forward by exact route nodes, then updated by electronics.py.
    standing.main();strength.main()
    report=load(OUT/'verification/preload_retention_loads.json')
    for row in report['rows']:
        if 'wrist_' not in row['axis']:
            j=next(j for j in load(OUT/'profiles/joint_interfaces.json') if j['axis_id']==row['axis'])
            if 'cartridge_hex_radius_mm' in j:
                t=j['cap_effective_ligament_mm'];r=j['cap_supported_radius_mm'];span=max(.1,j['friction_od_mm']/2-r)
                stress=2*row['required_clamp_N']*span/(2*math.pi*r*(t*t/6))
                area={2:2.07,3:5.03}[row['torque_pin_diameter_mm']]
                force=max(row['hold_target_Nm']*1000/(j['bearing_diameter_mm']/2),row['axial_handling_pull_N'])
                row.update(front_cap_effective_ligament_mm=t,front_cap_stress_MPa=stress,front_cap_yield_factor=j['front_cap_min_yield_MPa']/stress,capture_screw_double_shear_factor=2*area*450/force,capture_screw_grade='ISO4762 10.9, conservative shear 450 MPa; threaded stress area used')
                row['torque_pin_double_shear_factor']=row['capture_screw_double_shear_factor']
                row['criteria']['torque_pin']=row['capture_screw_double_shear_factor']>=2
                thread_area={4:8.78,6:20.1}[j['thread_diameter_mm']]
                row['axial_retention_factor']=min(1000,2*area*450,450*thread_area)/row['axial_handling_pull_N']
                row['axial_retention_basis']='Minimum of original D1.5 fixed capture pin rated 1000 N, new class10.9 transverse screw double shear, and shaft-thread proof; material/fit qualification remains pending.'
                row['criteria']['axial_retention']=row['axial_retention_factor']>=3
                row['criteria'].update(front_cap=row['front_cap_yield_factor']>=2,capture_screw=row['capture_screw_double_shear_factor']>=2)
            row['status']='PASS_CONDITIONAL' if all(row['criteria'].values()) else 'FAIL'
            continue
        # Two ears x two friction faces; each O22 stack receives this force.
        reff=2/3*(6**3-2.15**3)/(6**2-2.15**2)
        row['effective_radius_mm']=reff;row['friction_faces']=4
        row['required_clamp_per_O22_N']=max(1,row['hold_target_Nm']*1000/(4*.08*reff))
        row['model']='T6 W double-ear / double-face Ry@Rx; no ball/cup preload model inherited'
        row['physical_test_status']='User accepted T6 W; changed integration mass/load must be checked physically'
        for k in ['conservative_effective_radius_mm','assumed_min_lip_area_mm2','lip_stress_MPa','neck_bending_stress_MPa']:row.pop(k,None)
        row['interface']='T6_W_DOUBLE_AXIS';row['required_clamp_N']=row['required_clamp_per_O22_N']
        row['ear_net_Z_mm3']=(12-4.25)*4**2/6;row['ear_bending_screen_MPa']=row['hold_target_Nm']*1000/(2*row['ear_net_Z_mm3'])
        row['criteria']=dict(M3_proof=450*5.03/row['required_clamp_N']>=2,ear_bending=row['ear_bending_screen_MPa']<=8)
        row['physical_load_qualification']='PENDING'
        row['status']='PASS_CONDITIONAL' if all(row['criteria'].values()) else 'FAIL'
    report['mass_basis']='Boolean-unioned same-material production bodies, separate purchased hardware; no double counting of fused primitives'
    report['calculation_failures']=[r['axis'] for r in report['rows'] if r['status']=='FAIL']
    report['status']='PASS_CONDITIONAL' if not report['calculation_failures'] else 'FAIL'
    report['physical_load_qualification']='PENDING'
    report['scope']='Quasi-static same-material union mass plus E harness. Material, friction and printed allowable conditions are unmeasured. No impact, fatigue or 100-cycle qualification.'
    report['assumptions']=[s for s in report['assumptions'] if 'Spherical' not in s and 'spring-pin strength' not in s]+['Dry steel friction >=0.08, printed allowable 8 MPa, and stated certified shaft/plate/cap materials required. Capture bolt uses ISO4762 class10.9, not an old roll-pin rating. W is T6 double axis, not S1 ball joint.']
    put(OUT/'verification/preload_retention_loads.json',report)
    current={r['axis']:r for r in report['rows']};checks=[]
    for pk in load(OUT/'profiles/preload_selection.json')['rows']:
        target=current[pk['axis']]['required_clamp_N']/(2 if pk['family']=='H16' else 1)
        reserve=.925*pk['catalogue_force_at_75pct_N']/target
        checks.append(dict(axis=pk['axis'],tie=pk.get('tie'),required_N=target,spring=pk['sku'],parallel=pk['parallel'],series=pk['series'],capacity_75pct_lower_tolerance_N=.925*pk['catalogue_force_at_75pct_N'],capacity_ratio=reserve,status='PASS_CAPACITY_ONLY' if reserve>=1.15 else 'FAIL',adjustment='Use measured holding torque and axial stack height; rendered 65% deflection is not a tightening instruction. Verify settlement and 100 cycles.'))
    put(OUT/'verification/elastic_preload.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),status='PASS_CAPACITY_ONLY' if all(r['status']=='PASS_CAPACITY_ONLY' for r in checks) else 'FAIL',rows=checks,source=SOURCE_URL,actual_A8_curve_measured=False,scope='Catalogue capacity with -7.5% load tolerance; does not prove preload at an arbitrary nut angle or after wear.'))
    # Actual bone-tube cross-sections remain available under feature names.
    bone.main()
    channels=load(BASE/'profiles/channel_map.json');channels.update(revision='O24E',wrist_order=PROFILE['wrist_order'],calibration_valid=False)
    for c in channels['channels']:
        if c.get('kind')=='Bx_By_Bz':c.update(solved_axes=[c['id'][0]+'_wrist_flex',c['id'][0]+'_wrist_deviation'],model='O24E Ry@Rx calibrated field LUT; reject old D calibration')
    put(OUT/'profiles/channel_map.json',channels)
    old=load(BASE/'reference/full_UE_N_pose.json')
    for bone_row in old['bones']:
        if bone_row['frame'].endswith('wrist_flex'):bone_row['frame']=bone_row['frame'].replace('wrist_flex','wrist_deviation')
    put(OUT/'reference/full_UE_N_pose.json',old)
    put(OUT/'profiles/pose_frames.json',{n:frames(p['angles']) for n,p in load(OUT/'profiles/poses.json').items()})
    print('SYSTEM',report['total_solid_mass_g'] if 'total_solid_mass_g' in report else report.keys(),flush=True)

if __name__=='__main__':main()
