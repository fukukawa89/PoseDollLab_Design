"""Densify motion near the eight repaired contacts, without changing targets."""
from verify_revo23_daily import *
import math

p=read(B/'profiles/device_profile.json');spec=read(B/'profiles/daily_poses.json')
paths=[
    ('upperarm_l.side_raise',45,90),('upperarm_r.side_raise',-90,-45),
    ('clavicle_l.elevate.elevate',-15,-10),
    ('elbow_r.flex.flexion',105,130),('wrist_r.flex',30,45)
]
poses={};segments=[]
for prefix,lo,hi in paths:
    points=sorted((float(name.rsplit('@',1)[1]),name,q) for name,q in spec['poses'].items()
                  if name.startswith(prefix+'@') and lo<=float(name.rsplit('@',1)[1])<=hi)
    for (a,na,qa),(b,nb,qb) in zip(points,points[1:]):
        n=max(2,math.ceil((b-a)/1.))
        segments.append(dict(start=na,end=nb,samples=n-1,raw_axis_linear_interpolation=True))
        for i in range(1,n):
            t=i/n
            poses[f'edge_path/{prefix}@{a+(b-a)*t:g}']={k:(1-t)*qa[k]+t*qb[k] for k in p['raw_order']}
parts=load_current();out=B/'verification/edge_paths.json'
put(B/'profiles/edge_path_poses.json',dict(profile_sha256=sha(B/'profiles/device_profile.json'),poses=poses,segments=segments))
out.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
report=check_daily(parts,p,poses,[],sha(B/'assembly.npz'),None,out)
report.update(segments=segments,complete_policy=False,trial=False,
    note='All actual moving adjacent pairs at additional <=1 degree raw-axis steps around repaired contact regions; interpolates shoulder coordination. Not a continuous proof.',
    profile_sha256=sha(B/'profiles/device_profile.json'))
put(out,report)
print('EDGE PATHS',report['passed'],len(report['blocking_contacts']),flush=True)
