"""Find the smallest waist/chest axial adjustment clearing centered hips."""
from build_revo23_continuous import *
import itertools


def shifted_profile(p,rise):
    p=copy.deepcopy(p);F=frames(p,p['neutral_raw_deg'])
    for j in p['joints']:
        if j['id']=='waist':
            R=F['f:'+j['child']][:3,:3]@np.array(j['rotor_to_child_mm'])[:3,:3].T
            A=np.array(j['parent_to_mount_mm']);G=np.array(j['rotor_to_child_mm'])
            A[:3,3]+=F['f:'+j['parent']][:3,:3].T@np.array([0,0,rise])
            G[:3,3]-=R.T@np.array([0,0,rise])
            j['parent_to_mount_mm']=A.tolist();j['rotor_to_child_mm']=G.tolist()
        if j['id']=='chest':
            A=np.array(j['parent_to_mount_mm'])
            A[:3,3]+=F['f:'+j['parent']][:3,:3].T@np.array([0,0,rise])
            j['parent_to_mount_mm']=A.tolist()
    return p


def main():
    p=read(DROOT/'source/device_profile.json');parts=load_c()
    keys=[k for k in parts if k.split('/')[0] in ('thigh_l','thigh_r','waist','chest')]
    pairs=[(a,b) for a,b in itertools.combinations(keys,2) if a.split('/')[0]!=b.split('/')[0]]
    bounds={}
    for k in keys:
        bb=parts[k]['s'].bounding_box();bounds[k]=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))))
    poses={n:q for n,q in read(B/'profiles/daily_poses.json')['poses'].items()
           if n in ('A_STAND_35','N_NEUTRAL') or n.startswith(('thigh_','waist.','chest.','daily_'))}
    results=[]
    for rise in (2.,4.,6.,8.,10.,12.):
        pp=shifted_profile(p,rise);hits=[];cache={}
        for name,q in poses.items():
            ff=frames(pp,q);bb={}
            for k in keys:
                M=ff[parts[k]['token']];v=bounds[k]@M[:3,:3].T+M[:3,3];bb[k]=np.r_[v.min(0),v.max(0)]
            for a,b in pairs:
                if np.any(np.minimum(bb[a][3:],bb[b][3:])-np.maximum(bb[a][:3],bb[b][:3])<=0):continue
                T=np.linalg.inv(ff[parts[a]['token']])@ff[parts[b]['token']]
                sig=(a,b,tuple(np.round(T,7).ravel()))
                if sig not in cache:cache[sig]=max(0.,float((parts[a]['s']^move(parts[b]['s'],T)).volume()))
                if cache[sig]>.05:hits.append(dict(pose=name,pair=[a,b],overlap_mm3=cache[sig]))
        result=dict(additional_raise_mm=rise,contacts=hits,pose_count=len(poses))
        results.append(result);print('FIT RISE',rise,'contacts',len(hits),'worst',sorted(hits,key=lambda h:-h['overlap_mm3'])[:3],flush=True)
        put(B/'verification/centered_hip_space_search.json',results)
        if not hits:break


if __name__=='__main__':main()
