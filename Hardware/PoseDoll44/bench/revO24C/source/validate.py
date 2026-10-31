"""Actual exported meshes, independent UE FK, and finite rigid collision audit."""
from compact_arm import *
import argparse,time
import verify as V
original_target=V.target_fk

def target(ref,q):
    t=original_target(ref,q)
    # Independent Rodrigues FK supplies the proximal chain; B wrist order differs from A.
    d=math.radians(q.get('wrist_deviation',0));f=math.radians(q.get('wrist_flex',0))
    Rx=np.array([[1,0,0],[0,math.cos(d),-math.sin(d)],[0,math.sin(d),math.cos(d)]])
    Ry=np.array([[math.cos(f),0,math.sin(f)],[0,1,0],[-math.sin(f),0,math.cos(f)]])
    t['hand_R']=t['fore_R']@Rx@Ry
    return t

def compatible_frames(p,q=None):
    f=frames(p,q);f['hand']=f['hand_ball'];return f
V.OUT=OUT;V.frames=compatible_frames;V.target_fk=target;V.poses=poses

def exported():
    A=a.Assembly();z=np.load(OUT/'assembly_meshes.npz')
    for p in load(OUT/'assembly.json')['parts']:
        i=str(p['i']);A.add(p['name'],p['frame'],md.Manifold(md.Mesh64(np.ascontiguousarray(z[i+'v']),np.ascontiguousarray(z[i+'f'],dtype=np.uint64))),p['role'],p['notes'])
    return A

def cases(dense):
    result={n:q for n,(_,q) in poses().items()}
    for axis,_,limits,_ in a.AXES:
        for val in limits:result[f'isolated/{axis}/{val}']={axis:val}
    for flex in [-65,70]:
        for dev in [-20,30]:result[f'wrist_corner/{flex}/{dev}']=dict(elbow_flex=90,wrist_flex=flex,wrist_deviation=dev)
    if dense:
        for name,q in list(result.items()):
            n=max(1,math.ceil(max([abs(v) for v in q.values()] or [0])/5))
            for k in range(1,n):result[f'path/{name}/{k}']={j:v*k/n for j,v in q.items()}
        for f in np.arange(-65,71,5):
            for d in np.arange(-20,31,5):result[f'wrist_grid/{f}/{d}']=dict(elbow_flex=90,wrist_flex=float(f),wrist_deviation=float(d))
        for e in [0,90,120,145]:
            for r in [-85,0,80]:
                for f,d in [(0,0),(-65,-20),(-65,30),(70,-20),(70,30)]:
                    result[f'fold_twist_wrist/{e}/{r}/{f}/{d}']=dict(elbow_flex=e,forearm_roll=r,wrist_flex=f,wrist_deviation=d)
    else:
        for r in [-85,80]:result[f'fold_twist/145/{r}']=dict(elbow_flex=145,forearm_roll=r)
    return result

def collision(A,p,dense):
    start=time.time();rows=[]
    for n,q in cases(dense).items():
        hits=V.solid_pairs(A,p,q);rows.append(dict(pose=n,angles=q,count=len(hits),collisions=hits))
        if hits:print(n,json.dumps(hits),flush=True)
    out=dict(status='FAIL' if any(r['count'] for r in rows) else 'PASS',samples=len(rows),seconds=time.time()-start,
        geometry_sha256=sha(OUT/'assembly_meshes.npz'),threshold_mm3=.02,
        scope='All pairs on different rigid frames; no adjacent-joint exemptions. Finite nominal rigid mesh samples incl. electronics. Excludes harness, tools, full body, preload deformation and a continuous-space proof.',cases=rows)
    put(OUT/'verification'/('motion_dense.json' if dense else 'motion_quick.json'),out)
    print(json.dumps({k:v for k,v in out.items() if k!='cases'}),flush=True)
    return out

