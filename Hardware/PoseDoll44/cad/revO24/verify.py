"""O24 geometry, independent target FK, and finite solid-intersection audit."""
from arm import *
import argparse, time

def target_fk(ref,q):
    """Independent point/vector recursion from UE targets, with Rodrigues rotations.
    No mechanical lengths, mount translations, or mechanical FK are read here.
    """
    P=ref['points_mm']; C=np.array(P['clavicle_l']);S=np.array(P['upperarm_l'])
    E=np.array(P['lowerarm_l']);W=np.array(P['hand_l'])
    def R(v,a):
        v=unit(v);a=math.radians(a);K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
        return np.eye(3)+math.sin(a)*K+(1-math.cos(a))*(K@K)
    get=lambda n:q.get(n,0.)
    Rc=R([0,0,-1],get('clavicle_protract'))@R([1,0,0],get('clavicle_elevate'))
    Rs=Rc@R([0,-1,0],get('shoulder_flex'))@R([1,0,0],get('shoulder_abduct'))@R([0,0,-1],get('upperarm_roll'))
    Re=Rs@R([0,-1,0],get('elbow_flex'));Rf=Re@R([0,0,-1],ref['forearm_zero_clocking_deg']+get('forearm_roll'))
    Rh=Rf@R([0,1,0],get('wrist_flex'))@R([1,0,0],get('wrist_deviation'))
    s=C+Rc@(S-C);e=s+Rs@(E-S);w=e+Re@(W-E)
    return dict(C=C,S=s,E=e,W=w,upper_R=Rs,fore_R=Rf,hand_R=Rh)

def kinematic(p,ref):
    rng=np.random.default_rng(24);samples=[q for _,q in poses().values()]
    samples += [{a:rng.uniform(*lim) for a,_,lim,_ in AXES} for _ in range(2000)]
    worst=0.;rotation_error=0.;twist_drift=0.;shoulder_axis_error=0.;wrist_axis_error=0.
    for q in samples:
        ff=frames(p,q);tg=target_fk(ref,q)
        for b,k in [('shoulder_base','S'),('elbow_base','E'),('wrist_base','W')]:worst=max(worst,float(np.linalg.norm(ff[b][:3,3]-tg[k])))
        for b,k in [('upper','upper_R'),('fore','fore_R'),('hand','hand_R')]:rotation_error=max(rotation_error,float(np.max(abs(ff[b][:3,:3]-tg[k]))))
        q2={**q,'forearm_roll':q.get('forearm_roll',0)+90}
        twist_drift=max(twist_drift,float(np.linalg.norm(frames(p,q2)['wrist_base'][:3,3]-ff['wrist_base'][:3,3])))
        s=ff['shoulder_base'][:3,3]
        for token,axis in [('shoulder_base',[0,1,0]),('shoulder_pitch',[1,0,0]),('shoulder_swing',[0,0,-1])]:
            o=ff[token][:3,3];d=ff[token][:3,:3]@axis
            shoulder_axis_error=max(shoulder_axis_error,float(np.linalg.norm(np.cross(s-o,d))))
        w=ff['wrist_base'][:3,3]
        for token in ['wrist_base','wrist_flex']:wrist_axis_error=max(wrist_axis_error,float(np.linalg.norm(w-ff[token][:3,3])))
    # Mutation sensitivity: wrong mechanical upper-arm length must fail against the same immutable target.
    perturbed={**p,'upperarm_mm':p['upperarm_mm']+1}
    mutation=float(np.linalg.norm(frames(perturbed)['elbow_base'][:3,3]-target_fk(ref,{})['E']))
    result=dict(samples=len(samples),seed=24,max_joint_center_error_mm=worst,max_rotation_matrix_element_error=rotation_error,
        shoulder_axes_to_center_max_mm=shoulder_axis_error,wrist_axes_to_center_max_mm=wrist_axis_error,
        forearm_twist_90deg_max_wrist_drift_mm=twist_drift,one_mm_length_mutation_detected=mutation>.99,
        target_source=ref['source_files'],status='PASS' if worst<1e-8 and rotation_error<1e-10 and twist_drift<1e-8 and mutation>.99 else 'FAIL',
        scope='Analytic kinematics and frozen UE-derived N pose; not measured hardware or runtime Control Rig execution.')
    put(OUT/'verification/kinematics.json',result);return result

