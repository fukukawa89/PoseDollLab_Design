"""O23H: verify both ends of every structural connection against its host.

An overlap volume alone does not establish a seated end face. Host witnesses
exclude the rod under test; source pads must separately seat on native material.
"""
import math
from revo23_smooth import *
from verify_revo23_g import rod_body,wall_pad

GHASH='0c8009b72d72fce6acdf76d06cdcbebd2b16949ee578720b688713e71b34671d'
GHISTORY=B/'history/O23G_before_endface_repair_20261021'
HROOT=B/'design/end_face_candidate'
HREV='O23H-seated-end-faces-20261021'

def initialize():
    HROOT.mkdir(parents=True,exist_ok=True)
    if (GHISTORY/'snapshot.json').exists():
        assert sha(GHISTORY/'assembly.npz')==GHASH
        return
    assert sha(B/'assembly.npz')==GHASH
    files=['assembly.npz','assembly.json','retained_interfaces.npz','DELIVERY.json','DESIGN.zh-CN.md','SMOOTH_CONNECTIONS.zh-CN.md']
    files += [p.relative_to(B).as_posix() for folder in ('profiles','harness','preview') for p in (B/folder).rglob('*') if p.is_file()]
    files += [p.relative_to(B).as_posix() for p in (B/'verification').glob('*.json')]
    for rel in files:
        src=B/rel;dst=GHISTORY/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    shutil.copy2(CFG,GHISTORY/'parameters.json')
    ref=GHISTORY/'connections';ref.mkdir(exist_ok=True)
    for p in GROOT.glob('frame__*.json'):
        if 'rods' in read(p):shutil.copy2(p,ref/p.name)
    skins=GHISTORY/'skins';skins.mkdir(exist_ok=True)
    for p in FROOT.glob('*_skin.npz'):shutil.copy2(p,skins/p.name)
    put(GHISTORY/'snapshot.json',dict(geometry_sha256=GHASH,files={f:sha(GHISTORY/f) for f in files},reason='Source end-cap embedding was not a mandatory G check; preserve before repairing both ends.'))

def load_h():
    initialize();z=np.load(GHISTORY/'assembly.npz');parts={}
    for row in read(GHISTORY/'assembly.json')['items']:
        i=str(row['index']);path=HROOT/(row['key'].replace('/','__')+'.npz')
        if path.exists():
            n=np.load(path);s=solid(n['v'],n['f'])
        else:s=solid(z[i+'v'],z[i+'f'])
        parts[row['key']]=dict(row,s=s)
    return parts,read(GHISTORY/'profiles/device_profile.json'),read(GHISTORY/'parameters.json')

def connection_records(key):
    name=key.replace('/','__')+'.json';p=HROOT/name
    return read(p if p.exists() else GHISTORY/'connections'/name)

def native_keep(key):
    z=np.load(GHISTORY/'retained_interfaces.npz');return solid(z[key+'|v'],z[key+'|f'])

def clean_skin(key):
    z=np.load(GHISTORY/'skins'/(key.replace('/','__')+'_skin.npz'));return solid(z['v'],z['f'])

def face_witness(host,point,outward,radius):
    """The flat end, behind it, and the first 0.6 mm of the entering stem."""
    p=np.asarray(point,float);d=np.asarray(outward,float);d/=np.linalg.norm(d)
    samples=[]
    for depth in (-.8,-.4,0.,.3,.6):
        probe=cyl(p+d*(depth-.04),p+d*(depth+.04),radius)
        samples.append(dict(offset_mm=depth,covered_fraction=max(0.,min(1.,(probe^host).volume()/probe.volume()))))
    stem=cyl(p,p+d*.6,radius)
    covered=max(0.,min(1.,(stem^host).volume()/stem.volume()))
    minimum=min(r['covered_fraction'] for r in samples)
    return dict(point_world_mm=p,outward_world=d,radius_mm=radius,area_mm2=math.pi*radius**2,
        samples=samples,minimum_face_coverage=minimum,first_stem_coverage=covered,
        passed=minimum>=.98 and covered>=.98)

