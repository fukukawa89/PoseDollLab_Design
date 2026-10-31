"""Regress actual repaired STL round trips against the unchanged O23G assembly."""
from revo23_export import *
from present_revo23 import load_current
from verify_revo23_daily import check_daily
from revo23_daily import rigid_groups
import time

OUT=EXPORT_ROOT/'verification'

def inputs():
    parts=load_current();report=read(EXPORT_ROOT/'repair.json');hashes={}
    for r in report['rows']:
        path=B/r['staged_stl'];assert sha(path)==r['stl_sha256']
        m=trimesh.load(path,process=True);assert m.is_watertight and m.is_winding_consistent
        parts[r['key']]['s']=solid(m.vertices,m.faces);hashes[r['key']]=sha(path)
    digest=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    return parts,read(B/'profiles/device_profile.json'),hashes,digest

def bind(r,digest):
    r.update(geometry_sha256=sha(B/'assembly.npz'),profile_sha256=sha(B/'profiles/device_profile.json'),export_set_sha256=digest)
    return r

def motion(mode):
    parts,p,hashes,digest=inputs();spec=read(B/'profiles'/('daily_poses.json' if mode=='daily' else 'edge_path_poses.json'))
    path=OUT/(mode+'_motion.json');path.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
    r=check_daily(parts,p,spec['poses'],spec.get('policy',{}).get('poses',[]),digest,focus=set(hashes),output=path)
    baseline=B/'verification'/('daily_motion.json' if mode=='daily' else 'edge_paths.json');old=read(baseline)
    assert old['passed'] and old['geometry_sha256']==sha(B/'assembly.npz')
    r.update(complete_policy=True,export_stl_hashes=hashes,unchanged_pairs_inherited_from=baseline.relative_to(B).as_posix(),
        unchanged_pairs_baseline_sha256=sha(baseline),unchanged_assembly_sha256=sha(B/'assembly.npz'),
        scope='Every moving pair involving any of the 32 actual STL round trips at every original pose. Other pairs inherit the byte-identical passing G assembly.')
    put(path,bind(r,digest));print('EXPORT MOTION',mode,r['passed'],flush=True)

