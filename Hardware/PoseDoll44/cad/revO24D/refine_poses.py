from validate import *
from scipy.optimize import least_squares

def main():
    pp=poses();parts,z,solids=read_assembly();e=Collision(parts,solids);out=load(HERE/'daily_poses.json');rng=np.random.default_rng(10424)
    for n in ['arms_shrug','squat']:
        base=pp[n]['angles'];best=(1e20,None,None)
        choices=([(l,r) for l in [-20,-15,-10,-5,0,5,10,15,20] for r in [-20,-10,0,10,20]] if n=='arms_shrug' else [(l,r) for l in [0,3,6,18,22,28,35] for r in [0,3,6,18,22,28,35]])
        for l,r in choices:
            axis='clavicle_protract' if n=='arms_shrug' else 'hip_abduct';q={**base,'l_'+axis:l,'r_'+axis:r};hits=e.check(q);score=sum(h['volume_mm3'] for h in hits)
            if score<best[0]:best=(score,q,hits)
            if not hits:break
        out[n]['angles']=best[1];print(n,best[0],best[2],flush=True)
    n='cross';best=(1e20,None,None);ids=[s+'_'+v for s in ['l','r'] for v in ['shoulder_flex','shoulder_abduct','upperarm_roll','elbow_flex','forearm_roll','wrist_flex','wrist_deviation']]
    lim=np.array([next(a['limits_deg'] for a in PROFILE['axes'] if a['id']==v) for v in ids]);seed=np.array([pp[n]['angles'].get(v,0) for v in ids])
    for trial in range(80):
        targets=[[32+rng.uniform(-5,18),-42+rng.uniform(-8,8),420+rng.uniform(-4,12)],[48+rng.uniform(0,18),42+rng.uniform(-8,8),375+rng.uniform(-10,10)]]
        def residual(v):
            F=frames(dict(zip(ids,v)));errs=[]
            for s,target in zip(['l','r'],targets):
                m=F[s+'_wrist_flex'];errs.extend(m[:3,:3]@np.array([0,0,-36])+m[:3,3]-target)
            return np.r_[errs,.03*(v-seed)]
        start=np.clip(seed+rng.normal(0,12,len(seed)),lim[:,0]+.01,lim[:,1]-.01)
        opt=least_squares(residual,start,bounds=(lim[:,0],lim[:,1]),max_nfev=100)
        q={k:float(v) for k,v in zip(ids,opt.x)};hits=e.check(q);score=sum(h['volume_mm3'] for h in hits)
        if score<best[0]:best=(score,q,hits);print('cross best',trial,score,len(hits),flush=True)
        if not hits:break
    out[n]['angles']=best[1];print('cross residual contacts',best[2],flush=True)
    put(HERE/'daily_poses.json',out);put(OUT/'profiles/poses.json',poses());put(OUT/'profiles/pose_frames.json',{n:frames(p['angles']) for n,p in poses().items()})
if __name__=='__main__':main()
