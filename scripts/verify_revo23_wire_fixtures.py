"""Verify the saved printed seats, open strap tunnels and reserved wire spaces."""
from build_revo23_wire_seats import *
from channel_revo23_harness import sweep

parts,p,cfg=load_e();data=read(EROOT/'wire_seats.json')
poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
FF={n:frames(p,q) for n,q in poses.items()};rows=[]
for r in data['seats']:
    M=np.array(r['transform_body_mm']);host=parts[r['part']]['s']
    width=r['reserved_channel_width_mm'];height=r['reserved_channel_height_mm']
    legacy=r.get('minimum_roof_thickness_mm')==2.7
    low,high=(1.3,3.3) if legacy else (.6,2.4)
    tunnel=move(box([-width/2-3.1,low,-1.7],[width/2+3.1,high,1.7]),M)
    roof=move(box([-width/2+.2,3.6 if legacy else 2.7,-1.5],
                  [width/2-.2,5.5 if legacy else 4.5,1.5]),M)
    # Reserve exactly the recorded channel section, at its recorded location.
    W=M.copy();W[:3,3]=r['wire_center_body_mm']
    half=4.5 if r['body'].startswith('forearm_') else 6.
    wire=solid(*vf(move(box([-width/2,-height/2,-half],[width/2,height/2,half]),W)))
    roof_fraction=(roof^host).volume()/roof.volume()
    blocked_tunnel=max(0.,(tunnel^host).volume());blocked_wire=max(0.,(wire^host).volume())
    contacts=[];bb=np.array(wire.bounding_box())
    for other,pose,ob,_ in obstacle_transforms(r['part'],parts,p,FF,bb):
        overlap=max(0.,(wire^ob).volume())
        if overlap>.03:contacts.append(dict(other=other,pose=pose,overlap_mm3=overlap))
    row=dict(id=r['id'],part=r['part'],strap_tunnel_blocked_mm3=blocked_tunnel,
        roof_probe_solid_fraction=roof_fraction,wire_space_blocked_by_host_mm3=blocked_wire,
        wire_space_adjacent_contacts=contacts,
        passed=blocked_tunnel<.03 and roof_fraction>.98 and blocked_wire<.03 and not contacts)
    rows.append(row);print('FIXTURE',r['id'],row['passed'],'roof',round(roof_fraction,3),
        'slot',round(blocked_tunnel,4),'wire',round(blocked_wire,4),'contacts',len(contacts),flush=True)
channel_rows=[]
for r in read(EROOT/'wire_channels.json')['rows']:
    if not r['channel_open_in_actual_print']:
        channel_rows.append(dict(part=r['part'],passed=False,reason='No verified channel'));continue
    a=next(s for s in data['seats'] if s['id']==r['a']);M=np.array(a['transform_body_mm'])
    tube=solid(*vf(sweep(np.array(r['centerline_body_mm']),M[:3,0],M[:3,1],r['width_mm'],r['height_mm'])))
    blocked=max(0.,(tube^parts[r['part']]['s']).volume())
    channel_rows.append(dict(part=r['part'],blocked_by_final_print_mm3=blocked,passed=blocked<.03))
report=dict(candidate_mesh_hashes={k:sha(EROOT/(k.replace('/','__')+'.npz')) for k in
    sorted({r['part'] for r in data['seats']})},pose_count=len(FF),seats=rows,channels=channel_rows,
    passed=all(r['passed'] for r in rows+channel_rows),
    physical_threading_and_repeated_flex_tested=False,
    scope='Actual saved geometry: strap tunnels, bearing roofs, reserved bundle spaces and fixed internal channels. Flexible joint loops are not simulated as rigid solids.')
put(EROOT/'wire_fixture_verification.json',report)
print('WIRE FIXTURE RESULT',report['passed'],flush=True)
