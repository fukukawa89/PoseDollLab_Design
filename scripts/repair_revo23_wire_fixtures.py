"""Remove two final obstructions found by the independent saved-mesh audit."""
from build_revo23_wire_seats import *
from audit_revo23_load_paths import screen

parts,p,cfg=load_e()
records=read(EROOT/'wire_seats.json')['seats']
kz=np.load(DHISTORY/'source/retained_interfaces.npz')
poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
changes=[]
for seat_id,key in [('upperarm_l:tie2','frame/clavicle_l'),('waist:tie1','frame/waist')]:
    r=next(x for x in records if x['id']==seat_id)
    M=np.array(r['transform_body_mm']);width=r['reserved_channel_width_mm']
    host=parts[key]['s'];keep=solid(kz[key+'|v'],kz[key+'|f'])
    cutters=[];contacts=[]
    if key=='frame/waist':
        cutter=move(box([-width/2-3.1,.6,-1.7],[width/2+3.1,2.4,1.7]),M)
        cutters=[cutter]
    else:
        height=r['reserved_channel_height_mm']
        M[:3,3]=r['wire_center_body_mm']
        wire=solid(*vf(move(box([-width/2-.4,-height/2-.4,-6.4],
                               [width/2+.4,height/2+.4,6.4]),M)))
        seen=set()
        for name,q in poses.items():
            F=frames(p,q);T=np.linalg.inv(F[parts[key]['token']])@F[r['token']]
            sig=tuple(np.round(T,6).ravel())
            if sig in seen:continue
            seen.add(sig);cutter=move(wire,T)
            hit=max(0.,(host^cutter).volume())
            if hit<.001:continue
            contacts.append(dict(pose=name,overlap_mm3=hit));cutters.append(cutter)
    cutter=union(cutters)
    protected=max(0.,(keep^cutter).volume())
    skin_loss=max(0.,(local_skin(key,p,cfg)^cutter).volume())
    assert protected<.01 and skin_loss<.01,(key,protected,skin_loss)
    result=host-cutter
    assert len([c for c in result.decompose() if c.volume()>.001])==1
    v,f=vf(result);assert trimesh.Trimesh(v,f,process=False).is_watertight
    path=EROOT/(key.replace('/','__')+'.npz')
    backup=EROOT/'checkpoints/before_final_wire_relief';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    np.savez_compressed(path,v=v,f=f)
    report=screen(key,result,keep,local_skin(key,p,cfg),1.)
    put(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'),report)
    changes.append(dict(part=key,seat=seat_id,removed_mm3=host.volume()-result.volume(),
        precision_land_loss_mm3=protected,original_skin_loss_mm3=skin_loss,contacts=contacts))
put(EROOT/'final_wire_relief.json',dict(rows=changes))
print('FINAL WIRE RELIEF',changes,flush=True)