def features():
    parts,p,hashes,digest=inputs()
    import verify_revo23_g as g
    g.put=lambda path,r:put(OUT/Path(path).name,bind(r,digest))
    g.materials(parts,p)
    original=load_current();diff=[]
    for key in hashes:
        s=original[key]['s'];c=parts[key]['s']
        removed=max(0.,(s-c).volume());added=max(0.,(c-s).volume())
        r=read(EXPORT_ROOT/(key.replace('/','__')+'.json'))
        if r.get('numeric_island_removal'):
            # Explicit, local exception for a disconnected numerical tetrahedron,
            # not a general tolerance change. Re-evaluate its complete mesh.
            assert r['main_surface_displacement_bound_mm']<.0011
            assert len(r['numeric_island_removal'])<=2
            actual=trimesh.Trimesh(*vf(c),process=False)
            for island in r['numeric_island_removal']:
                mesh=trimesh.Trimesh(island['vertices'],island['faces'],process=False)
                assert mesh.is_watertight and 0<mesh.volume<1e-4 and len(mesh.faces)<=12 and max(mesh.extents)<.5
                _,distance,_=trimesh.proximity.closest_point(actual,np.vstack([mesh.vertices,mesh.triangles_center]))
                assert float(distance.max())<.030001
        else:assert r['surface_displacement_bound_mm']<.0011
        diff.append(dict(key=key,removed_mm3=removed,added_mm3=added,
            volume_relative_difference=abs(c.volume()-s.volume())/s.volume(),
            declared_surface_bound_mm=r['surface_displacement_bound_mm'],numeric_island_removal=r.get('numeric_island_removal',[])))
    put(OUT/'geometry_difference.json',bind(dict(rows=diff,source_assembly_unchanged=True,
        max_declared_surface_bound_mm=max(r['declared_surface_bound_mm'] for r in diff),
        passed=max(r['volume_relative_difference'] for r in diff)<1e-5),digest))
    from channel_revo23_harness import sweep
    from build_revo23_reinforced import obstacle_transforms
    poses=dict(read(B/'profiles/daily_poses.json')['poses']);poses.update(read(B/'profiles/edge_path_poses.json')['poses'])
    FF={name:frames(p,q) for name,q in poses.items()};data=read(B/'harness/wire_seats.json');rows=[]
    for r in data['seats']:
        M=np.array(r['transform_body_mm']);host=parts[r['part']]['s'];width=r['reserved_channel_width_mm'];height=r['reserved_channel_height_mm']
        legacy=r.get('minimum_roof_thickness_mm')==2.7;low,high=(1.3,3.3) if legacy else (.6,2.4)
        tunnel=move(box([-width/2-3.1,low,-1.7],[width/2+3.1,high,1.7]),M)
        roof=move(box([-width/2+.2,3.6 if legacy else 2.7,-1.5],[width/2-.2,5.5 if legacy else 4.5,1.5]),M)
        W=M.copy();W[:3,3]=r['wire_center_body_mm'];half=4.5 if r['body'].startswith('forearm_') else 6.
        wire=move(box([-width/2,-height/2,-half],[width/2,height/2,half]),W)
        roof_fraction=(roof^host).volume()/roof.volume();blocked_tunnel=max(0.,(tunnel^host).volume());blocked_wire=max(0.,(wire^host).volume())
        contacts=[]
        for other,pose,ob,_ in obstacle_transforms(r['part'],parts,p,FF,np.array(wire.bounding_box())):
            overlap=max(0.,(wire^ob).volume())
            if overlap>.03:contacts.append(dict(other=other,pose=pose,overlap_mm3=overlap))
        row=dict(id=r['id'],part=r['part'],strap_tunnel_blocked_mm3=blocked_tunnel,roof_probe_solid_fraction=roof_fraction,
            wire_space_blocked_by_host_mm3=blocked_wire,wire_space_adjacent_contacts=contacts,
            passed=blocked_tunnel<.03 and roof_fraction>.98 and blocked_wire<.03 and not contacts)
        rows.append(row);print('EXPORT WIRE',r['id'],row['passed'],flush=True)
    channels=[]
    for r in read(B/'harness/wire_channels.json')['rows']:
        a=next(s for s in data['seats'] if s['id']==r['a']);M=np.array(a['transform_body_mm'])
        tube=sweep(np.array(r['centerline_body_mm']),M[:3,0],M[:3,1],r['width_mm'],r['height_mm'])
        blocked=max(0.,(tube^parts[r['part']]['s']).volume());channels.append(dict(part=r['part'],blocked_mm3=blocked,passed=blocked<.03))
    put(OUT/'wire_fixtures.json',bind(dict(seats=rows,channels=channels,pose_count=len(FF),passed=all(r['passed'] for r in rows+channels),physical_flex_tested=False),digest))
    print('EXPORT FEATURES FINISHED',flush=True)

def fixed():
    parts,p,hashes,digest=inputs()
    import verify_revo23 as v
    v.cases=lambda profile,suite:{'A_STAND_35':read(B/'profiles/default_pose.json')['raw_deg']}
    base,_,_=v.load_baseline();result=v.motion(parts,base,p,'fixed_reference')
    groups=rigid_groups(p,{x['token'] for x in parts.values()})
    rows=[r for case in result['rows'] for r in case['contacts'] if groups[parts[r['pair'][0]]['token']]==groups[parts[r['pair'][1]]['token']]]
    hits=[r for r in rows if r['increased']]
    put(OUT/'fixed_interfaces.json',bind(dict(rows=rows,new_contacts=hits,passed=not hits),digest))
    print('EXPORT FIXED',not hits,len(hits),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['daily','edge','features','fixed']);a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if a.mode in ('daily','edge'):motion(a.mode)
    elif a.mode=='features':features()
    else:fixed()
