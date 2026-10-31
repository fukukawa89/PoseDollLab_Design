"""Checks actual exported solids, complete height, independent FK and finite motion.
No adjacent-body or bearing-contact pair is automatically exempted.
"""
from fullbody import *
import argparse,time
from adjacency import segment,required,EDGES
from scipy.spatial.transform import Rotation

def read_assembly():
    data=load(OUT/'assembly.json');z=np.load(OUT/'assembly_meshes.npz');parts=data['parts'];solids=[]
    for p in parts:
        i=str(p['i']);solids.append(md.Manifold(md.Mesh64(np.ascontiguousarray(z[i+'v']),np.ascontiguousarray(z[i+'f'],dtype=np.uint64))))
    return parts,z,solids

def family(n):
    while NODES[n]['axis'] is None and NODES[n]['parent']:n=NODES[n]['parent']
    return n

class Collision:
    def __init__(self,parts,solids):
        self.parts=parts;self.solids=solids;self.cache={};self.bools=0
        families=[family(p['frame']) for p in parts]
        self.all_mask=np.triu(np.array([[x!=y for y in families] for x in families]),1)
        self.mask=self.all_mask & np.array([[required(p['frame'],t['frame']) for t in parts] for p in parts])
    def check(self,q,scope='adjacent'):
        F=frames(q);w=[moved(s,F[p['frame']]) for p,s in zip(self.parts,self.solids)]
        b=np.array([s.bounding_box() for s in w]).reshape(-1,2,3)
        broad=(self.all_mask if scope=='all' else self.mask) & np.all(b[:,None,1]>b[None,:,0]+1e-6,2) & np.all(b[None,:,1]>b[:,None,0]+1e-6,2)
        hits=[]
        for i,j in zip(*np.where(broad)):
            pi,pj=self.parts[i],self.parts[j]
            rel=np.linalg.inv(F[pi['frame']])@F[pj['frame']]
            key=(int(i),int(j),np.round(rel,7).tobytes())
            if key not in self.cache:
                self.cache[key]=(self.solids[i]^moved(self.solids[j],rel)).volume();self.bools+=1
            v=self.cache[key]
            if v>.02:hits.append(dict(a=pi['name'],b=pj['name'],volume_mm3=round(v,5),segments=[segment(pi['frame']),segment(pj['frame'])],required_adjacent=required(pi['frame'],pj['frame'])))
        return hits

def collision(dense=False,neutral=False):
    parts,z,solids=read_assembly();engine=Collision(parts,solids);cases={n:p['angles'] for n,p in poses().items()}
    if neutral:cases={'neutral':dict(NEUTRAL_ANGLES)}
    if dense:
        for ax in PROFILE['axes']:
            for val in ax['limits_deg']:cases['boundary/'+ax['id']+'/'+str(val)]={ax['id']:val}
        for n,q in list(cases.items()):
            steps=max(1,math.ceil(max([abs(v) for v in q.values()] or [0])/5))
            for j in range(1,steps):cases[f'path/{n}/{j:03d}']={k:v*j/steps for k,v in q.items()}
    rows=[];summary={};start=time.time()
    for n,q in cases.items():
        allhits=engine.check(q,scope='all');hits=[h for h in allhits if h['required_adjacent']];advisory=[h for h in allhits if not h['required_adjacent']]
        rows.append(dict(pose=n,angles=q,count=len(hits),collisions=hits,advisory_count=len(advisory),nonadjacent_contacts=advisory))
        for h in hits:
            key=h['a']+' / '+h['b'];r=summary.setdefault(key,dict(count=0,max_volume_mm3=0,poses=[]));r['count']+=1;r['max_volume_mm3']=max(r['max_volume_mm3'],h['volume_mm3']);r['poses'].append(n)
        if len(rows)%25==0 or not dense:print(n,len(hits),flush=True)
    report=dict(status='PASS' if not summary else 'FAIL',samples=len(rows),threshold_mm3=.02,geometry_sha256=sha(OUT/'assembly_meshes.npz'),seconds=time.time()-start,boolean_tests=engine.bools,
       scope='Actual exported meshes: all moving parts within the same or adjacent anatomical segments are required, including intermediate gimbal stages, shells and hardware. Non-adjacent contacts are advisory under the explicit user instruction of 2026-10-23. Same rigid-body contact is excluded. Finite nominal samples, not a continuous-space proof.',cases=rows)
    tag='neutral' if neutral else ('dense' if dense else 'named')
    put(OUT/f'verification/motion_{tag}.json',report);put(OUT/f'verification/pairs_{tag}.json',summary)
    print(json.dumps(dict(status=report['status'],samples=len(rows),unique_pairs=len(summary),seconds=report['seconds']),ensure_ascii=False),flush=True)

