"""O23E workbench: immutable D input, measurable attachments, and wire fixtures."""
from build_revo23_continuous import *
import csv

EROOT=B/'design/reinforced_candidate'
DHISTORY=B/'history/O23D_before_fingers_strength_harness_20261020'
DHASH='64d347b397c0eb90f084982b04a33fd9bcf3adab72a4eebca7e4de686451e7fc'


def archive_d():
    if (DHISTORY/'snapshot.json').exists():
        assert sha(DHISTORY/'assembly.npz')==DHASH
        return
    assert sha(B/'assembly.npz')==DHASH,'Snapshot the reviewed D geometry only.'
    DHISTORY.mkdir(parents=True,exist_ok=True)
    names=['assembly.npz','assembly.json','DELIVERY.json','DESIGN.zh-CN.md',
        'CONTINUOUS_WALLS.zh-CN.md','profiles/device_profile.json',
        'profiles/default_pose.json','profiles/daily_poses.json','profiles/edge_path_poses.json']
    names += [str(x.relative_to(B)) for x in (B/'verification').glob('*.json')
              if not any(v in x.name for v in ('partial','progress','trial'))]
    names += [str(x.relative_to(B)) for x in (B/'images').glob('*') if x.is_file()]
    for name in names:
        src=B/name;dst=DHISTORY/name;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
    shutil.copy2(CFG,DHISTORY/'parameters.json')
    shutil.copytree(DROOT/'source',DHISTORY/'source',dirs_exist_ok=True)
    for src in DROOT.glob('frame__*'):
        if src.is_file():
            dst=DHISTORY/'candidates'/src.name;dst.parent.mkdir(exist_ok=True)
            shutil.copy2(src,dst)
    put(DHISTORY/'snapshot.json',dict(geometry_sha256=DHASH,
        reason='User accepted D exterior; preserve it before finger, load-path and harness work.',
        files={n:sha(DHISTORY/n) for n in names}))


def load_d():
    archive_d()
    z=np.load(DHISTORY/'assembly.npz');parts={}
    for item in read(DHISTORY/'assembly.json')['items']:
        i=str(item['index']);parts[item['key']]=dict(item,s=solid(z[i+'v'],z[i+'f']))
    return parts,read(DHISTORY/'profiles/device_profile.json'),read(DHISTORY/'parameters.json')


def local_skin(key,p,cfg):
    path=DHISTORY/'candidates'/(key.replace('/','__')+'_skin.npz')
    if not path.exists():return md.Manifold()
    F=frames(p,p['neutral_raw_deg'])['f:'+key.split('/',1)[1]]
    geom=canonical(key.split('/',1)[1],F,cfg)
    if geom is None:return md.Manifold()
    z=np.load(path);return move(solid(z['v'],z['f']),np.linalg.inv(F)@geom[3])


def connection_inventory():
    parts,p,cfg=load_d();z=np.load(DHISTORY/'source/retained_interfaces.npz')
    out=[];EROOT.mkdir(parents=True,exist_ok=True)
    diagnostic={}
    for key,item in parts.items():
        if item['role']!='structure':continue
        keep=solid(z[key+'|v'],z[key+'|f']);skin=local_skin(key,p,cfg)
        bridges=item['s']-keep-skin
        components=[x for x in bridges.decompose() if x.volume()>.05]
        r=dict(key=key,body=item['body'],bbox_mm=item['s'].bounding_box(),
            volume_mm3=item['s'].volume(),kept_components=[
                dict(volume_mm3=x.volume(),bbox_mm=x.bounding_box()) for x in keep.decompose() if x.volume()>.05],
            bridge_components=[dict(volume_mm3=x.volume(),bbox_mm=x.bounding_box()) for x in components],
            original_ribs=read(DHISTORY/'candidates'/(key.replace('/','__')+'.json'))['ribs'])
        out.append(r)
        for label,s in [('part',item['s']),('keep',keep),('skin',skin),('bridge',bridges)]:
            if not s.is_empty():diagnostic[key+'|'+label+'|v'],diagnostic[key+'|'+label+'|f']=vf(s)
        print(key,'keeps',len(r['kept_components']),'ribs',len(r['original_ribs']),
              'free bridges',[(round(x['volume_mm3'],1),np.round(np.array(x['bbox_mm'])[3:]-np.array(x['bbox_mm'])[:3],1).tolist()) for x in r['bridge_components']],flush=True)
    np.savez_compressed(EROOT/'connection_diagnostics.npz',**diagnostic)
    put(EROOT/'connection_inventory.json',dict(input_geometry_sha256=DHASH,rows=out,
        note='Inventory only. Connectivity is not an assertion of load capacity.'))


if __name__=='__main__':
    connection_inventory()
