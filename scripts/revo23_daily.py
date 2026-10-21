"""Explicit ordinary-use poses and anatomical adjacency for O23D.

These are engineering review targets, not a claim about population ROM.
The original raw limits/protocol remain unchanged. Impossible solver targets
are reported, never silently replaced with an easier pose.
"""
from build_revo23 import *
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import shutil

C_HISTORY=B/'history/O23C_before_continuous_walls_20261020'
C_HASH='fd65aa05c1c60feb4ba8f53aabccba061c95a59778b330a16e73e724f0e1b5c3'


def archive_c():
    if not (C_HISTORY/'assembly.npz').exists():
        assert sha(B/'assembly.npz')==C_HASH
        for rel in ('assembly.npz','assembly.json','retained_interfaces.npz',
                    'profiles','design','verification','images','DELIVERY.json',
                    'DESIGN.zh-CN.md','review_stl','review_3mf'):
            src=B/rel;dst=C_HISTORY/rel
            if not src.exists():continue
            dst.parent.mkdir(parents=True,exist_ok=True)
            if src.is_dir():shutil.copytree(src,dst)
            else:shutil.copy2(src,dst)
        shutil.copy2(CFG,C_HISTORY/'parameters.json')
    assert sha(C_HISTORY/'assembly.npz')==C_HASH


def anatomical_body(item):
    name=item['body'].split('/')[0].split('.')[0]
    # Collar mechanisms belong to the anatomical shoulder girdle/chest.
    # Otherwise extra mechanical frames would incorrectly make upper arm and
    # chest appear nonadjacent even though they meet at the shoulder.
    if name.startswith('clavicle_'):name='chest'
    if name.startswith('elbow_'):name=name.replace('elbow_','forearm_')
    if name.startswith('ball_'):name=name.replace('ball_','foot_')
    return name


def anatomical_edges(p):
    edges=set()
    for j in p['joints']:
        a=anatomical_body({'body':j['parent']})
        b=anatomical_body({'body':j['child']})
        edges.add(frozenset((a,b)))
    return edges


def adjacent(a,b,p,edges=None):
    x,y=anatomical_body(a),anatomical_body(b)
    return x==y or frozenset((x,y)) in (edges if edges is not None else anatomical_edges(p))


def joint_rotation(j,x):
    kind=j['kind']
    if kind in ('tut','wide_tut'):Q=kin.b.b.L.tut.frames(x)['D']
    elif kind=='three_axis':Q=kin.b.b.L.three_axis.frames(x)['C02']
    elif kind=='hinge':Q=kin.b.b.rot(2,x[0])
    elif kind=='ankle_core':Q=kin.b.b.rot(1,-x[1])@kin.b.b.rot(0,x[0])
    else:raise ValueError(kind)
    return np.array(j['parent_to_mount_mm'])[:3,:3]@Q@np.array(j['rotor_to_child_mm'])[:3,:3]