def socket_solid(f):
    b=np.array(f['base_world_mm']);d=np.array(f['normal_world']);u=np.array(f['u_world']);v=np.cross(d,u)
    w,h=f['width_mm'],f['height_mm'];angle=np.linspace(0,2*np.pi,48,endpoint=False)
    base=np.array([b+x*u+y*v for x,y in itertools.product((-w/2,w/2),(-h/2,h/2))])
    e=np.array(f.get('top_normal_world',d));tu=u-e*(u@e)
    if np.linalg.norm(tu)<.01:tu=v-e*(v@e)
    tu/=np.linalg.norm(tu);tv=np.cross(e,tu)
    top=b+d*f['depth_mm']+np.array(f.get('top_offset_world_mm',[0,0,0]))+f['top_radius_mm']*(np.cos(angle)[:,None]*tu+np.sin(angle)[:,None]*tv)
    socket_length=f.get('socket_length_mm',0.)
    socket=cyl(b+d*f['depth_mm']+np.array(f.get('top_offset_world_mm',[0,0,0]))-e*socket_length,
               b+d*f['depth_mm']+np.array(f.get('top_offset_world_mm',[0,0,0])),f['top_radius_mm']) if socket_length else md.Manifold()
    if socket_length:top=top-e*(socket_length-.5)
    neck=f.get('neck_mm',0.)
    if not neck:return md.Manifold.hull_points(np.vstack([base,top]))+socket
    shoulder=base+d*neck
    return md.Manifold.hull_points(np.vstack([base,shoulder]))+md.Manifold.hull_points(np.vstack([base+d*(neck-.5),top]))+socket

def socket_base_witness(host,f):
    b=np.array(f['base_world_mm']);d=np.array(f['normal_world']);u=np.array(f['u_world']);v=np.cross(d,u)
    M=np.eye(4);M[:3,:3]=np.c_[u,v,d];M[:3,3]=b;w,h=f['width_mm'],f['height_mm'];rows=[]
    for depth in (-.6,-.3,0.,.3):
        probe=move(box([-w/2,-h/2,depth-.04],[w/2,h/2,depth+.04]),M)
        rows.append(dict(offset_mm=depth,covered_fraction=(probe^host).volume()/probe.volume()))
    minimum=min(r['covered_fraction'] for r in rows)
    # The adapter itself must actually end at the specified flat base plane.
    vertices,_=vf(socket_solid(f));behind=float(np.min((vertices-b)@d))
    return dict(area_mm2=w*h,samples=rows,minimum_face_coverage=minimum,
        material_behind_base_plane_mm=max(0.,-behind),passed=minimum>=.98 and behind>=-.001)

def mount_reinforcement(key):
    path=HROOT/'mount_reinforcement'/(key.replace('/','__')+'.npz')
    paths=([path] if path.exists() else [])+list((HROOT/'mount_reinforcement').glob(key.replace('/','__')+'__m*.npz'))
    solids=[]
    for path in paths:
        z=np.load(path);solids.append(solid(z['v'],z['f']))
    return union(solids)

def native_hosts(key,parts,p,N,baseline=False):
    M=N[parts[key]['token']]
    hosts=[move(c,M) for c in sorted([x for x in native_keep(key).decompose() if x.volume()>.05],key=lambda s:-s.volume())]
    path=HROOT/'mount_reinforcement'/(key.replace('/','__')+'.json')
    paths=([path] if path.exists() else [])+list((HROOT/'mount_reinforcement').glob(key.replace('/','__')+'__m*.json'))
    if not baseline:
        for path in paths:
            record=read(path);z=np.load(path.with_suffix('.npz'));hosts[record['mount']]+=move(solid(z['v'],z['f']),M)
    return hosts