def independent(q):
    """Vector recursion from immutable UE points. Does not use PROFILE nodes or FK."""
    def r(axis,angle):
        ax=np.array(axis,float);ax/=np.linalg.norm(ax);t=math.radians(angle);x,y,z=ax;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0.]])
        return np.eye(3)+np.sin(t)*K+(1-np.cos(t))*K@K
    get=lambda n:q.get(n,0)
    result={};targets={};rots={}
    Rl=r([0,1,0],get('lumbar_flex'))@r([-1,0,0],get('lumbar_side'))@r([0,0,1],get('lumbar_yaw'))
    lumbar=P['spine_02']; chest=lumbar+Rl@(P['spine_04']-lumbar)
    Rc=Rl@r([-1,0,0],get('thorax_side'))@r([0,1,0],get('thorax_flex'))
    neck=chest+Rc@(P['neck_01']-P['spine_04'])
    Rn=Rc@r([-1,0,0],get('neck_side'))@r([0,1,0],get('neck_flex'))@r([0,0,1],get('neck_yaw'))
    targets.update(lumbar_yaw=lumbar,thorax_flex=chest,neck_yaw=neck,head=neck+Rn@(P['head']-P['neck_01']))
    rots.update(lumbar_yaw=Rl,thorax_flex=Rc,neck_yaw=Rn,head=Rn)
    for side,s in [('l',1),('r',-1)]:
        pre=side+'_';Q=lambda n:get(pre+n)
        C=chest+Rc@(P['clavicle_'+side]-P['spine_04'])
        Rcl=Rc@r([0,0,-s],Q('clavicle_protract'))@r([s,0,0],Q('clavicle_elevate'))
        S=C+Rcl@(P['upperarm_'+side]-P['clavicle_'+side])
        Ru=Rcl@r([0,-1,0],Q('shoulder_flex'))@r([s,0,0],Q('shoulder_abduct'))@r([0,0,-s],Q('upperarm_roll'))
        E=S+Ru@(P['lowerarm_'+side]-P['upperarm_'+side])
        Re=Ru@r([0,-1,0],Q('elbow_flex'));Rf=Re@r([0,0,-s],Q('forearm_roll')-90)
        W=E+Re@(P['hand_'+side]-P['lowerarm_'+side]);Rh=Rf@r([s,0,0],Q('wrist_deviation'))@r([0,1,0],Q('wrist_flex'))
        targets.update({pre+'clavicle_elevate':C,pre+'upperarm_roll':S,pre+'elbow_flex':E,pre+'wrist_flex':W})
        rots.update({pre+'clavicle_elevate':Rcl,pre+'upperarm_roll':Ru,pre+'forearm_roll':Rf,pre+'wrist_flex':Rh})
        Hh=P['thigh_'+side];Rt=r([s,0,0],Q('hip_abduct'))@r([0,-1,0],Q('hip_flex'))@r([0,0,-s],Q('hip_roll'))
        K=Hh+Rt@(P['calf_'+side]-Hh);Rk=Rt@r([0,1,0],Q('knee_flex'));A=K+Rk@(P['foot_'+side]-P['calf_'+side])
        Ra=Rk@r([s,0,0],Q('ankle_roll'))@r([0,-1,0],Q('ankle_flex'));B=A+Ra@(P['ball_'+side]-P['foot_'+side]);Rb=Ra@r([0,-1,0],Q('toe_flex'))
        targets.update({pre+'hip_roll':Hh,pre+'knee_flex':K,pre+'ankle_flex':A,pre+'toe_flex':B})
        rots.update({pre+'hip_roll':Rt,pre+'knee_flex':Rk,pre+'ankle_flex':Ra,pre+'toe_flex':Rb})
    return targets,rots

