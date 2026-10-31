"""Author search for compact local forks/boards, with fixed effective axes."""
from layout_A_search import *

def main():
    parts,z,ss=read_assembly();data=load(OUT/'verification/joint_local_grids.json');cases=[dict(NEUTRAL_ANGLES)]+[c['angles'] for g in data['groups'] for c in g['cases']]
    mode=sys.argv[1];by={p['name']:i for i,p in enumerate(parts)}
    if mode=='fork':
        i=by['l_elbow_fork_-14'];fr=parts[i]['frame'];obs=obstacles(parts,ss,fr,cases,[parts[i]['name']]);cache={}
        for dx in [-3,3,-5,5,-7,7,-9,9,-12,12]:
            points=[[0,0,22],[dx,0,22],[dx,-10.5,22],[dx,-10.5,7],[0,-10.5,7],[0,-10.5,0]]
            shape=union(beam(x,y,2.6) for x,y in zip(points[:-1],points[1:]))-cyl([0,-20,0],[0,20,0],4.58)
            shape=moved(shape,np.linalg.inv(F0[fr])@T(P['lowerarm_l']));hits=score(shape,obs,ss,parts,cache)
            print(mode,dx,sum(v for n,v in hits),sorted({n for n,v in hits}),flush=True)
            if not hits:put(OUT/'verification/A_local_fork_proposal.json',dict(points=points,radius_mm=2.6));return
    else:
        pre='l_elbow' if mode=='elbow' else 'r_shoulder_pitch';ids=[i for i,p in enumerate(parts) if p['name'].startswith(pre+'_') and any(k in p['name'] for k in ['pcb','connector','sensor_holder'])];fr=parts[ids[0]]['frame'];shape=union(ss[i] for i in ids);obs=obstacles(parts,ss,fr,cases,[parts[i]['name'] for i in ids]);cache={};j=next(j for j in load(OUT/'profiles/joint_interfaces.json') if j['id']==pre);o=np.array(j['center_mm']);axis=j['axis_world'];old=load(HERE/'sensor_layout.json').get(pre,0)
        options=[(a,[0,0,0]) for a in range(0,360,15)] if mode=='elbow' else [(a,[x,0,z]) for a in [15,0,90,270] for x,z in [(2,0),(-2,0),(0,2),(0,-2),(3,0),(-3,0),(0,3),(0,-3),(2,2),(2,-2),(-2,2),(-2,-2)]]
        for angle,delta in options:
            W=T(delta)@T(o)@rot(axis,angle-old)@T(-o);s=moved(shape,np.linalg.inv(F0[fr])@W@F0[fr]);hits=score(s,obs,ss,parts,cache)
            print(mode,angle,delta,round(sum(v for n,v in hits),4),sorted({n for n,v in hits}),flush=True)
            if not hits:put(OUT/f'verification/A_local_{mode}_proposal.json',dict(angle=angle,delta_world_mm=delta));return
    print('NO LOCAL CANDIDATE',mode,flush=True)

if __name__=='__main__':main()
