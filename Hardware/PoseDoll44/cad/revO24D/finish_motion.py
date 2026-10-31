"""Reproducible clearance posture and functional-pose search; no joint offsets."""
from validate import *
from scipy.optimize import least_squares

def main():
    parts,z,solids=read_assembly();e=Collision(parts,solids);out=load(HERE/'daily_poses.json');results={}
    for side in ([] if '--cross' in sys.argv else ['l','r']):
        for axis,values in [('shoulder_flex',range(-45,176,5)),('elbow_flex',range(0,146,5))]:
            for opening in [5,8,10,12,15]:
                fails=[]
                for v in values:
                    q={side+'_'+axis:v,side+'_shoulder_abduct':opening};hits=e.check(q)
                    if hits:fails.append((v,len(hits)))
                print('CLEARANCE',side,axis,opening,fails,flush=True)
                if not fails:results[side+'_'+axis]=opening;break
    for name,updates in [
        ('bend',dict(l_shoulder_flex=30,r_shoulder_flex=30,l_elbow_flex=20,r_elbow_flex=20)),
        ('step',dict(l_shoulder_abduct=10,r_shoulder_abduct=10)),
        ('kneel',dict(r_hip_flex=0,r_knee_flex=95,r_ankle_flex=-20,l_shoulder_flex=60,r_shoulder_flex=60,l_elbow_flex=25,r_elbow_flex=25))]:
        p=copy.deepcopy(poses()[name]);p['angles'].update(updates);hits=e.check(p['angles']);print('DAILY',name,len(hits),hits[:4],flush=True)
        if not hits:out[name]=p
    name='cross';ids=[s+'_'+v for s in ['l','r'] for v in ['shoulder_flex','shoulder_abduct','upperarm_roll','elbow_flex','forearm_roll','wrist_flex','wrist_deviation']]
    lim=np.array([next(a['limits_deg'] for a in PROFILE['axes'] if a['id']==v) for v in ids]);seed=np.array([poses()[name]['angles'].get(v,0) for v in ids]);rng=np.random.default_rng(242410)
    best=1e20
    for trial in range(160):
        targets=[[rng.uniform(60,95),rng.uniform(-35,-15),rng.uniform(395,435)],[rng.uniform(65,100),rng.uniform(15,35),rng.uniform(420,460)]]
        def residual(v):
            F=frames(dict(zip(ids,v)));errs=[]
            for s,target in zip(['l','r'],targets):
                m=F[s+'_wrist_flex'];errs.extend(m[:3,:3]@np.array([0,0,-36])+m[:3,3]-target)
            return np.r_[errs,.03*(v-seed)]
        opt=least_squares(residual,np.clip(seed+rng.normal(0,8,len(seed)),lim[:,0]+.01,lim[:,1]-.01),bounds=(lim[:,0],lim[:,1]),max_nfev=100)
        q={k:float(v) for k,v in zip(ids,opt.x)};hits=e.check(q);score=sum(h['volume_mm3'] for h in hits)
        if score<best:
            best=score;print('CROSS',trial,score,len(hits),hits[:4],flush=True);put(HERE/'cross_proposal.json',dict(angles=q,targets=targets,collisions=hits))
        if not hits:
            out[name]=dict(label='双臂胸前交叉',angles=q);results['cross_targets_mm']=targets;results['cross_target_error_mm']=float(np.linalg.norm(residual(opt.x)[:6]));break
    put(HERE/'daily_poses.json',out);put(HERE/'motion_layout.json',results)
    put(OUT/'profiles/poses.json',poses());put(OUT/'profiles/pose_frames.json',{n:frames(p['angles']) for n,p in poses().items()})
if __name__=='__main__':main()
