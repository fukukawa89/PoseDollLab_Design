"""Rebuild solved G candidates around functional lands, dropping old rod stubs."""
from revo23_smooth import *
parts,p,cfg=load_g();N=frames(p,p['neutral_raw_deg']);kz=np.load(EHISTORY/'source/retained_interfaces.npz')
out=[]
for key,item in parts.items():
    path=GROOT/(key.replace('/','__')+'.npz')
    if item['role']!='structure' or not path.exists():continue
    r=read(path.with_suffix('.json'));M=N[item['token']]
    original=source_keep(key,kz,item,p,N);keep=raw_keep(key,parts,p,N);mat=[keep,skin_of(key)]
    for rod in r['rods']:
        pts=np.array(rod['centerline_world_mm']);radius=rod['radius_mm']
        body=cyl(*pts,radius) if len(pts)==2 else round_sweep(pts,radius)
        pos=np.array(rod['wall_landing_world_mm']);normal=pos-pts[-1];normal/=np.linalg.norm(normal)
        depth=7. if item['body'].startswith(('forearm_','elbow_')) else 13.
        pad=tapered(pos-normal*depth,pos-normal*1.8,radius+.8,radius+2.5)
        mat.append(move(body+pad,np.linalg.inv(M)))
    s=union(mat);cc=[a for a in s.decompose() if a.volume()>.05]
    row=dict(key=key,removed_legacy_stub_mm3=max(0.,(original-keep).volume()),components=len(cc))
    if len(cc)==1:
        save_s(path,s);r['candidate_sha256']=sha(path);r['volume_mm3']=s.volume();r['legacy_stub_cleanup']=row
        # Land ordering changes when obsolete fragments are removed. Bind
        # each real rod to the mounting land it actually intersects.
        lands=sorted(keep.decompose(),key=lambda a:-a.volume())
        for rod in r['rods']:
            pts=np.array(rod['centerline_world_mm']);b=cyl(*pts,rod['radius_mm']) if len(pts)==2 else round_sweep(pts,rod['radius_mm'])
            b=move(b,np.linalg.inv(M));rod['mount']=int(np.argmax([(b^a).volume() for a in lands]))
        put(path.with_suffix('.json'),r);row['rebuilt']=True
    else:row['rebuilt']=False
    out.append(row);print(row,flush=True)
put(GROOT/'stub_cleanup.json',dict(rows=out))