def audit(parts,p,label='candidate',baseline=False):
    N=frames(p,p['neutral_raw_deg']);rows=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        records=read(GHISTORY/'connections'/(key.replace('/','__')+'.json')) if baseline else connection_records(key);hosts=native_hosts(key,parts,p,N,baseline)
        for i,r in enumerate(records['rods']):
            points=np.array(r['centerline_world_mm']);start_dir=points[1]-points[0];start_dir/=np.linalg.norm(start_dir)
            source=face_witness(hosts[r['mount']],points[0],start_dir,r['radius_mm'])
            pads=[]
            for foot in r.get('source_feet',[]):
                a=np.array(foot['start_world_mm']);b=np.array(foot['end_world_mm'])
                base=face_witness(hosts[r['mount']],b,a-b,foot['r1_mm'])
                s=tapered(a,b,foot['r0_mm'],foot['r1_mm']);join=face_witness(s,points[0],start_dir,r['radius_mm'])
                pads.append(dict(base=base,rod_end=join,passed=base['passed'] and join['passed']))
            source_ok=source['passed'] or any(x['passed'] for x in pads)
            if 'source_socket' in r:
                f=r['source_socket'];base=socket_base_witness(hosts[r['mount']],f)
                join=face_witness(socket_solid(f),points[0],start_dir,r['radius_mm'])
                pads.append(dict(base=base,rod_end=join,passed=base['passed'] and join['passed']))
                source_ok=source_ok or pads[-1]['passed']
            end_dir=points[-2]-points[-1]
            if 'target_mount' in r:
                target=face_witness(hosts[r['target_mount']],points[-1],end_dir,r['radius_mm']);wall=None
                if 'target_socket' in r:
                    f=r['target_socket'];base=socket_base_witness(hosts[r['target_mount']],f)
                    join=face_witness(socket_solid(f),points[-1],end_dir,r['radius_mm'])
                    target=dict(native_end=target,base=base,rod_end=join,minimum_face_coverage=join['minimum_face_coverage'],passed=base['passed'] and join['passed'])
            else:
                target=face_witness(wall_pad(r),points[-1],end_dir,r['radius_mm'])
                pos=np.array(r['wall_landing_world_mm']);n=pos-np.array(r.get('wall_foot_reference_endpoint_world_mm',points[-1]));n/=np.linalg.norm(n)
                tip=r.get('foot_tip_mm',1.8);disk=cyl(pos-n*(tip+.2),pos-n*tip,r['radius_mm']+2.5)
                wall=dict(bond_disk_fraction=(disk^move(clean_skin(key),N[item['token']])).volume()/disk.volume())
                wall['passed']=wall['bond_disk_fraction']>=.9599
            # Existing records may use a wall foot as the entire short connector.
            row=dict(part=key,index=i,mount=r['mount'],target_mount=r.get('target_mount'),foot_only=r.get('foot_only',False),
                source=source,source_feet=pads,target=target,wall=wall,
                passed=source_ok and target['passed'] and (wall is None or wall['passed']))
            rows.append(row)
            print('END FACE',key,i,'source',round(source['minimum_face_coverage'],3),'target',round(target['minimum_face_coverage'],3),'PASS',row['passed'],flush=True)
    out=dict(revision=GREV if baseline else HREV,baseline_geometry_sha256=GHASH,rows=rows,rods=len(rows),failed_rods=sum(not r['passed'] for r in rows),
        affected_parts=sorted({r['part'] for r in rows if not r['passed']}),passed=all(r['passed'] for r in rows),
        method='Both flat rod ends checked against separately identified host material at -0.8,-0.4,0,+0.3,+0.6 mm; 0.08 mm witness slabs, >=98% disk and first-stem coverage. Source pads additionally checked against native land. Not physical strength certification.')
    if not baseline:
        out['geometry_sha256']=sha(HROOT/'assembly.npz') if (HROOT/'assembly.npz').exists() else None
        out['candidate_part_hashes']={key:sha(HROOT/(key.replace('/','__')+'.npz')) for key,item in parts.items() if item['role']=='structure'}
    put(HROOT/(label+'_end_faces.json'),out);return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',action='store_true');args=ap.parse_args()
    parts,p,cfg=load_h();r=audit(parts,p,'baseline' if args.baseline else 'candidate',args.baseline);print('FAILED',r['failed_rods'],'/',r['rods'],'PARTS',r['affected_parts'],flush=True)
