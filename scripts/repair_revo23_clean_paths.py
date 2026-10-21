"""Add a counted alternative connection where a sparse path meets a thin edge."""
from build_revo23_clean_connections import *
import build_revo23_clean_connections as connections
from channel_revo23_harness import sweep
from audit_revo23_load_paths import screen


def wire_voids(key):
    shapes=[]
    for r in read(FROOT/'wire_seats.json')['seats']:
        if r['part']!=key:continue
        M=np.array(r['transform_body_mm']);width=r['reserved_channel_width_mm'];height=r['reserved_channel_height_mm']
        low,high=(1.3,3.3) if r.get('minimum_roof_thickness_mm')==2.7 else (.6,2.4)
        shapes.append(move(box([-width/2-3.1,low,-1.7],[width/2+3.1,high,1.7]),M))
        W=M.copy();W[:3,3]=r['wire_center_body_mm'];half=4.5 if r['body'].startswith('forearm_') else 6.
        shapes.append(move(box([-width/2,-height/2,-half],[width/2,height/2,half]),W))
    if (FROOT/'wire_channels.json').exists():
        seats=read(FROOT/'wire_seats.json')['seats']
        for r in read(FROOT/'wire_channels.json')['rows']:
            if r['part']!=key or not r['channel_open_in_actual_print']:continue
            a=next(s for s in seats if s['id']==r['a']);M=np.array(a['transform_body_mm'])
            shapes.append(sweep(np.array(r['centerline_body_mm']),M[:3,0],M[:3,1],r['width_mm'],r['height_mm']))
    return union(shapes)


def repair(key,land_index,radius=6.5,target_index=None):
    parts,p,cfg=load_f();base,_,_=load_e_snapshot();N=frames(p,p['neutral_raw_deg'])
    kz=np.load(EHISTORY/'source/retained_interfaces.npz')
    keep=source_keep(key,kz,base[key],p,N)
    lands=sorted([c for c in keep.decompose() if c.volume()>50],key=lambda x:-x.volume())
    path=FROOT/(key.replace('/','__')+'.npz');r=read(path.with_suffix('.json'))
    z=np.load(path.with_name(path.stem+'_skin.npz'));skin=solid(z['v'],z['f'])
    source=lands[land_index]
    target=lands[target_index] if target_index is not None else skin
    if target.is_empty():target=union([c for i,c in enumerate(lands) if i!=land_index])
    original=parts[key]['s']
    before=screen(key,original,keep,skin,1)
    row=next(x for x in before['rows'] if x['land']==land_index)
    cut=np.array(row['cut_center_mm']);guard=max(4,min(9,row['cut_spread_mm']*.55))
    voids=wire_voids(key)
    allowed=solid(*vf((base[key]['s']+skin)-voids))
    search=solid(*vf(allowed-ball(cut,guard)))
    connections._grid_cache.clear()
    points=safe_route(search,source,target)
    if points is None:
        search=solid(*vf(allowed-ball(cut,max(3,guard*.6))))
        points=safe_route(search,source,target)
    assert points is not None,('No alternative route',key,land_index)
    beam=solid(*vf(route_shape(points,radius)^allowed))
    candidate=solid(*vf(original+beam))
    cc=candidate.decompose()
    debris=sum(max(0,c.volume()) for c in cc if c.volume()<.01)
    assert debris<.02
    candidate=max(cc,key=lambda c:c.volume())
    assert (original-candidate).volume()<.02,('Alternative loses original material',key)
    after=screen(key,candidate,keep,skin,1)
    new=next(x for x in after['rows'] if x['land']==land_index)
    assert new['conservative_cut_area_mm2']>row['conservative_cut_area_mm2']+1,('No area improvement',key)
    count=sum(x['mount']==land_index for x in r['rods'])
    assert count<3,('Three rod limit',key,land_index)
    candidate=save_s(path,candidate)
    r['rods'].append(dict(id=f'{key}/mount_{land_index}/rod_{count+1}',mount=land_index,
        rod_count=1,radius_mm=radius,centerline_body_mm=points,clipped_volume_mm3=beam.volume(),
        target_mount=target_index,
        reason='Alternative broad attachment avoiding the measured thin section.'))
    r.update(candidate_sha256=sha(path),volume_mm3=candidate.volume())
    put(path.with_suffix('.json'),r)
    after['candidate_sha256']=sha(path);put(FROOT/'load_paths'/(path.stem+'.json'),after)
    print('REPAIRED',key,land_index,round(row['conservative_cut_area_mm2'],2),
          '->',round(new['conservative_cut_area_mm2'],2),'rod',count+1,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('land',type=int)
    ap.add_argument('--radius',type=float,default=6.5);ap.add_argument('--target',type=int)
    a=ap.parse_args();repair(a.key,a.land,a.radius,a.target)
