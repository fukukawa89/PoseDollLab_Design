from design import *
from collections import defaultdict
import time

def saved():
    a=load(OUT/'production_assembly.json')['parts'];z=np.load(OUT/'production_meshes.npz')
    ss=[md.Manifold(md.Mesh64(np.array(z[str(p['i'])+'v'],copy=True),np.array(z[str(p['i'])+'f'],dtype=np.uint64,copy=True))) for p in a]
    return a,ss

def check(full=False):
    a,ss=saved();poses=named_poses() if full else [('zero',{})];issues={};start=time.time()
    if '--quick' in sys.argv:poses=[('zero',{})]+[(n,p['angles']) for n,p in POSES.items()]+[(f'wrist/{f}/{d}',{'l_wrist_flex':f,'l_wrist_deviation':d}) for f in [-65,0,70] for d in [-20,0,30]]
    for no,(name,q) in enumerate(poses):
        ff=frames(q);world=[moved(s,ff[p['frame']]) for p,s in zip(a,ss)];bb=np.array([e.bounds(s) for s in world])
        for i,p in enumerate(a):
            if p.get('baseline_name') and not p.get('reprint'):continue
            possible=np.flatnonzero(np.all(bb[:,1]>bb[i,0]+.001,axis=1)&np.all(bb[:,0]<bb[i,1]-.001,axis=1))
            for j in possible:
                if j==i:continue
                if j>i and (not a[j].get('baseline_name') or a[j].get('reprint')):continue
                key=tuple(sorted([p['name'],a[j]['name']]))
                vol=(world[i]^world[j]).volume()
                if vol>.03 and (key not in issues or vol>issues[key]['overlap_mm3']):issues[key]=dict(parts=key,overlap_mm3=vol,pose=name)
        if no%40==0:print('CHECK',no,'/',len(poses),'pairs',len(issues),'seconds',round(time.time()-start,1),flush=True)
    rows=sorted(issues.values(),key=lambda r:-r['overlap_mm3'])
    expected={tuple(sorted(x)) for x in [('HS_HL_F1','SHOULDER_PITCH'),('HS_HR_F1','SHOULDER_PITCH'),('HE_HL_F1','UPPER_ARM'),('HE_HR_F1','UPPER_ARM')]+[(n,'KEEP_E-P019') for n in ['KEEP_E-H1133','KEEP_E-H1141','KEEP_E-H1149','KEEP_E-H1157']]}
    unexpected=[r for r in rows if tuple(r['parts']) not in expected or abs(r['overlap_mm3']-.0817568)>.005]
    put(OUT/'verification'/('motion_prototype.json' if full else 'zero_prototype.json'),dict(passed=not unexpected,sampled_poses=len(poses),unexpected=unexpected,issues=rows,geometry_sha256=sha(OUT/'production_meshes.npz'),scope='All new / changed installed bodies vs all bodies; inherited unchanged-vs-unchanged R4 pairs not repeated. Nominal discrete samples, not continuous swept-volume proof. Eight original FW4 retention-pad contacts separately accepted.'))
    print('ISSUES',len(rows),flush=True)
    for r in rows[:75]:print(r,flush=True)

if __name__=='__main__':check('--full' in sys.argv)
