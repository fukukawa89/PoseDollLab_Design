"""Detect new fixed-part interference introduced by re-clocked structural lands."""
from build_revo23_continuous import *
from present_revo23 import load_current

p=read(B/'profiles/device_profile.json');parts=load_current()
checkpoint=DROOT/'checkpoints/before_collar_clock_180'
previous=read(checkpoint/'device_profile.json');z=np.load(checkpoint/'assembly.npz')
old={k:dict(v,s=solid(z[str(v['index'])+'v'],z[str(v['index'])+'f'])) for k,v in parts.items()}
F=frames(p,p['neutral_raw_deg']);P=frames(previous,previous['neutral_raw_deg'])
groups=rigid_groups(p,{v['token'] for v in parts.values()})
keys=['frame/chest','frame/clavicle_l','frame/clavicle_r',
      'frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame']
rows=[];hits=[]
for key in keys:
    item=parts[key];bb=np.array(item['s'].bounding_box());I=np.linalg.inv(F[item['token']])
    for k,other in parts.items():
        if k==key or groups[item['token']]!=groups[other['token']]:continue
        s=move(other['s'],I@F[other['token']]);b=np.array(s.bounding_box())
        if np.any(np.minimum(bb[3:],b[3:])-np.maximum(bb[:3],b[:3])<=0):continue
        volume=max(0.,(item['s']^s).volume())
        if volume<=.05:continue
        os=move(old[k]['s'],np.linalg.inv(P[item['token']])@P[other['token']])
        before=max(0.,(old[key]['s']^os).volume())
        r=dict(pair=[key,k],overlap_mm3=volume,previous_overlap_mm3=before,
               increased=volume>before+.05)
        rows.append(r)
        if r['increased']:hits.append(r)
put(B/'verification/fixed_interfaces.json',dict(geometry_sha256=sha(B/'assembly.npz'),
    previous_geometry_sha256=sha(checkpoint/'assembly.npz'),rows=rows,new_contacts=hits,
    passed=not hits,scope='All fixed rigid attachments of the five rebuilt collar/chest carriers. Existing same-pair fitted overlaps retained explicitly.',
    physical_tested=False,manufacturing_release=False))
print('FIXED INTERFACES',not hits,len(hits),flush=True)
for r in hits:print(r,flush=True)
