"""Reserve the left upper-arm wire corridor through the shoulder sweep."""
from channel_revo23_harness import *
parts,p,cfg=load_e();seats=read(EROOT/'wire_seats.json')['seats']
body='upperarm_l';r=[s for s in seats if s['body']==body]
a,b=r[:2];M=np.array(a['transform_body_mm'])
pa=np.array(a['wire_center_body_mm']);pb=np.array(b['wire_center_body_mm'])
points=np.linspace(pa,pb,13)
tube=solid(*vf(sweep(points,M[:3,0],M[:3,1],7.3,4.3)))
key='frame/clavicle_l';host=parts[key]['s']
kz=np.load(DHISTORY/'source/retained_interfaces.npz');keep=solid(kz[key+'|v'],kz[key+'|f'])
poses=read(DHISTORY/'profiles/daily_poses.json')['poses'];poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
seen=set();cutters=[];rows=[]
for name,q in poses.items():
    F=frames(p,q);T=np.linalg.inv(F[parts[key]['token']])@F['f:'+body]
    signature=tuple(np.round(T,6).ravel())
    if signature in seen:continue
    seen.add(signature);cut=move(tube,T)
    hit=max(0.,(host^cut).volume())
    if hit<.001:continue
    protected=max(0.,(keep^cut).volume())
    rows.append(dict(pose=name,overlap_mm3=hit,precision_land_overlap_mm3=protected))
    assert protected<.01,('wire route reaches precision land',rows[-1])
    cutters.append(cut)
result=host-union(cutters)
assert len([c for c in result.decompose() if c.volume()>.001])==1
before=screen(key,host,keep,local_skin(key,p,cfg),1.)
after=screen(key,result,keep,local_skin(key,p,cfg),1.)
assert min(x['conservative_cut_area_mm2'] for x in after['rows'])>=100
path=EROOT/'frame__clavicle_l.npz'
backup=EROOT/'checkpoints/before_wire_sweep_relief';backup.mkdir(parents=True,exist_ok=True)
if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
v,f=vf(result);np.savez_compressed(path,v=v,f=f)
put(EROOT/'load_paths_candidate/frame__clavicle_l.json',after)
put(EROOT/'wire_sweep_relief.json',dict(part=key,reserved_for='Left upper-arm fixed wire channel',
    nominal_added_width_and_height_clearance_mm=.8,contacts=rows,pose_count=len(poses),
    removed_volume_mm3=host.volume()-result.volume(),precision_land_loss_mm3=0,
    before=before,after=after))
print('WIRE SWEEP RELIEF',len(rows),'removed',host.volume()-result.volume(),flush=True)
