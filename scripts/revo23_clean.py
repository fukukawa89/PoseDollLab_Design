"""O23F workbench: symmetric simple skins and explicitly counted connections."""
from revo23_reinforcement import *
from build_revo23_reinforced import obstacle_transforms, spaced_points, padded_hull
import itertools

EHASH='e9bd47cc6a64a2e92148e237acaccf98df93c1a4fdc1f8524e6df6613fbfaa8d'
EHISTORY=B/'history/O23E_before_clean_symmetric_walls_20261021'
FROOT=B/'design/clean_candidate'
FREV='O23F-clean-symmetric-walls-20261021'


def archive_e():
    if (EHISTORY/'snapshot.json').exists():
        assert sha(EHISTORY/'assembly.npz')==EHASH
        return
    assert sha(B/'assembly.npz')==EHASH
    EHISTORY.mkdir(parents=True,exist_ok=True)
    names=['assembly.npz','assembly.json','retained_interfaces.npz','DELIVERY.json',
           'DESIGN.zh-CN.md','CONTINUOUS_WALLS.zh-CN.md',
           'FINGERS_STRUCTURE_HARNESS.zh-CN.md']
    for directory in ('profiles','verification','harness','images','preview'):
        names += [str(x.relative_to(B)) for x in (B/directory).rglob('*') if x.is_file()]
    copied={}
    for rel in names:
        source=B/rel
        if not source.exists(): continue
        dest=EHISTORY/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest);copied[rel]=sha(dest)
    shutil.copy2(CFG,EHISTORY/'parameters.json')
    for x in EROOT.glob('*.npz'):
        if x.name.startswith(('frame__','o22__')):
            dest=EHISTORY/'candidates'/x.name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(x,dest)
            if x.with_suffix('.json').exists():shutil.copy2(x.with_suffix('.json'),dest.with_suffix('.json'))
    for name in ('wire_seats.json','wire_channels.json','case_wire_seats.json'):
        if (EROOT/name).exists():shutil.copy2(EROOT/name,EHISTORY/name)
    (EHISTORY/'source').mkdir(exist_ok=True)
    for name in ('retained_interfaces.npz','interface_edge_reliefs.npz','interface_edge_reliefs.json'):
        source=DHISTORY/'source'/name
        if source.exists():shutil.copy2(source,EHISTORY/'source'/name)
    put(EHISTORY/'snapshot.json',dict(geometry_sha256=EHASH,files=copied))


def load_e_snapshot():
    z=np.load(EHISTORY/'assembly.npz');doc=read(EHISTORY/'assembly.json')
    parts={}
    for r in doc['items']:
        i=str(r['index']);parts[r['key']]=dict(r,s=solid(z[i+'v'],z[i+'f']))
    return parts,read(EHISTORY/'profiles/device_profile.json'),read(EHISTORY/'parameters.json')


def load_f():
    parts,p,cfg=load_e_snapshot()
    for key,item in parts.items():
        path=FROOT/(key.replace('/','__')+'.npz')
        if path.exists():
            z=np.load(path);item['s']=solid(z['v'],z['f'])
    return parts,p,cfg


def save_s(path,s):
    v,f=vf(s)
    np.savez_compressed(path,v=v,f=f)
    return solid(v,f)


def inspect():
    archive_e();FROOT.mkdir(exist_ok=True)
    parts,p,cfg=load_e_snapshot();N=frames(p,p['neutral_raw_deg'])
    kz=np.load(EHISTORY/'source/retained_interfaces.npz');out=[]
    for key,r in parts.items():
        if r['role']!='structure':continue
        n=N[r['token']];geom=canonical(r['body'],n,cfg)
        A=geom[3] if geom else np.eye(4)
        if geom is None:A[:3,3]=n[:3,3]
        keep=move(solid(kz[key+'|v'],kz[key+'|f']),np.linalg.inv(A)@n)
        lands=sorted([c for c in keep.decompose() if c.volume()>.01],key=lambda x:-x.volume())
        d=read(DHISTORY/'candidates'/(key.replace('/','__')+'.json'))
        row=dict(key=key,frame=n,canonical=A,volume_mm3=r['s'].volume(),
                 lands=[dict(volume_mm3=l.volume(),bbox=l.bounding_box()) for l in lands],
                 low=d['lower_boundary_mm'],high=d['upper_boundary_mm'],
                 ribs=d['ribs'],rows=geom[2] if geom else [])
        out.append(row)
        print(key,'lands',[(round(l.volume(),1),np.round(l.bounding_box(),1).tolist()) for l in lands],
              'skin z',np.round(geom[2][:,0],1).tolist() if geom else None,flush=True)
    put(FROOT/'inventory.json',out)


if __name__=='__main__':
    inspect()
