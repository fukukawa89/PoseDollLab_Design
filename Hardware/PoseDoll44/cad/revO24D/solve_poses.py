"""Coordinate full-body tasks, then check their actual exported solids."""
from validate import *
from scipy.optimize import least_squares

def main():
    base=poses(); overrides={};parts,z,solids=read_assembly();engine=Collision(parts,solids)
    def add(n,updates,label=None):
        p=copy.deepcopy(base[n]);p['angles'].update(updates)
        if label:p['label']=label
        overrides[n]=p
    add('arms_overhead_front',dict(l_shoulder_abduct=18,r_shoulder_abduct=18))
    add('arms_shrug',dict(l_clavicle_protract=20,r_clavicle_protract=20), '双臂 · 抬肩并前伸肩带')
    add('turn',dict(l_shoulder_flex=35,r_shoulder_flex=35,l_elbow_flex=25,r_elbow_flex=25))
    add('squat',dict(l_shoulder_flex=80,r_shoulder_flex=80,l_elbow_flex=20,r_elbow_flex=20))
    add('step',dict(l_shoulder_flex=-5,l_elbow_flex=35,r_elbow_flex=20))
    add('kneel',dict(l_shoulder_flex=25,r_shoulder_flex=25,l_elbow_flex=30,r_elbow_flex=30))
    add('cross',dict(l_shoulder_flex=60,r_shoulder_flex=82,l_elbow_flex=100,r_elbow_flex=110,l_upperarm_roll=55,r_upperarm_roll=50,l_shoulder_abduct=-5,r_shoulder_abduct=-5))
    targets={};rng=np.random.default_rng(24040)
    for name,side,target in [('arms_drink','l',[31,11,520]),('arms_head','l',[2,43,526]),('arms_head','r',[2,-43,526])]:
        ids=[side+'_'+a for a in ['shoulder_flex','shoulder_abduct','upperarm_roll','elbow_flex','forearm_roll','wrist_flex','wrist_deviation']]
        seed=np.array([base[name]['angles'].get(n,0) for n in ids]);lims=np.array([next(a['limits_deg'] for a in PROFILE['axes'] if a['id']==n) for n in ids])
        fixed={side+'_clavicle_elevate':10,side+'_clavicle_protract':5}
        def residual(v):
            q={**fixed,**dict(zip(ids,v))};F=frames(q)[side+'_wrist_flex'];p=F[:3,:3]@np.array([0,0,-36])+F[:3,3]
            return np.r_[(p-target),.035*(v-seed)]
        opt=least_squares(residual,seed,bounds=(lims[:,0],lims[:,1]),max_nfev=150)
        q={**fixed,**{k:float(v) for k,v in zip(ids,opt.x)}}
        if name not in overrides:overrides[name]=dict(label='左手靠近口部' if name=='arms_drink' else '双手靠近头侧',angles={})
        overrides[name]['angles'].update(q);targets.setdefault(name,{})[side]=dict(palm_center_target_mm=target,residual_mm=float(np.linalg.norm(residual(opt.x)[:3])))
    for n,p in overrides.items():
        hits=engine.check(p['angles']);print(n,len(hits),flush=True)
        if hits:print(json.dumps(hits,ensure_ascii=False),flush=True)
    put(HERE/'daily_poses.json',overrides);put(OUT/'verification/reach_targets.json',dict(method='Position IK for physical palm centre (local 0,0,-36), regularized to C seeds. Does not define a collision result.',targets=targets))
    # Update only pose outputs, not an independent geometry regeneration.
    put(OUT/'profiles/poses.json',poses());put(OUT/'profiles/pose_frames.json',{n:frames(p['angles']) for n,p in poses().items()})
if __name__=='__main__':main()
