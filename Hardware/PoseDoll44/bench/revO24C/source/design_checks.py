"""Reliability sizing comparisons, restraint and magnetic feasibility. Not physical certification."""
from validate import *
import importlib.util

def mass_and_load(p):
    densities={'structure':.00124,'rotor':.00124,'metal':.00785,'bearing':.00785,'friction':.0014,'pcb':.002,'magnet':.0075,'connector':.0013}
    results={}
    for rev,folder in [('O24B',BASE_B),('O24C',OUT)]:
        data=load(folder/'assembly.json')['parts'];z=np.load(folder/'assembly_meshes.npz');ff=frames(p,dict(shoulder_flex=90));total=0.;moment={n:np.zeros(3) for n in ['shoulder','elbow','wrist']}
        groups={'shoulder':['shoulder_pitch','shoulder_swing','upper','elbow_base','elbow','fore','wrist_base','wrist_guide','hand_ball'],
                'elbow':['elbow','fore','wrist_base','wrist_guide','hand_ball'],'wrist':['hand_ball']}
        anchors={'shoulder':'shoulder_base','elbow':'elbow_base','wrist':'wrist_base'}
        for part in data:
            i=str(part['i']);m=trimesh.Trimesh(z[i+'v'],z[i+'f'],process=False);g=m.volume*densities[part['role']];total+=g
            center=(ff[part['frame']]@np.r_[m.center_mass,1])[:3]
            for key,tokens in groups.items():
                if part['frame'] in tokens:moment[key]+=np.cross((center-ff[anchors[key]][:3,3])/1000,[0,0,-g*.00980665])
        results[rev]=dict(geometric_mass_g=total,horizontal_gravity_Nm={k:float(np.linalg.norm(v)) for k,v in moment.items()})
    put(OUT/'verification/load_budget.json',dict(status='BUDGET_ONLY',method='Actual mesh signed-volume centroids and assumed material densities; same density set for B/C. Simplified solid bearings and rigid overlaps, omitted wiring/lock hardware. Neither measured weight nor a strength certification.',density_g_per_mm3=densities,revisions=results,
        retained_bench_holding_targets_Nm=dict(shoulder=.13,elbow=.04,wrist=.006),physical_tests='NOT RUN'))

def bearing_and_contact(A):
    parts={v['name']:v for v in A.parts};meta=load(OUT/'assembly.json')['parts'];data={v['name']:v for v in meta}
    # Check protected standard items by rigid-invariant dimensions/volume, against actual A geometry.
    old={v['name']:v for v in load(OLD/'assembly.json')['parts']};checks=[]
    for n,v in data.items():
        if n.startswith('C_') or v['role'] not in ['bearing','friction','pcb','magnet']:continue
        size=np.ptp(np.array(v['bounds_mm']),axis=0);before=old[n]
        checks.append(dict(part=n,max_extent_change_mm=float(np.max(abs(size-np.ptp(np.array(before['bounds_mm']),axis=0)))),volume_change_mm3=abs(v['volume_mm3']-before['volume_mm3'])))
    # Discrete actual inner-surface triangles yield contact area and effective radius under uniform pressure.
    contact={}
    for rev,folder,prefix,radius in [('O24B',BASE_B,'B_',12.05),('O24C',OUT,'C_',11.05)]:
        z=np.load(folder/'assembly_meshes.npz');selected=[r for r in load(folder/'assembly.json')['parts'] if r['name'].startswith(prefix+'spherical_liner')];area=0.;r_integral=np.zeros(3);normals=[]
        for part in selected:
            verts=z[str(part['i'])+'v'];faces=z[str(part['i'])+'f'];rr=np.linalg.norm(verts,axis=1)
            face_mask=np.all(abs(rr[faces]-radius)<.02,axis=1);tri=verts[faces[face_mask]]
            areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2;centers=tri.mean(1);area+=areas.sum()
            for axis in range(3):r_integral[axis]+=(np.linalg.norm(np.delete(centers,axis,1),axis=1)*areas).sum()
            normals.extend(centers/np.linalg.norm(centers,axis=1)[:,None])
        effective=r_integral/area;worst=min(effective[:2]);normal_load=.006/(.2*worst/1000)
        contact[rev]=dict(inner_contact_area_mm2=float(area),uniform_pressure_effective_radius_xyz_mm=effective,minimum_xy_effective_radius_mm=float(worst),normal_load_for_006Nm_mu02_N=float(normal_load),mean_pressure_MPa=float(normal_load/area))
    # A conservative second budget uses 3.5 mm instead of uniform-pressure mean radius.
    c=CONFIG;normal=.006/(.2*.0035);span=2*c['elbow_ear_center_mm'];bearing_reaction=2/2+.04/(span/1000)
    report=dict(status='PASS' if all(r['max_extent_change_mm']<1e-7 and r['volume_change_mm3']<1e-5 for r in checks) else 'FAIL',
        geometry_sha256=sha(OUT/'assembly_meshes.npz'),protected_standard_components=checks,
        retained_dimensions_mm=dict(shoulder_elbow_shaft=4,axial_journal_OD=6,axial_journal_ID=3,shoulder_yoke_strut=6,elbow_fork_strut=5.2,wrist_pin=3,wrist_neck=6,liner_thickness=.7,socket_radial_wall=2.25),
        contact_comparison=contact,wrist_conservative_sizing=dict(target_Nm=.006,assumed_mu=.2,assumed_effective_radius_mm=3.5,required_total_normal_N=normal,mean_pressure_on_C_area_MPa=normal/contact['O24C']['inner_contact_area_mm2']),
        elbow_support=dict(old_bearing_span_mm=28,new_bearing_span_mm=span,assumed_radial_force_N=2,assumed_overturning_moment_Nm=.04,estimated_max_radial_reaction_N=bearing_reaction,
            catalog_684ZZ_static_radial_N=22*9.80665,source='https://www.smbbearings.com/firebrick/ckeditor/plugins/upload/Uploads/Documents/bearingpdfs/684ZZ-miniature-bearing-4x9x4mm.pdf',
            warning='Radial capacity comparison only; does not approve friction preload through the bearing or plastic seats.'),
        guide_nominal_half_play_deg=dict(O24B=math.degrees(math.atan(.15/14)),O24C=math.degrees(math.atan((c['slot_radius_mm']-1.5)/13))),
        scope='PASS covers retained standard dimensions only. Contact areas and loads are assumed-pressure sizing calculations. Actual friction, preload force path, print anisotropy, fits, guide binding, wear and long-term hold remain untested.')
    put(OUT/'verification/reliability_screen.json',report)

