"""Check cross-module static packing after clocking the collar carriers."""
from build_revo23_continuous import *
from present_revo23 import load_current

p=read(DROOT/'source/device_profile.json');F=frames(p,p['neutral_raw_deg'])
parts=load_c();parts={k:v for k,v in parts.items() if v['role']!='structure'}
S={k:move(v['s'],F[v['token']]) for k,v in parts.items()}
BB={k:np.array(s.bounding_box()) for k,s in S.items()}
changed=[k for k in parts if k.startswith(('clavicle_l.protract/','clavicle_r.protract/'))]
hits=[];seen=set();maximum=0.
for a in changed:
    for b in parts:
        if a.split('/')[0]==b.split('/')[0]:continue
        pair=tuple(sorted((a,b)))
        if pair in seen:continue
        seen.add(pair)
        if np.any(np.minimum(BB[a][3:],BB[b][3:])-np.maximum(BB[a][:3],BB[b][:3])<=0):continue
        v=max(0.,(S[a]^S[b]).volume());maximum=max(maximum,v)
        if v>.05:hits.append(dict(pair=pair,overlap_mm3=v))
put(B/'verification/collar_static_packing.json',dict(profile_sha256=profile_signature(p),
    hits=hits,maximum_overlap_mm3=maximum,passed=not hits,
    scope='Neutral actual collar native parts versus every different native module, including rigidly attached modules. Same-module geometry is invariant under rigid clocking.'))
print('COLLAR STATIC',not hits,maximum,len(hits),flush=True)
for h in hits:print(h,flush=True)
