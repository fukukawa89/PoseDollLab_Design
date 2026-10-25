"""Independent geometry/kinematics checks for the constrained ball wrist."""
from spherical_wrist import *
import argparse,time
from verify import target_fk

def collision(A,p,cases):
    rows=[];start=time.time()
    for name,q in cases.items():
        ff=frames(p,q);world=[a.moved(v['s'],ff[v['frame']]) for v in A.parts]
        bounds=np.array([s.bounding_box() for s in world]).reshape(-1,2,3);hits=[]
        family=lambda t:{'shoulder_base':'collar','elbow_base':'upper','wrist_base':'fore'}.get(t,t)
        for i,x in enumerate(A.parts):
            for j in range(max(i+1,94),len(A.parts)):
                y=A.parts[j]
                if family(x['frame'])==family(y['frame']):continue
                if np.any(bounds[i,1]<=bounds[j,0]+1e-5) or np.any(bounds[j,1]<=bounds[i,0]+1e-5):continue
                volume=(world[i]^world[j]).volume()
                if volume>.02:hits.append(dict(a=x['name'],b=y['name'],volume_mm3=round(volume,6)))
        rows.append(dict(name=name,angles=q,collisions=hits))
        if hits:print(name,json.dumps(hits),flush=True)
    return dict(status='FAIL' if any(r['collisions'] for r in rows) else 'PASS',samples=len(rows),seconds=time.time()-start,
        geometry_sha256=sha(OUT/'assembly_meshes.npz'),threshold_mm3=.02,
        scope='Different-frame pairs involving the new wrist, including sensors and proximal arm; unchanged proximal/proximal pairs use O24A audit. Discrete rigid nominal meshes, not flexible preload deformation, continuous motion, tools or full torso.',cases=rows)

def analytic(p,ref):
    data=load(OUT/'assembly.json')['parts'];z=np.load(OUT/'assembly_meshes.npz');ball=next(x for x in data if x['name']=='B_ball_and_centered_neck')
    verts=z[str(ball['i'])+'v'];vv=verts[np.abs(np.linalg.norm(verts,axis=1)-12)<1e-5]
    fit=np.linalg.lstsq(np.c_[2*vv,np.ones(len(vv))],np.sum(vv*vv,axis=1),rcond=None)[0];center=fit[:3]
    shaft=verts[(verts[:,2]<-12.1)&(np.abs(np.linalg.norm(verts[:,:2],axis=1)-3)<1e-5)]
    stem_xy=shaft[:,:2].mean(0);rng=np.random.default_rng(2402);max_error=0.;max_plane=0.;max_stem=0.
    for _ in range(1000):
        q={x['id']:rng.uniform(*x['limits_deg']) for x in p['axes']};ff=frames(p,q);target=target_fk(ref,q)
        actual=ff['hand_ball'][:3,:3]@center+ff['hand_ball'][:3,3]
        max_error=max(max_error,float(np.linalg.norm(actual-target['W'])))
        local=np.linalg.inv(ff['wrist_base'])@ff['hand_ball'];max_plane=max(max_plane,abs(float(local[0,1])))
        origin=ff['hand_ball'][:3,:3]@np.r_[stem_xy,0]+ff['hand_ball'][:3,3]
        max_stem=max(max_stem,float(np.linalg.norm(np.cross(target['W']-origin,ff['hand_ball'][:3,2]))))
    assert max_error<1e-8 and max_plane<1e-10 and max_stem<1e-8
    result=dict(status='PASS',samples=1000,sphere_vertices_fitted=len(vv),fitted_ball_center_local_mm=center,
        max_ball_center_error_to_UE_W_mm=max_error,max_neck_axis_to_W_error_mm=max_stem,
        max_guide_pin_plane_constraint_error=max_plane,physical_dof=2,
        constraint='ex^T R ey = 0; two opposing pins are redundant guides, not two independent constraints. Constraint rotational Jacobian has rank 1, leaving 2 rotations.',
        min_output_direction_jacobian_singular_value=math.cos(math.radians(70)),
        nominal_unpreloaded_guide_half_play_deg=math.degrees(math.atan((CONFIG['slot_radius_mm']-CONFIG['pin_radius_mm'])/14)),
        physical_accuracy_measured=False,geometry_sha256=sha(OUT/'assembly_meshes.npz'))
    put(OUT/'verification/kinematics.json',result);return result