def make_daily(p):
    neutral=p['neutral_raw_deg'];ff=kin.forward(p,neutral);joints={j['id']:j for j in p['joints']}
    result={};definitions=[];solutions=[]
    def save(name,q,group,target):
        assert all(p['raw_limits_deg'][k][0]-1e-6<=v<=p['raw_limits_deg'][k][1]+1e-6 for k,v in q.items())
        result[name]=q;definitions.append(dict(name=name,group=group,target=target,acceptance='adjacent_required_nonadjacent_advisory'))
    save('A_STAND_35',read(B/'profiles/default_pose.json')['raw_deg'],'basic','A stand')
    save('N_NEUTRAL',dict(neutral),'basic','Arms alongside trunk; nonadjacent contact is advisory')
    for label in ('left_elbow','asymmetric','right_forearm'):
        save(label,read(H/'bench/revO22/ue'/f'{label}.payload.json')['joint_angles_deg'],'basic','Retained named demonstration')

    def solve(jid,axis,angle,seed=None):
        j=joints[jid];raw=j['raw_ids'];a=ff[j['parent']][:3,:3];c=ff[j['child']][:3,:3]
        target=a.T@kin.b.b.rot(axis,angle)@c
        x0=np.array([neutral[k] for k in raw]) if seed is None else np.array(seed)
        limits=np.array([p['raw_limits_deg'][k] for k in raw]);x0=np.clip(x0,limits[:,0]+1e-7,limits[:,1]-1e-7)
        def residual(x):
            # Tiny redundancy regularizer preserves the nearest continuous branch.
            return np.r_[Rotation.from_matrix(target.T@joint_rotation(j,x)).as_rotvec(),(x-x0)*1e-7]
        def fit(start):
            fit=least_squares(residual,np.clip(start,limits[:,0]+1e-7,limits[:,1]-1e-7),
                bounds=(limits[:,0],limits[:,1]),xtol=1e-11,ftol=1e-11,gtol=1e-11,max_nfev=350)
            err=np.rad2deg(np.linalg.norm(Rotation.from_matrix(target.T@joint_rotation(j,fit.x)).as_rotvec()))
            return err,fit
        error,opt=fit(x0)
        if error>.05:
            rng=np.random.default_rng(230105)
            alternatives=[fit(np.array([neutral[k] for k in raw]))]
            alternatives.extend(fit(rng.uniform(limits[:,0],limits[:,1])) for _ in range(16))
            feasible=[v for v in alternatives if v[0]<.05]
            error,opt=min(feasible,key=lambda v:np.linalg.norm(v[1].x-x0)) if feasible else min(alternatives,key=lambda v:v[0])
        solutions.append(dict(joint=jid,world_axis=axis,target_deg=angle,error_deg=error,raw_deg=dict(zip(raw,opt.x))))
        if error>.05:raise RuntimeError(('unreachable ordinary-use target',solutions[-1]))
        return dict(zip(raw,map(float,opt.x)))

    def sweep(jid,label,axis,angles):
        # Approach each side from zero; do not jump to an unrelated inverse branch.
        samples=sorted(set(float(v) for v in angles))
        byangle={}
        for seq in ([v for v in samples if v>=0],sorted([v for v in samples if v<0],reverse=True)):
            seed=None
            for angle in seq:
                vals=solve(jid,axis,angle,seed);seed=list(vals.values());byangle[angle]=vals
        for angle in samples:
            q=dict(neutral);q.update(byangle[angle])
            save(f'{jid}.{label}@{angle:g}',q,jid,dict(world_rotation_axis=axis,relative_to_neutral_deg=angle))

    def raw_sweep(jid,label,raw,angles):
        for angle in angles:
            q=dict(neutral);q[raw]=float(angle)
            save(f'{jid}.{label}@{angle:g}',q,jid,dict(raw_axis=raw,angle_deg=angle))

    for side,sign in [('l',1),('r',-1)]:
        sweep('upperarm_'+side,'forward_raise',1,-np.arange(0,121,15))
        sweep('upperarm_'+side,'side_raise',0,sign*np.arange(0,91,15))
        sweep('upperarm_'+side,'axial_turn',2,np.arange(-45,46,15))
        sweep('thigh_'+side,'hip_flexion',1,-np.arange(-15,91,15))
        sweep('thigh_'+side,'hip_abduction',0,sign*np.arange(0,36,7))
        sweep('thigh_'+side,'hip_turn',2,np.arange(-30,31,15))
        for prefix,end,step in [('elbow_',130,10),('calf_',120,10)]:
            jid=prefix+side+'.flex';raw_sweep(jid,'flexion',jid+'/r0',range(0,end+1,step))
        jid='forearm_'+side+'.twist';raw_sweep(jid,'twist',jid+'/r0',range(-80,81,10))
        for word,end,step in [('flex',45,9),('deviate',20,5)]:
            raw_sweep('wrist_'+side,word,f'hand_{side}.{word}/r0',range(-end,end+1,step))
        raw_sweep('foot_'+side,'roll','foot_'+side+'/r0',range(-15,16,5))
        raw_sweep('foot_'+side,'pitch','foot_'+side+'/r1',range(-25,26,5))
        jid='ball_'+side+'.flex';raw_sweep(jid,'toe',jid+'/r0',range(0,46,5))
        for word in ('protract','elevate'):
            jid=f'clavicle_{side}.{word}';raw_sweep(jid,word,jid+'/r0',range(-15,16,5))
    for jid,targets in [('waist',[(2,-30,30),(1,-15,30),(0,-20,20)]),
                        ('chest',[(2,-20,20),(1,-15,20),(0,-15,15)]),
                        ('head',[(2,-60,60),(1,-25,30),(0,-20,20)])]:
        for axis,lo,hi in targets:
            sweep(jid,['side_bend','bend','turn'][axis],axis,np.linspace(lo,hi,int((hi-lo)/5)+1))

    for label,hip,knee,elbow,raise_angle in [('seated',90,90,90,0),('reach_front',0,0,20,90),('carry_front',0,0,90,30),('shallow_squat',45,80,40,45)]:
        q=dict(neutral)
        for side in ('l','r'):
            q.update(solve('thigh_'+side,1,-hip));q['calf_'+side+'.flex/r0']=knee
            q.update(solve('upperarm_'+side,1,-raise_angle));q['elbow_'+side+'.flex/r0']=elbow
        save('daily_'+label,q,'combined',label)
    q=dict(neutral)
    for side,angle,knee in [('l',30,15),('r',-15,40)]:
        q.update(solve('thigh_'+side,1,-angle));q['calf_'+side+'.flex/r0']=knee
    save('daily_step',q,'combined','One forward and one rear leg')
    return result,dict(policy_id='O23D-ordinary-adjacent-v1',pose_count=len(result),poses=definitions,
                       inverse_orientation_checks=solutions,maximum_solver_error_deg=max(x['error_deg'] for x in solutions),
                       note='Engineering review targets, not medical ROM. Raw limit table unchanged. No random all-axis extrema gate.')


def rigid_groups(p,tokens):
    """Numerically identify exact rigid attachments, including frame/joint aliases."""
    rng=np.random.default_rng(231004);q0=p['neutral_raw_deg'];F0=frames(p,q0)
    samples=[frames(p,{k:float(rng.uniform(*v)) for k,v in p['raw_limits_deg'].items()}) for _ in range(5)]
    signatures={}
    for t in sorted(tokens,key=lambda t:(not t.startswith('f:'),t)):
        sig=tuple(np.round(np.concatenate([(F[t]@np.linalg.inv(F0[t])).ravel() for F in samples]),7))
        signatures.setdefault(sig,[]).append(t)
    return {t:group[0] for group in signatures.values() for t in group}


if __name__=='__main__':
    archive_c()
    p=read(B/'profiles/device_profile.json');poses,report=make_daily(p)
    put(B/'profiles/daily_poses.json',dict(profile_sha256=sha(B/'profiles/device_profile.json'),poses=poses,policy=report))
    print('DAILY',len(poses),'max IK error',report['maximum_solver_error_deg'],flush=True)