def checks():
    parts,z,solids=read_assembly();rng=np.random.default_rng(2404);sample=[p['angles'] for p in poses().values()]
    sample.extend({ax['id']:float(rng.uniform(*ax['limits_deg'])) for ax in PROFILE['axes']} for _ in range(1000))
    pe=re=0
    for q in sample:
        target,rr=independent(q);F=frames(q)
        pe=max(pe,max(np.linalg.norm(F[n][:3,3]-v) for n,v in target.items()))
        re=max(re,max(np.max(abs(F[n][:3,:3]-v)) for n,v in rr.items()))
    bad=copy.deepcopy(PROFILE)
    next(n for n in bad['nodes'] if n['id']=='l_elbow_flex')['offset_mm'][2]-=1
    mutation=np.linalg.norm(frames({},bad)['l_elbow_flex'][:3,3]-independent({})[0]['l_elbow_flex'])
    put(OUT/'verification/kinematics.json',dict(status='PASS' if pe<1e-7 and re<1e-10 and mutation>.999 else 'FAIL',samples=len(sample),seed=2404,max_center_error_mm=pe,max_rotation_element_error=re,one_mm_bone_length_mutation_detected=mutation>.999,mutation_error_mm=mutation,scope='Independent analytic FK against frozen UE positions; not hardware accuracy or runtime UE execution'))
    # Global full model height and mass use exported vertices and volume centroids.
    world=[];density={'structure':.00124,'rotor':.00124,'shell':.00124,'friction':.00785,'metal':.00785,'bearing':.00785,'pcb':.002,'magnet':.0075,'connector':.0013}
    masses=[]
    for p in parts:
        v=z[str(p['i'])+'v'];F=FA[p['frame']];world.append(v@F[:3,:3].T+F[:3,3]);masses.append(p['volume_mm3']*p.get('density_g_mm3',density[p['role']]))
    v=np.vstack(world);lo=v.min(0);hi=v.max(0)
    put(OUT/'verification/envelope.json',dict(status='PASS' if hi[2]-lo[2]<600 else 'FAIL',pose='A neutral',angles_deg=NEUTRAL_ANGLES,bounds_mm=[lo,hi],size_mm=hi-lo,height_mm=hi[2]-lo[2],margin_to_600_mm=600-hi[2]+lo[2],head_and_feet_and_all_delivered_shells_included=True,external_fixture_excluded=True,geometry_sha256=sha(OUT/'assembly_meshes.npz')))
    put(OUT/'verification/mass_initial.json',dict(mass_g=sum(masses),density_g_mm3=density,method='Exported solid volume. Metal and bearing envelope is conservative solid material; same-body overlaps may overcount; cable/electronics allowance handled separately. Not measured.'))
    # Fit unique covariance axes of actual annular bearing vertices.
    fitted=[]
    for p in parts:
        if p['role']!='bearing':continue
        vv=z[str(p['i'])+'v'];mean=vv.mean(0);ev,U=np.linalg.eigh(np.cov(vv.T));_,ii,jj=min((abs(ev[i]-ev[j]),i,j) for i,j in [(0,1),(0,2),(1,2)]);d=U[:,({0,1,2}-{ii,jj}).pop()]
        m=F0[p['frame']];point=m[:3,:3]@mean+m[:3,3];axis=m[:3,:3]@d
        name=p['name'];target=None
        if name[0:2] in ['l_','r_']:
            side=name[0]
            if '_clavicle_' in name:target=P['clavicle_'+side]
            elif name[2:].startswith(('shoulder','humeral')):target=P['upperarm_'+side]
            elif name[2:].startswith(('elbow','forearm')):target=P['lowerarm_'+side]
            elif name[2:].startswith('hip_'):target=P['thigh_'+side]
            elif name[2:].startswith('knee_'):target=P['calf_'+side]
            elif name[2:].startswith('ankle_'):target=P['foot_'+side]
            elif name[2:].startswith('toe_'):target=P['ball_'+side]
        else:
            for pre,bone in [('lumbar','spine_02'),('thorax','spine_04'),('neck','neck_01')]:
                if name.startswith(pre+'_'):target=P[bone]
        if target is not None:fitted.append(dict(part=name,axis_world=axis,fitted_origin_mm=point,target_mm=target,point_line_error_mm=float(np.linalg.norm(np.cross(target-point,axis)))))
    put(OUT/'verification/exported_axes.json',dict(status='PASS' if fitted and max(r['point_line_error_mm'] for r in fitted)<1e-6 else 'FAIL',fitted_bearings=len(fitted),max_center_error_mm=max(r['point_line_error_mm'] for r in fitted),rows=fitted,geometry_sha256=sha(OUT/'assembly_meshes.npz'),note='PCA on exported annular bearings. Spherical wrist centre fit and motion-frame audit are separate checks.'))
    print(json.dumps(dict(kinematics=load(OUT/'verification/kinematics.json')['status'],height_mm=hi[2]-lo[2],mass_g=sum(masses),axis_error_mm=max(r['point_line_error_mm'] for r in fitted)),ensure_ascii=False))

if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('--dense',action='store_true');arg.add_argument('--neutral',action='store_true');arg.add_argument('--checks',action='store_true');opts=arg.parse_args()
    if opts.checks:checks()
    else:collision(opts.dense,opts.neutral)
