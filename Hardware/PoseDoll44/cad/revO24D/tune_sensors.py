"""Author sensor clocking using exact solid intersections; does not change axes."""
from connections import *
from rom_cases import examination_cases

def score_group(parts,ss,ids,axis,point,angle,cases):
    replace={};total=0;nh=0;pairs=set()
    world=T(point)@rot(axis,angle)@T(-np.array(point))
    for i in ids:replace[i]=moved(ss[i],np.linalg.inv(F0[parts[i]['frame']])@world@F0[parts[i]['frame']])
    seen=set()
    for q in cases:
        F=frames(q)
        for i in ids:
            s=replace[i];bb=np.array(s.bounding_box()).reshape(2,3);par=parts[i]['frame'];back=np.linalg.inv(F[par])
            for j,p in enumerate(parts):
                if j in ids or family(par)==family(p['frame']):continue
                W=back@F[p['frame']];key=(i,j,np.round(W,5).tobytes())
                if key in seen:continue
                seen.add(key);t=moved(ss[j],W);b=np.array(t.bounding_box()).reshape(2,3)
                if np.all(bb[1]>b[0]) and np.all(b[1]>bb[0]):
                    v=(s^t).volume()
                    if v>.02:total+=v;nh+=1;pairs.add((parts[i]['name'],p['name']))
    return nh,total,sorted(pairs)

def main():
    parts,z,ss=read_assembly();cases=[{}]+[p['angles'] for p in examination_cases().values()]+[p['angles'] for p in poses().values()]
    result=[]
    for pre,axis,point in [('neck_shoulder_swing',[0,1,0],P['neck_01']),('r_shoulder_pitch',[0,1,0],P['upperarm_r'])]:
        ids=[i for i,p in enumerate(parts) if p['name'].startswith(pre+'_') and any(t in p['name'] for t in ['pcb','connector','sensor_holder'])]
        best=None
        for ang in range(0,360,30):
            n,v,pairs=score_group(parts,ss,ids,axis,point,ang,cases);item=(n,v,ang,pairs)
            print(pre,ang,n,round(v,2),flush=True)
            if best is None or item[:2]<best[:2]:best=item
        print('BEST',pre,best,flush=True);result.append(dict(prefix=pre,axis=axis,point_mm=point,angle_delta_deg=best[2],remaining_pairs=best[3]))
    put(OUT/'verification/sensor_clock_search.json',result)
if __name__=='__main__':main()