def restraint(A):
    pins=[r for r in A.parts if r['name'].startswith('C_guide_pin')];caps=[r for r in A.parts if r['name'].startswith('C_socket_half')];rows=[]
    for f,d in [(0,0),(55,20),(-60,-15)]:
        for r in [0,4,-4]:
            M=a.rot([1,0,0],d)@a.rot([0,1,0],f)@a.rot([0,0,1],r)
            volume=sum((a.moved(pin['s'],M)^cap['s']).volume() for pin in pins for cap in caps)
            rows.append(dict(flex=f,deviation=d,extra_roll=r,overlap_mm3=volume))
    ok=all(r['overlap_mm3']<.02 if r['extra_roll']==0 else r['overlap_mm3']>.02 for r in rows)
    put(OUT/'verification/antiroll_negative_control.json',dict(status='PASS' if ok else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),cases=rows,scope='Actual pin/slot geometry rejects unauthorized roll; not a strength or backlash test.'))
    r=CONFIG['liner_inner_radius_mm'];normals=np.array([[sx*3,sy*10,sz*math.sqrt(r*r-3*3-10*10)] for sx in [-1,1] for sy in [-1,1] for sz in [-1,1]])/r
    assert np.linalg.matrix_rank(normals)==3 and np.linalg.norm(normals.sum(0))<1e-10
    liner_min=min(np.array(p['s'].bounding_box()).reshape(2,3)[0,2] for p in A.parts if p['name'].startswith('C_spherical_liner'))
    assert liner_min>CONFIG['socket_lower_lip_z_mm']
    put(OUT/'verification/capture_feasibility.json',dict(status='PASS',geometry_sha256=sha(OUT/'assembly_meshes.npz'),contact_normals=normals,rank=3,positive_equal_weight_sum_norm=np.linalg.norm(normals.sum(0)),liner_min_z_mm=liner_min,trim_z_mm=CONFIG['socket_lower_lip_z_mm'],scope='Contact normals lie within retained opposing liner patches, positively span translation; free-lip cut stays below liner. Local ideal constraint only, not retention strength, pullout or manufactured fit qualification.'))

def magnetic(p):
    # Reuse the published B estimator equations, injecting C values/output only.
    sys.path.insert(0,str(H/'cad/revO24B'))
    spec=importlib.util.spec_from_file_location('wrist_principle_B',H/'cad/revO24B/validate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.CONFIG=CONFIG;module.OUT=OUT;module.sensing()
    meta=load(OUT/'assembly.json')['parts'];magnets=[r for r in meta if r['role']=='magnet' and not r['name'].startswith('C_')];samples=load(OUT/'verification/motion_dense.json')['cases'];rows=[]
    for case in samples:
        f=frames(p,case['angles']);sensor=(f['wrist_base']@np.r_[CONFIG['sensor_position_mm'],1])[:3];mags=[]
        for mag in magnets:
            center=(f[mag['frame']]@np.r_[np.mean(mag['bounds_mm'],axis=0),1])[:3];distance=np.linalg.norm(center-sensor);bound=2*1.2*mag['volume_mm3']/(4*math.pi*distance**3)*1000
            mags.append(dict(part=mag['name'],distance_mm=distance,upper_bound_mT=bound,fixed=mag['frame']=='fore'))
        rows.append(dict(pose=case['pose'],variable_bound_mT=sum(m['upper_bound_mT'] for m in mags if not m['fixed']),fixed_bound_mT=sum(m['upper_bound_mT'] for m in mags if m['fixed']),parts=mags))
    worst=max(rows,key=lambda r:r['variable_bound_mT'])
    put(OUT/'verification/magnetic_interference_budget.json',dict(status='BUDGET_ONLY',geometry_sha256=sha(OUT/'assembly_meshes.npz'),samples=len(samples),worst_variable=worst,max_fixed_bound_mT=max(r['fixed_bound_mT'] for r in rows),scope='Conservative point-dipole magnitude upper bounds summed, Br=1.2 T assumed. Not the actual vector field or angular error; no finite-magnet/ferromagnetic/ambient model or calibration.'))

if __name__=='__main__':
    p=load(OUT/'profiles/arm_profile.json');A=exported();mass_and_load(p);bearing_and_contact(A);restraint(A);magnetic(p);freeze_baselines();print('Sizing and sensing reports written; physical qualification remains NOT RUN.')
