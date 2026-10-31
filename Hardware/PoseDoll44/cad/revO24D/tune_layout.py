"""Offline exact-solid clock search; output is a proposal, never a pass claim."""
from validate import *
from rom_cases import examination_cases

def main():
    parts,z,ss=read_assembly();interfaces={j['id']:j for j in load(OUT/'profiles/joint_interfaces.json')}
    cases=[{}]+[v['angles'] for v in examination_cases().values()]+[v['angles'] for v in poses().values()]
    corners=[]
    for s in ss:
        lo,hi=np.array(s.bounding_box()).reshape(2,3);corners.append(np.array([[hi[k] if mask>>k&1 else lo[k] for k in range(3)] for mask in range(8)]))
    result=[]
    brake='--brake' in sys.argv
    for pre in (['lumbar_shoulder_swing'] if brake else ['r_shoulder_pitch','l_shoulder_pitch','l_humeral','r_humeral','l_forearm','r_forearm','l_hip_pitch','r_hip_pitch','neck_shoulder_swing']):
        tokens=['pressure_','fork_','guide_boss_','compression_spacer_','preload_'] if brake else ['pcb','connector','sensor_holder']
        ids=[i for i,p in enumerate(parts) if p['name'].startswith(pre+'_') and any(t in p['name'] for t in tokens)]
        fr=parts[ids[0]]['frame'];obs={}
        for q in cases:
            F=frames(q);back=np.linalg.inv(F[fr]);rels={n:back@W for n,W in F.items()}
            for j,p in enumerate(parts):
                if family(fr)==family(p['frame']):continue
                W=rels[p['frame']];key=(j,np.round(W,6).tobytes())
                if key in obs:continue
                vv=corners[j]@W[:3,:3].T+W[:3,3];obs[key]=(j,W,vv.min(0),vv.max(0))
        arr=list(obs.values());mins=np.array([x[2] for x in arr]);maxs=np.array([x[3] for x in arr]);shapes={};best=None
        joint=interfaces[pre];o=np.array(joint['center_mm']);ax=joint['axis_world']
        for angle in range(0,360,15):
            L=np.linalg.inv(F0[fr])@T(o)@rot(ax,angle)@T(-o)@F0[fr];nh=0;vol=0;pairs=set()
            for i in ids:
                s=moved(ss[i],L);b=np.array(s.bounding_box()).reshape(2,3)
                candidates=np.where(np.all(maxs>b[0],1)&np.all(mins<b[1],1))[0]
                for idx in candidates:
                    j,W,_,_=arr[idx]
                    if idx not in shapes:shapes[idx]=moved(ss[j],W)
                    v=(s^shapes[idx]).volume()
                    if v>.02:nh+=1;vol+=v;pairs.add((parts[i]['name'],parts[j]['name']))
            item=(nh,vol,angle,sorted(pairs))
            if best is None or item[:2]<best[:2]:best=item
        print(pre,best,flush=True);result.append(dict(prefix=pre,angle_delta_deg=best[2],remaining_pair_states=best[0],remaining_volume_mm3=best[1],pairs=best[3]))
    put(OUT/('verification/brake_layout_proposal.json' if brake else 'verification/sensor_layout_proposal.json'),dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),rows=result))

if __name__=='__main__':main()
