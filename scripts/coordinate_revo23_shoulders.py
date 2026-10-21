"""Fit ordinary shoulder poses with modest clavicle motion and exact target rotation.

No target angle is reduced. Candidate collar angles stay within +/-15 degrees.
All remaining actual-solid conflicts still have to pass verify_revo23_daily.
"""
from build_revo23_continuous import *
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
import itertools


def main():
    p=read(DROOT/'source/device_profile.json');parts=load_c()
    path=B/'profiles/daily_poses.json'
    original=B/'profiles/daily_poses_uncoordinated.json'
    if not original.exists():shutil.copy2(path,original)
    spec=read(original);groups=rigid_groups(p,{v['token'] for v in parts.values()})
    edges=anatomical_edges(p);cache={};bounds={}
    keys=[k for k,v in parts.items() if v['role']!='structure']
    for k in keys:
        b=parts[k]['s'].bounding_box();bounds[k]=np.array(list(itertools.product(*zip(b[:3],b[3:]))))
    pairs={}
    for side in ('l','r'):
        moving={k for k in keys if k.startswith(('upperarm_'+side+'/', 'clavicle_'+side+'.'))}
        pairs[side]=[(a,b) for a in moving for b in keys if a!=b and (b not in moving or a<b)
                     and adjacent(parts[a],parts[b],p,edges) and groups[parts[a]['token']]!=groups[parts[b]['token']]]

    def score(q,side):
        F=frames(p,q);bb={}
        for k in {x for pair in pairs[side] for x in pair}:
            M=F[parts[k]['token']];v=bounds[k]@M[:3,:3].T+M[:3,3];bb[k]=np.r_[v.min(0),v.max(0)]
        total=0.
        for a,b in pairs[side]:
            if np.any(np.minimum(bb[a][3:],bb[b][3:])-np.maximum(bb[a][:3],bb[b][:3])<=0):continue
            rel=np.linalg.inv(F[parts[a]['token']])@F[parts[b]['token']]
            ck=(a,b,tuple(np.round(rel,7).ravel()))
            if ck not in cache:cache[ck]=max(0.,float((parts[a]['s']^move(parts[b]['s'],rel)).volume()))
            if cache[ck]>.05:total+=cache[ck]
        return total

    records=[]
    definitions={d['name']:d for d in spec['policy']['poses']}
    for name,q0 in spec['poses'].items():
        group=definitions[name]['group']
        if group not in ('upperarm_l','upperarm_r','basic','combined'):continue
        q=dict(q0);targets=kin.forward(p,q0)
        for side in ('l','r'):
            before=score(q,side)
            if before<.05:continue
            j=next(j for j in p['joints'] if j['id']=='upperarm_'+side)
            raw=j['raw_ids'];limits=np.array([p['raw_limits_deg'][r] for r in raw]);x0=np.array([q0[r] for r in raw])
            collar=[f'clavicle_{side}.{word}/r0' for word in ('protract','elevate')]
            grid=sorted(itertools.product((-15,-10,-5,0,5,10,15),repeat=2),key=lambda a:sum(abs(a[n]-q0[collar[n]]) for n in range(2)))
            best=(before,float('inf'),q,None)
            for angles in grid:
                trial=dict(q);trial.update(dict(zip(collar,angles)))
                parent=kin.forward(p,trial)[j['parent']][:3,:3]
                target=parent.T@targets[j['child']][:3,:3]
                def residual(x):
                    return np.r_[Rotation.from_matrix(target.T@joint_rotation(j,x)).as_rotvec(),(x-x0)*1e-8]
                fit=least_squares(residual,np.clip(x0,limits[:,0]+1e-7,limits[:,1]-1e-7),
                    bounds=(limits[:,0],limits[:,1]),max_nfev=200,xtol=1e-10,ftol=1e-10,gtol=1e-10)
                err=np.rad2deg(np.linalg.norm(residual(fit.x)[:3]))
                if err>.02:continue
                trial.update(dict(zip(raw,map(float,fit.x))));hit=score(trial,side)
                cost=sum(abs(angles[n]-q0[collar[n]]) for n in range(2))+.01*np.linalg.norm(fit.x-x0)
                if (hit,cost)<best[:2]:best=(hit,cost,trial,dict(collar_deg=angles,orientation_error_deg=err))
                if hit<.05:break
            q=best[2]
            records.append(dict(pose=name,side=side,before_overlap_mm3=before,after_overlap_mm3=best[0],solution=best[3],raw_deg=q))
            print('SHOULDER',name,side,'before',round(before,3),'after',round(best[0],3),'solution',best[3],flush=True)
        spec['poses'][name]=q
    spec['policy']['shoulder_coordination']=records
    spec['policy']['coordination_note']='Exact arm orientation targets retained; clavicle protraction/elevation may accompany raising/turning the arm within +/-15 degrees. This is a defined pose set, not all arbitrary joint combinations.'
    spec['profile_sha256']=sha(DROOT/'source/device_profile.json')
    put(path,spec);put(B/'verification/shoulder_coordination.json',dict(records=records,unresolved=[r for r in records if r['after_overlap_mm3']>.05]))
    print('COORDINATED',len(records),'unresolved',sum(r['after_overlap_mm3']>.05 for r in records),flush=True)


if __name__=='__main__':main()
