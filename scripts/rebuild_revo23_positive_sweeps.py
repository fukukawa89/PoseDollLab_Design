"""Rebuild bent beams from positive convex cells and remove redundant free stubs."""
from revo23_smooth import *
from verify_revo23_g import rod_body,wall_pad
from build_revo23_wire_seats import saddle
from channel_revo23_harness import sweep

parts,p,cfg=load_g();N=frames(p,p['neutral_raw_deg']);seats=read(GROOT/'wire_seats.json')['seats'];channels=read(GROOT/'wire_channels.json')['rows']
backup=GROOT/'checkpoints/before_positive_sweeps';backup.mkdir(parents=True,exist_ok=True)
for name in ('assembly.npz','assembly.json','staging.json','daily_motion.json','edge_motion.json'):
    if not (backup/name).exists():shutil.copy2(GROOT/name,backup/name)
results=[]
for key,item in parts.items():
    if item['role']!='structure':continue
    path=GROOT/(key.replace('/','__')+'.npz');report=read(path.with_suffix('.json'))
    for source in (path,path.with_suffix('.json')):
        if not (backup/source.name).exists():shutil.copy2(source,backup/source.name)
    M=N[item['token']];I=np.linalg.inv(M);keep=raw_keep(key,parts,p,N);skin=skin_of(key);material=[keep,skin];removed_stubs=0
    for r in report['rods']:
        r['positive_cells']=True;r['foot_tip_mm']=1.3 if item['body'].startswith('ball_') else 1.8
        r['foot_depth_mm']=7. if item['body'].startswith(('forearm_','elbow_','ball_')) else 13.
        body=move(rod_body(r),I)
        if 'target_mount' not in r:
            foot=move(wall_pad(r),I)
            if key.startswith('frame/thigh_') and (body^keep).volume()<1. and (foot^keep).volume()>1.:
                r['foot_only']=True;r['method']='One smooth, broad integral wall foot; redundant free cylinder removed.';body=foot;removed_stubs+=1
            material.append(foot)
        material.append(body)
        for foot in r.get('source_feet',[]):material.append(move(tapered(foot['start_world_mm'],foot['end_world_mm'],foot['r0_mm'],foot['r1_mm']),I))
    base=union(material);pads=[];voids=[];geom=canonical(item['body'],M,cfg);outer=move(geom[1],I@geom[3]) if geom else None
    for r in seats:
        if r['part']!=key:continue
        w=r['reserved_channel_width_mm'];h=r['reserved_channel_height_mm'];half=4.5 if r['body'].startswith('forearm_') else 6.
        C=np.array(r['transform_body_mm']);pad,tunnel=saddle(w,half);pad=move(pad,C)
        if outer is not None:pad=pad^outer
        pads.append(pad);voids.extend([move(tunnel,C),move(box([-w/2,4.95,-half],[w/2,4.95+h,half]),C)])
    for r in channels:
        if r['part']!=key or not r['channel_open_in_actual_print']:continue
        seat=next(s for s in seats if s['id']==r['a']);C=np.array(seat['transform_body_mm'])
        voids.append(sweep(np.array(r['centerline_body_mm']),C[:3,0],C[:3,1],r['width_mm'],r['height_mm']))
    void=union(voids);conflict=max(0.,(base^void).volume());result=(base+union(pads))-void
    report['positive_cell_rebuild']=dict(wire_space_intersection_mm3=conflict,redundant_free_cylinders_removed=removed_stubs,
        method='Boolean union of individually convex ring-to-ring cells. No self-overlapping single tube surface and no spherical bend nodes.')
    if conflict>.03:
        print('WIRE REPOSITION REQUIRED',key,conflict,flush=True)
        save_s(GROOT/(path.stem+'_positive_base.npz'),base);results.append(dict(key=key,passed=False,reason='wire',conflict_mm3=conflict));continue
    cc=[c for c in result.decompose() if c.volume()>.001]
    if len(cc)!=1:
        print('CONNECTED PATH REQUIRED',key,[c.volume() for c in cc],flush=True);results.append(dict(key=key,passed=False,reason='components'));continue
    save_s(path,result);report['candidate_sha256']=sha(path);report['volume_mm3']=result.volume();put(path.with_suffix('.json'),report)
    results.append(dict(key=key,passed=True,source_hash=sha(backup/path.name),candidate_sha256=sha(path),removed_free_cylinders=removed_stubs,volume_mm3=result.volume()))
    print('POSITIVE CELLS',key,'removed stubs',removed_stubs,'volume',result.volume(),flush=True)
put(GROOT/'positive_sweep_rebuild.json',dict(rows=results,passed=all(r['passed'] for r in results)))