def sensing():
    # First-order point dipole feasibility only. It is intentionally not a calibrated sensor simulation.
    c=CONFIG;r=np.array(c['sensor_position_mm'])/1000;v=math.pi*(c['magnet_diameter_mm']/2000)**2*c['magnet_height_mm']/1000
    k=c['magnet_model_Br_T']*v/(4*math.pi*np.linalg.norm(r)**3)*1000 # mT
    u=r/np.linalg.norm(r);D=k*(3*np.outer(u,u)-np.eye(3));inv=np.linalg.inv(D)
    rng=np.random.default_rng(5170);errors=[];quant_errors=[];field=[];roundtrip=[];lsb=2*c['sensor_range_mT']/2**c['sensor_ADC_bits']
    def estimate(B):
        m=inv@B;m=m/np.linalg.norm(m)
        return np.degrees([math.asin(np.clip(m[0],-1,1)),math.atan2(-m[1],m[2])])
    for f in np.linspace(-65,70,28):
        for d in np.linspace(-20,30,11):
            R=(a.rot([1,0,0],d)@a.rot([0,1,0],f))[:3,:3];B=D@R[:,2];field.append(np.linalg.norm(B));roundtrip.append(np.max(abs(estimate(B)-[f,d])))
            quant_errors.append(estimate(np.round(B/lsb)*lsb)-[f,d])
            for _ in range(10):errors.append(estimate(B+rng.normal(0,.01,3))-[f,d])
    # A centered axial magnet has no information about spin around its own axis.
    ambiguous1=D@np.array([0,0,1]);ambiguous2=D@(a.rot([0,0,1],60)[:3,:3]@np.array([0,0,1]))
    result=dict(status='PASS',scope='Analytic two-DOF observability feasibility only; NOT hardware accuracy, NOT finite-cylinder magnetic simulation or cross-talk validation.',
        model='centered axial point dipole; B = K(3rr^T-I) R ez; R=Rx(deviation)Ry(flexion)',
        nominal_equatorial_field_mT=k,field_magnitude_range_mT=[min(field),max(field)],ideal_roundtrip_max_error_deg=max(roundtrip),
        sensor_adc_quantization_lsb_mT=lsb,ideal_quantization_RMS_deg=np.sqrt(np.mean(np.array(quant_errors)**2,axis=0)),
        assumed_independent_field_noise_mT=.01,assumed_noise_RMS_deg=np.sqrt(np.mean(np.array(errors)**2,axis=0)),
        full_3dof_60deg_spin_field_difference_mT=float(np.linalg.norm(ambiguous1-ambiguous2)),
        does_not_measure_unconstrained_ball_roll=True,physical_sensor_test='NOT RUN',
        unresolved=['Finite magnet geometry and offsets','Cross-talk from proximal O24A magnets','Ferromagnetic fasteners','Sensor gain, bias and temperature','Guide backlash allows unobserved extra rotation','PCB routing and calibration dataset'])
    assert result['ideal_roundtrip_max_error_deg']<1e-9
    put(OUT/'verification/magnetic_feasibility.json',result);return result

def comparison():
    old=load(OLD/'assembly.json')['parts'][94:123];new=[p for p in load(OUT/'assembly.json')['parts'][94:] if p['name']!='B_hand_handle']
    def bounds(parts):
        lo=np.min([p['bounds_mm'][0] for p in parts],axis=0);hi=np.max([p['bounds_mm'][1] for p in parts],axis=0)
        return dict(min_mm=lo,max_mm=hi,size_mm=hi-lo,box_volume_mm3=float(np.prod(hi-lo)),parts=len(parts))
    aa,bb=bounds(old),bounds(new)
    out=dict(status='PASS',frame='Local wrist frame, neutral, rigid palm excluded in both. Includes new custom PCB and nominal fasteners; not swept volume or final manufacturing dimensions.',
        O24A=aa,O24B=bb,box_volume_change_percent=(bb['box_volume_mm3']/aa['box_volume_mm3']-1)*100,
        reference_height_mm=560,full_doll_height='NOT BUILT',unchanged_UE_joint_centers=True,
        wrist_angle_order_changed=True,old_wrist_rotation='Ry(flexion) @ Rx(deviation)',new_wrist_rotation=CONFIG['angle_order'],
        old_wrist_sensor_channels=2,new_wrist_field_sensors=1,new_wrist_virtual_angles=2,firmware_compatible=False)
    put(OUT/'verification/comparison.json',out);return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true');args=parser.parse_args()
    p=load(OLD/'profiles/arm_profile.json');ref=load(OLD/'reference/target_quinn.json');A=build()
    ff=[-65,0,70] if args.quick else np.arange(-65,71,5);dd=[-20,0,30] if args.quick else np.arange(-20,31,5)
    cases={f'wrist/{f}/{d}':dict(wrist_flex=float(f),wrist_deviation=float(d),elbow_flex=90) for f in ff for d in dd}
    cases.update({name:q for name,(_,q) in a.poses().items()})
    result=collision(A,p,cases);put(OUT/'verification'/('motion_quick.json' if args.quick else 'motion_grid.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},ensure_ascii=False))
    if not args.quick:
        for name,value in [('kinematics',analytic(p,ref)),('magnetic',sensing()),('comparison',comparison())]:print(name,json.dumps({k:v for k,v in value.items() if k not in ['rows','unresolved']},default=lambda x:x.tolist(),ensure_ascii=False))
    for name,digest in load(OUT/'reference/O24A_frozen_hashes.json').items():assert sha(OLD/name)==digest,'O24A changed'

if __name__=='__main__':main()