def solid_pairs(A,p,q,threshold=.02):
    F=frames(p,q);parts=A.parts;world=[];bounds=[]
    for v in parts:
        s=moved(v['s'],F[v['frame']]);world.append(s);bounds.append(np.array(s.bounding_box()).reshape(2,3))
    bounds=np.array(bounds);hits=[]
    for i,a in enumerate(parts):
        for j in range(i+1,len(parts)):
            b=parts[j]
            # Rigidly joined solids on the same frame are not moving collision pairs.
            family=lambda x:{'shoulder_base':'collar','elbow_base':'upper','wrist_base':'fore'}.get(x,x)
            if family(a['frame'])==family(b['frame']):continue
            if np.any(bounds[i,1] <= bounds[j,0]+1e-5) or np.any(bounds[j,1] <= bounds[i,0]+1e-5):continue
            volume=(world[i]^world[j]).volume()
            if volume>threshold:hits.append(dict(a=a['name'],b=b['name'],frames=[a['frame'],b['frame']],volume_mm3=round(volume,5)))
    return hits

def collision(A,p,dense=False):
    cases={name:q for name,(_,q) in poses().items()}
    for name,_,limits,_ in AXES:
        for v in limits:cases[f'isolated/{name}/{v}']={name:v}
    for flex in [-65,70]:
        for dev in [-20,30]:cases[f'wrist_combined/{flex}/{dev}']=dict(elbow_flex=90,wrist_flex=flex,wrist_deviation=dev)
    if dense:
        # Each named path from neutral, at no more than 5 degrees per joint step.
        for name,q in list(cases.items()):
            n=max(1,int(math.ceil(max([abs(v) for v in q.values()] or [0])/5)))
            for i in range(1,n):cases[f'{name}/{i:03d}']={k:v*i/n for k,v in q.items()}
    start=time.time();rows=[]
    for name,q in cases.items():
        hits=solid_pairs(A,p,q);rows.append(dict(pose=name,angles=q,collisions=hits,count=len(hits)))
        print(name,len(hits),flush=True)
    result=dict(status='PASS' if not any(r['count'] for r in rows) else 'FAIL',samples=len(rows),seconds=time.time()-start,
                threshold_mm3=.02,geometry_sha256=sha(OUT/'assembly_meshes.npz') if (OUT/'assembly_meshes.npz').exists() else None,
                scope='All different-frame parts including PCB, connector and hardware envelopes; same-frame rigid contacts excluded. No flexible harness, tools, pressure calibration, full torso shell, or continuous proof.',cases=rows)
    put(OUT/'verification'/('motion_dense.json' if dense else 'motion_named.json'),result)
    summary={}
    for row in rows:
        for h in row['collisions']:
            key=h['a']+' / '+h['b'];entry=summary.setdefault(key,dict(count=0,max_volume_mm3=0,poses=[]));entry['count']+=1;entry['max_volume_mm3']=max(entry['max_volume_mm3'],h['volume_mm3']);entry['poses'].append(row['pose'])
    put(OUT/'verification/collision_pairs.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2)[:22000])
    return result

def exported_axes(p,ref):
    """Fit real exported annular meshes, rather than accepting declared origins."""
    data=json.loads((OUT/'assembly.json').read_text('utf8'));meshes=np.load(OUT/'assembly_meshes.npz')
    selected={
      'clavicle_z_bearing_17':('C',[0,0,1]),'clavicle_x_bearing_12':('C',[1,0,0]),
      'shoulder_pitch_bearing_-26':('S',[0,1,0]),'shoulder_swing_bearing_-16':('S',[1,0,0]),
      'humeral_bearing_15':('S',[0,0,-1]),'elbow_bearing_-1':('E',[0,1,0]),
      'forearm_bearing_31':('E',[0,0,-1]),'wrist_flex_bearing_-10':('W',[0,1,0]),
      'wrist_dev_bearing_-9':('W',[1,0,0])}
    rows=[]
    for part in data['parts']:
        if part['name'] not in selected:continue
        v=meshes[str(part['i'])+'v'];center=v.mean(0);w,U=np.linalg.eigh(np.cov(v.T))
        # The circular transverse directions have equal second moments; the third is the shaft axis.
        pairs=[(abs(w[i]-w[j]),i,j) for i,j in [(0,1),(0,2),(1,2)]]
        _,i,j=min(pairs);unique=({0,1,2}-{i,j}).pop();axis=U[:,unique]
        target,nominal=selected[part['name']];worst=0;ang=0
        for _,q in poses().values():
            F=frames(p,q);M=F[part['frame']];o=M[:3,:3]@center+M[:3,3];d=M[:3,:3]@axis;tg=target_fk(ref,q)[target]
            worst=max(worst,float(np.linalg.norm(np.cross(tg-o,d))))
            ang=max(ang,float(np.degrees(np.arccos(np.clip(abs(np.dot(axis,nominal)),-1,1)))))
        rows.append(dict(part=part['name'],fitted_center_local_mm=center,fitted_axis_local=axis,target=target,max_point_line_distance_mm=worst,max_axis_angle_deg=ang))
    result=dict(method='PCA fit to actual exported annular bearing vertices; unique covariance direction fitted independently of declared axis',
        components=len(rows),cases=len(poses()),geometry_sha256=sha(OUT/'assembly_meshes.npz'),
        status='PASS' if len(rows)==9 and max(r['max_point_line_distance_mm'] for r in rows)<1e-7 and max(r['max_axis_angle_deg'] for r in rows)<1e-5 else 'FAIL',rows=rows)
    put(OUT/'verification/exported_axes.json',result);return result

def mapping(p,ref):
    output={};errors=[];source={b['name']:b for b in ref['bone_reference']};swap=ue.SWAP
    for name,(_,q) in poses().items():
        tg=target_fk(ref,q);F=frames(p,q);bones={}
        for bone,key,R in [('clavicle_l','C',F['collar'][:3,:3]),('upperarm_l','S',tg['upper_R']),('lowerarm_l','E',tg['fore_R']),('hand_l','W',tg['hand_R'])]:
            Rworld=R@np.array(ref['neutral_rotations_RH'][bone]);Rue=swap.T@Rworld@swap
            Pue=swap.T@((tg[key]-np.array(ref['floor_shift_mm']))/(10*ref['uniform_scale']))
            bones[bone]=dict(position_cm=Pue,rotation_xyzw=Rotation.from_matrix(Rue).as_quat(),matrix=T(Pue,Rue))
        for parent,child in [('clavicle_l','upperarm_l'),('upperarm_l','lowerarm_l'),('lowerarm_l','hand_l')]:
            relative=np.linalg.inv(bones[parent]['matrix'])@bones[child]['matrix']
            errors.append(float(np.linalg.norm(relative[:3,3]-source[child]['local']['translation'])))
        output[name]={bone:{k:v for k,v in row.items() if k!='matrix'} for bone,row in bones.items()}
    put(OUT/'profiles/ue_component_pose_examples.json',dict(asset=ref['asset'],coordinate_system='UE original mesh local, cm, xyzw; full scale',runtime_integration_tested=False,poses=output))
    result=dict(status='PASS' if max(errors)<1e-8 else 'FAIL',pose_count=len(output),max_parent_child_translation_difference_from_actual_UE_asset_cm=max(errors),runtime_UE='NOT RUN')
    put(OUT/'verification/ue_transform_mapping.json',result);return result

def reach_check(p,ref):
    rows=[]
    for name,offset in [('drink',[25,12,10]),('head',[5,34,20])]:
        target=np.array(ref['points_mm']['head'])+offset
        hand=(frames(p,poses()[name][1])['hand']@np.array([0,0,-28,1]))[:3]
        rows.append(dict(pose=name,target_mm=target,hand_center_mm=hand,error_mm=float(np.linalg.norm(hand-target))))
    put(OUT/'verification/functional_reach.json',dict(status='PASS' if max(r['error_mm'] for r in rows)<.5 else 'FAIL',
       note='Head-relative task points, not independently identified anatomical mouth/ear landmarks. No cup or head-shell contact test.',rows=rows))

def holding_budget(p):
    data=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz')
    dens={'structure':.00124,'rotor':.00124,'metal':.00785,'bearing':.00785,'friction':.0014,'pcb':.002,'magnet':.0075,'connector':.0013}
    mass={};F=frames(p,{'shoulder_flex':90})
    groups={'shoulder_base':['shoulder_pitch','shoulder_swing','upper','elbow_base','elbow','fore','wrist_base','wrist_flex','hand'],
            'elbow_base':['elbow','fore','wrist_base','wrist_flex','hand'],'wrist_base':['wrist_flex','hand']}
    moments={k:np.zeros(3) for k in groups}
    for d in data['parts']:
        v=z[str(d['i'])+'v'];m=d['volume_mm3']*dens[d['role']];mass[d['role']]=mass.get(d['role'],0)+m
        # Vertex-centroid approximation is explicit: this is a sizing budget, not mass-property certification.
        M=F[d['frame']];center=M[:3,:3]@v.mean(0)+M[:3,3]
        for key,tokens in groups.items():
            if d['frame'] in tokens:moments[key]+=np.cross((center-F[key][:3,3])/1000,[0,0,-9.80665*m/1000])
    put(OUT/'verification/holding_budget.json',dict(method='Solid-volume material assumptions and mesh vertex-centroid approximation; rigid overlaps may double-count material; bearings simplified; cables and omitted hardware not included.',
      density_g_per_mm3=dens,mass_g_by_role=mass,total_geometric_mass_g=sum(mass.values()),horizontal_pose_gravity_Nm={k:float(np.linalg.norm(v)) for k,v in moments.items()},physical_hold_test='NOT RUN'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dense',action='store_true');parser.add_argument('--kinematics-only',action='store_true');args=parser.parse_args()
    ref,c,k=reference();p=profile(ref);print(kinematic(p,ref))
    print(exported_axes(p,ref)['status']);print(mapping(p,ref))
    reach_check(p,ref)
    holding_budget(p)
    if not args.kinematics_only:collision(build(p),p,args.dense)
