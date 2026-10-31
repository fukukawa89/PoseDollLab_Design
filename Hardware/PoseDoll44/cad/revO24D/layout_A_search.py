"""Author tool: local sensor clock search against actual saved grid postures."""
from validate import *

def obstacles(parts,ss,fr,cases,excluded):
    corners=[]
    for s in ss:
        lo,hi=np.array(s.bounding_box()).reshape(2,3)
        corners.append(np.array([[hi[k] if mask>>k&1 else lo[k] for k in range(3)] for mask in range(8)]))
    obs={}
    for qi,q in enumerate(cases):
        F=frames(q);back=np.linalg.inv(F[fr])
        for i,p in enumerate(parts):
            if p['name'] in excluded or family(fr)==family(p['frame']):continue
            if qi and not required(fr,p['frame']):continue
            rel=back@F[p['frame']];key=(i,np.round(rel,6).tobytes())
            if key in obs:continue
            v=corners[i]@rel[:3,:3].T+rel[:3,3];obs[key]=(i,rel,v.min(0),v.max(0))
    rows=list(obs.values());return rows,np.array([r[2] for r in rows]),np.array([r[3] for r in rows])

def score(candidate,obs,ss,parts,cache,bounds=None):
    rows,mins,maxs=obs;b=np.array(candidate.bounding_box()).reshape(2,3);hits=[]
    mask=np.all(maxs>b[0],1)&np.all(mins<b[1],1)
    if bounds is not None:
        mask &= np.any(np.array([np.all(maxs>bb[0],1)&np.all(mins<bb[1],1) for bb in bounds]),axis=0)
    for ix in np.where(mask)[0]:
        i,rel,_,_=rows[ix]
        if ix not in cache:cache[ix]=moved(ss[i],rel)
        v=(candidate^cache[ix]).volume()
        if v>.02:hits.append((parts[i]['name'],v))
    return hits

def main():
    parts,z,ss=read_assembly();g=load(OUT/'verification/joint_local_grids.json')
    cases=[dict(NEUTRAL_ANGLES)]+[c['angles'] for group in g['groups'] for c in group['cases']]
    pre='r_humeral';names=[p['name'] for p in parts if p['name'].startswith(pre+'_') and any(t in p['name'] for t in ['pcb','connector','sensor_holder'])]
    ids=[i for i,p in enumerate(parts) if p['name'] in names];fr=parts[ids[0]]['frame'];shape=union(ss[i] for i in ids)
    j=next(j for j in load(OUT/'profiles/joint_interfaces.json') if j['id']==pre);o=np.array(j['center_mm']);axis=j['axis_world'];old=load(HERE/'sensor_layout.json')[pre]
    obs=obstacles(parts,ss,fr,cases,names);cache={};best=(1e30,None,None)
    for angle in range(0,360,15):
        world=T(o)@rot(axis,angle-old)@T(-o);s=moved(shape,np.linalg.inv(F0[fr])@world@F0[fr]);hits=score(s,obs,ss,parts,cache);volume=sum(v for n,v in hits)
        if volume<best[0]:best=(volume,angle,sorted({n for n,v in hits}));print('SENSOR BEST',best,flush=True)
        if not hits:break
    put(OUT/'verification/A_sensor_proposal.json',dict(volume=best[0],angle=best[1],colliding_parts=best[2]))

if __name__=='__main__':main()