def axes(p,ref):
    data=load(OUT/'assembly.json')['parts'];z=np.load(OUT/'assembly_meshes.npz')
    names={'clavicle_z_bearing_17':('C',[0,0,1]),'clavicle_x_bearing_12':('C',[1,0,0]),'shoulder_pitch_bearing_-26':('S',[0,1,0]),'shoulder_swing_bearing_-16':('S',[1,0,0]),'humeral_bearing_15':('S',[0,0,-1]),'elbow_bearing_-1':('E',[0,1,0]),'forearm_bearing_31':('E',[0,0,-1])}
    rows=[]
    for part in data:
        if part['name'] not in names:continue
        verts=z[str(part['i'])+'v'];o=verts.mean(0);w,U=np.linalg.eigh(np.cov(verts.T))
        _,i,j=min((abs(w[i]-w[j]),i,j) for i,j in [(0,1),(0,2),(1,2)]);axis=U[:,({0,1,2}-{i,j}).pop()]
        name,nominal=names[part['name']];errors=[]
        for _,q in poses().values():
            m=frames(p,q)[part['frame']];x=m[:3,:3]@o+m[:3,3];d=m[:3,:3]@axis
            errors.append(np.linalg.norm(np.cross(target(ref,q)[name]-x,d)))
        rows.append(dict(part=part['name'],fitted_axis=axis,max_center_to_axis_mm=max(errors),axis_dot_error=1-abs(np.dot(axis,nominal))))
    ball=next(r for r in data if r['name']=='C_ball_and_centered_neck');v=z[str(ball['i'])+'v'];vv=v[abs(np.linalg.norm(v,axis=1)-CONFIG['ball_radius_mm'])<1e-5]
    fit=np.linalg.lstsq(np.c_[2*vv,np.ones(len(vv))],np.sum(vv*vv,axis=1),rcond=None)[0];center=fit[:3];max_ball=0.
    for _,q in poses().values():
        m=frames(p,q)['hand_ball'];max_ball=max(max_ball,float(np.linalg.norm(m[:3,:3]@center+m[:3,3]-target(ref,q)['W'])))
    ok=len(rows)==7 and max(r['max_center_to_axis_mm'] for r in rows)<1e-7 and max(r['axis_dot_error'] for r in rows)<1e-8 and max_ball<1e-7
    result=dict(status='PASS' if ok else 'FAIL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),bearing_axes=rows,ball_center_fit_mm=center,ball_vertices=len(vv),max_ball_center_to_UE_mm=max_ball,method='PCA on actual exported bearings; least-squares sphere fit to actual ball surface vertices. Float arithmetic, not measured accuracy.')
    put(OUT/'verification/exported_axes.json',result)

def comparison(p):
    out={}
    for name,folder in [('O24A',OLD),('O24B',BASE_B),('O24C',OUT)]:
        data=load(folder/'assembly.json')['parts'];z=np.load(folder/'assembly_meshes.npz');F=frames(p);out[name]={}
        groups={'shoulder':[r for r in data if r['name'].startswith(('shoulder_','humeral_'))],
                'elbow':[r for r in data if r['name'].startswith('elbow_')],
                'wrist':[r for r in data if r['name'].startswith(('wrist_','B_','C_')) and 'hand_handle' not in r['name']]}
        for group,parts in groups.items():
            anchor={'shoulder':'shoulder_base','elbow':'elbow_base','wrist':'wrist_base'}[group];v=[]
            for part in parts:
                m=np.linalg.inv(F[anchor])@F[part['frame']];verts=z[str(part['i'])+'v'];v.append(verts@m[:3,:3].T+m[:3,3])
            v=np.vstack(v);size=np.ptp(v,axis=0)
            out[name][group]=dict(min_mm=v.min(0),max_mm=v.max(0),size_mm=size,box_volume_mm3=float(np.prod(size)),parts=len(parts))
    changes={group:{dim:(out['O24C'][group][dim]/out['O24B'][group][dim]-1)*100 for dim in ['box_volume_mm3']} for group in ['shoulder','elbow','wrist']}
    put(OUT/'verification/comparison.json',dict(status='PASS',frame='Neutral local shoulder/elbow/wrist coordinates; sensors and fastener envelopes included, palm excluded from wrist. Box volume is neither material volume nor swept volume.',revisions=out,change_from_B_percent=changes))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true');parser.add_argument('--analysis-only',action='store_true');args=parser.parse_args()
    p=load(OUT/'profiles/arm_profile.json');ref=load(OUT/'reference/target_quinn.json')
    if not args.analysis_only:collision(exported(),p,not args.quick)
    if not args.quick:
        print('kinematics',V.kinematic(p,ref)['status']);axes(p,ref);V.mapping(p,ref);V.reach_check(p,ref);comparison(p)
    freeze_baselines()

if __name__=='__main__':main()
