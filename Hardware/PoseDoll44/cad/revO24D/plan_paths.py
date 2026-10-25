"""Finite collision-checked coordinated transitions, separate from raw ROM sweeps."""
from validate import *

def main():
    parts,z,s=read_assembly();e=Collision(parts,s);cache={};rows=[];allposes=poses();rng=np.random.default_rng(2424)
    def check(q):
        key=tuple(sorted((k,round(v,6)) for k,v in q.items() if abs(v)>1e-7))
        if key not in cache:cache[key]=e.check(q)
        return cache[key]
    def segment(q0,q1):
        keys=set(q0)|set(q1);n=max(1,math.ceil(max((abs(q1.get(k,0)-q0.get(k,0)) for k in keys),default=0)/4))
        path=[]
        for j in range(1,n+1):
            q={k:q0.get(k,0)+(q1.get(k,0)-q0.get(k,0))*j/n for k in keys};hits=check(q)
            if hits:return None,dict(fraction=j/n,angles=q,collisions=hits)
            path.append(q)
        return path,None
    def trial(points):
        path=[dict(NEUTRAL_ANGLES)]
        if check(NEUTRAL_ANGLES):return None,dict(angles=NEUTRAL_ANGLES,collisions=check(NEUTRAL_ANGLES))
        for a,b in zip(points[:-1],points[1:]):
            seg,fail=segment(a,b)
            if fail:return None,fail
            path.extend(seg)
        return path,None
    hub={'l_shoulder_flex':80,'r_shoulder_flex':80,'l_elbow_flex':20,'r_elbow_flex':20}
    gate={'l_shoulder_abduct':45,'r_shoulder_abduct':45};wide={**hub,**gate}
    for name,p in allposes.items():
        goal=p['angles'];options=[[dict(NEUTRAL_ANGLES),goal],[dict(NEUTRAL_ANGLES),gate,goal],[dict(NEUTRAL_ANGLES),gate,wide,hub,goal]]
        # Raise arms clear of the pelvis first; then legs and trunk; then arm endpoint.
        mid={**goal,**hub};options.append([dict(NEUTRAL_ANGLES),gate,wide,hub,mid,goal])
        left={k:v for k,v in goal.items() if k.startswith('l_')};right={k:v for k,v in goal.items() if k.startswith('r_')}
        for clearance in [dict(r_shoulder_abduct=90),dict(r_shoulder_flex=120,r_elbow_flex=15),dict(r_shoulder_flex=70,r_shoulder_abduct=45),dict(r_shoulder_flex=15,r_elbow_flex=30)]:
            options.append([dict(NEUTRAL_ANGLES),gate,wide,hub,{**left,**clearance},goal])
        found=None;failure=None;used=None
        for ix,waypoints in enumerate(options):
            path,failure=trial(waypoints)
            if path is not None:found=path;used=waypoints;break
        if found is None and not check(goal):
            # Bounded reproducible waypoint search, retaining the exact end pose.
            for j in range(100):
                mid={**goal}
                for side in ['l','r']:
                    mid[side+'_shoulder_flex']=float(rng.uniform(35,115));mid[side+'_shoulder_abduct']=float(rng.uniform(5,55));mid[side+'_elbow_flex']=float(rng.uniform(30,100))
                options2=[dict(NEUTRAL_ANGLES),gate,wide,hub,mid,goal];path,failure=trial(options2)
                if path is not None:found=path;used=options2;break
        rows.append(dict(pose=name,status='PASS_SAMPLED_PATH' if found is not None else 'PATH_UNRESOLVED',samples=len(found or []),waypoints=used,path=found,last_failure=failure if found is None else None))
        print(name,rows[-1]['status'],rows[-1]['samples'],flush=True)
    put(OUT/'verification/motion_task_paths.json',dict(status='PASS_SAMPLED_PATHS' if all(r['path'] is not None for r in rows) else 'PARTIAL',geometry_sha256=sha(OUT/'assembly_meshes.npz'),start_pose='A neutral',start_angles=NEUTRAL_ANGLES,max_step_deg=4,total_unique_samples=len(cache),threshold_mm3=.02,cases=rows,scope='A neutral to named poses, each joint changes at most 4 degrees per step. Same/adjacent anatomical moving bodies required; non-adjacent body contacts advisory per user instruction. Finite sampling, not continuum or flexible harness proof.'))
if __name__=='__main__':main()
