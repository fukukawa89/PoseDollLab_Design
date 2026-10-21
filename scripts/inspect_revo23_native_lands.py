"""Separate functional joint envelopes from old cut-off rod remnants."""
from revo23_smooth import *
from functools import lru_cache

@lru_cache(None)
def libraries():return kin.b.b.L.libraries()

def core_boxes(key,parts,p,N,margin=2.):
    body=parts[key]['body'];M=N[parts[key]['token']];guards=[];rows=[]
    for j in p['joints']:
        if body not in (j['parent'],j['child']):continue
        parent=body==j['parent'];kind=j['kind'];lib,owners,sku=libraries()[kind]
        if kind in ('wide_tut','tut'):names=['P_case_minus' if parent else 'D_case_minus']
        elif kind=='three_axis':names=['P_case_minus' if parent else 'C02']
        elif kind=='ankle_core':names=['C02' if parent else 'C01']
        else:names=['base_sensor_half','base_service_half'] if parent else ['lever_cup']
        for name in names:
            bb=np.array(lib[name].bounding_box());T=N['j:'+j['id']+':'+owners[name]]
            if j['id']=='wrist_r':
                T=np.diag([1.,-1.,1.,1.])@N['j:wrist_l:'+owners[name]]
            guards.append(move(box(bb[:3]-margin,bb[3:]+margin),np.linalg.inv(M)@T))
            rows.append(dict(joint=j['id'],native_part=name,margin_mm=margin))
    if key=='frame/chest':
        heads=np.array(read(B/'design/compact_revision.json')['mount_heads_world_mm'])
        for side in (-1,1):
            selected=heads[heads[:,1]*side>0];c=selected.mean(0)
            guards.append(move(box([c[0]-4,c[1]-9,selected[:,2].min()-9],[c[0]+15,c[1]+9,selected[:,2].max()+9]),np.linalg.inv(M)))
    return union(guards),rows

def protected_keep(key,parts,p,N,original):
    from revo23_daily import rigid_groups
    guard,defs=core_boxes(key,parts,p,N)
    groups=rigid_groups(p,{x['token'] for x in parts.values()});own=groups[parts[key]['token']]
    for other,item in parts.items():
        if other==key or item['role']=='structure' or groups[item['token']]!=own:continue
        s=move(item['s'],np.linalg.inv(N[parts[key]['token']])@N[item['token']]);b=np.array(s.bounding_box())
        guard+=box(b[:3]-3,b[3:]+3)
    s=original^guard
    return union([c for c in s.decompose() if c.volume()>=5.]),defs

if __name__=='__main__':
    parts,p,c=load_g();N=frames(p,p['neutral_raw_deg']);out=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        keep=raw_keep(key,parts,p,N);guard,defs=core_boxes(key,parts,p,N)
        cropped,defs=protected_keep(key,parts,p,N,keep);remaining=[x.volume() for x in cropped.decompose() if x.volume()>.05]
        out.append(dict(key=key,removed_mm3=max(0.,(keep-guard).volume()),remaining=remaining,definitions=defs))
        print(key,round(out[-1]['removed_mm3'],2),np.round(remaining,1).tolist(),flush=True)
        save_s(GROOT/(key.replace('/','__')+'_native_keep.npz'),cropped)
    put(GROOT/'native_land_inspection.json',out)
