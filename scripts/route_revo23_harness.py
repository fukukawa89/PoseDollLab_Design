"""46 independent five-core routes through actual printed O23E tie locations.

Straight links are dimensional routing guides. Moving spans are loose service
loops, not rigid cylinders. Their length bounds use all daily and transition
poses; physical routing, pinching and repeated-flex qualification remain open.
"""
from build_revo23_wire_seats import *
import csv


def main():
    parts,p,cfg=load_e();seats=read(EROOT/'wire_seats.json')['seats']
    bybody={}
    for r in seats:
        if r['part'].startswith('frame/'):bybody.setdefault(r['body'],[]).append(r)
    channels=read(EROOT/'wire_channels.json')['rows'] if (EROOT/'wire_channels.json').exists() else []
    channels={frozenset((r['a'],r['b'])):r for r in channels if r['channel_open_in_actual_print']}
    F0=frames(p,p['neutral_raw_deg']);poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
    poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
    FF={n:frames(p,q) for n,q in poses.items()}
    groups=rigid_groups(p,{v['token'] for v in parts.values()})
    parent={j['child']:j['parent'] for j in p['joints']};joints={j['id']:j for j in p['joints']}
    nodes=[n for bank in read(H/'bench/revO22/profiles/wiring.json')['banks'] for n in bank['nodes']]
    footprints=read(B/'electronics/carrier/placement.json')['footprints']
    C=np.array(read(B/'design/compact_revision.json')['controller_frame_neutral_mm'])
    C[:3,3]=cfg['controller_front_corner_neutral_mm'];T=np.linalg.inv(F0['f:chest'])@C
    use={r['id']:[] for r in seats};rows=[];links={}
    def world(point,F):
        return (F[point['token']]@np.r_[point['point_body_mm'],1])[:3]
    def anchor(r):
        return dict(id=r['id'],token=r['token'],point_body_mm=r['wire_center_body_mm'])
    def lineage(body):
        chain=[]
        while body not in chain:
            chain.append(body)
            if body=='chest':break
            body='waist' if body=='pelvis' else ('chest' if body=='waist' else parent[body])
        return chain
    for n in nodes:
        sensor=n['sensor_part_O20']
        for side in ('l','r'):
            if sensor==f'hand_{side}.flex/sensor_PCB':sensor=f'wrist_{side}/C02_sensor_PCB'
            if sensor==f'hand_{side}.deviate/sensor_PCB':sensor=f'wrist_{side}/C01_sensor_PCB'
        s=parts[sensor+'/wire_solder'];bb=np.array(s['s'].bounding_box());point=(bb[:3]+bb[3:])/2
        pb=np.array(parts[sensor+'/pcb']['s'].bounding_box());pc=(pb[:3]+pb[3:])/2
        direction=point-pc;direction/=np.linalg.norm(direction)
        start=dict(id=n['raw_id']+':solder',token=s['token'],point_body_mm=point)
        exitpoint=dict(id=n['raw_id']+':pigtail',token=s['token'],point_body_mm=point+direction*6)
        body=s['body']
        if body.startswith('hand_'):body=body.replace('hand_','forearm_')
        if body.endswith('.dorsiflex_frame'):body=body.split('.')[0].replace('foot_','calf_')
        if '/' in body:
            joint=joints[body.split('/')[0]]
            # Shoulder/hip/neck ring boards return toward the trunk. Routing
            # them down the distal limb would create unnecessary wire bulk.
            body=joint['child'] if joint['id'] in ('waist','chest') else joint['parent']
        chain=lineage(body);points=[start,exitpoint]
        side='l' if '_l' in n['raw_id'] else ('r' if '_r' in n['raw_id'] else None)
        for b in chain:
            available=bybody.get(b,[])
            if not available:continue
            if b in ('pelvis','waist','chest'):
                # Separate trunk bundles use separate saddles; do not route all
                # 230 cores serially through one small tie.
                if side:
                    target=1 if side=='l' else -1
                    selected=min(available,key=lambda a:-target*world(anchor(a),F0)[1])
                else:selected=min(available,key=lambda a:len(use[a['id']]))
                ordered=[selected]
            else:
                previous=world(points[-1],F0)
                ordered=sorted(available,key=lambda a:np.linalg.norm(world(anchor(a),F0)-previous))
            for a in ordered:points.append(anchor(a));use[a['id']].append(n['raw_id'])
        connector=next(r for r in footprints if r['value'].startswith(n['connector']+' '))
        z=8.0 if connector['side']=='B' else 22.
        port=dict(id=n['connector'],token='f:chest',
                  point_body_mm=(T@np.array([connector['x_mm'],connector['y_mm'],z,1]))[:3])
        case=min([r for r in seats if r['part']=='o22/controller_housing'],
            key=lambda a:np.linalg.norm(world(anchor(a),F0)-world(port,F0))+
            max(0,len(use[a['id']])-22)*1000)
        points.append(anchor(case));use[case['id']].append(n['raw_id']);points.append(port)
        route_links=[];length=0.
        for a,b in zip(points,points[1:]):
            k=a['id']+' -> '+b['id']
            if k not in links:
                fixed=groups[a['token']]==groups[b['token']]
                nominal=float(np.linalg.norm(world(a,F0)-world(b,F0)))
                distances=[(float(np.linalg.norm(world(a,F)-world(b,F))),name) for name,F in FF.items()]
                maximum,witness=max(distances);minimum=min(x[0] for x in distances)
                corridor=channels.get(frozenset((a['id'],b['id'])))
                if corridor:
                    path=np.array(corridor['centerline_body_mm'])
                    nominal=maximum=minimum=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum())
                allowance=0. if fixed else math.pi*10+20
                links[k]=dict(a=a,b=b,rigid_span=fixed,neutral_separation_mm=nominal,
                    sampled_minimum_separation_mm=minimum,sampled_maximum_separation_mm=maximum,
                    maximum_witness=witness,untied_service_loop_extra_mm=allowance,
                    allocated_wire_length_mm=maximum+allowance,nominal_bend_radius_mm=None if fixed else 10,
                    printed_corridor=corridor,
                    loose_loop=True if not fixed else False,straight_line_is_not_final_cable_shape=True)
            route_links.append(k);length+=links[k]['allocated_wire_length_mm']
        length=int(math.ceil((length+40)/25)*25)
        rows.append(dict(raw_id=n['raw_id'],connector=n['connector'],carrier_reference=connector['reference'],
            sensor_part=sensor,points=points,anchor_chain=chain,links=route_links,
            preliminary_cut_each_of_five_wires_mm=length,termination_allowance_mm=40,
            cut_length_released=False,physical_route_verified=False))
    capacities=[]
    for r in seats:
        count=len(use[r['id']])*5
        capacities.append(dict(id=r['id'],used_cores=count,capacity_cores=r['maximum_cores_at_OD_0p7'],
            passed=count<=r['maximum_cores_at_OD_0p7'],sensor_channels=use[r['id']]))
    channel_capacities=[]
    for corridor in channels.values():
        users=[r['raw_id'] for r in rows if any(
            links[k]['printed_corridor'] and
            links[k]['printed_corridor']['part']==corridor['part'] for k in r['links'])]
        count=len(users)*5
        # The continuous corridor is elliptical, unlike each seat's rectangular
        # reserved space. Check its smaller actual area, not its bounding box.
        area=math.pi*corridor['width_mm']*corridor['height_mm']/4
        packing=count*math.pi*.7**2/4/area
        channel_capacities.append(dict(part=corridor['part'],used_cores=count,
            elliptical_area_mm2=area,packing_fraction=packing,
            maximum_design_packing_fraction=.6,passed=packing<=.6,sensor_channels=users))
    out=EROOT/'harness';out.mkdir(exist_ok=True)
    report=dict(schema='POSEDOLL-O23E-HARNESS/1',input_geometry_sha256=DHASH,
        rows=rows,links=links,seats=seats,capacity_checks=capacities,
        capacity_passed=all(r['passed'] for r in capacities+channel_capacities),
        channel_capacity_checks=channel_capacities,
        body_sections_with_seats=sorted(bybody),
        body_sections_missing_seats=[r['body'] for r in parts.values() if r['role']=='structure'
            and not r['body'].startswith(('hand_','ball_')) and r['body'] not in bybody],
        sensor_count=46,conductors_per_sensor=5,independent_home_runs=True,daisy_chain=False,
        wire_spec=dict(conductor='AWG30 flexible fine-stranded copper',
            maximum_insulated_OD_mm=.7,conductor_resistance_ohm_per_m_max_at_test_temperature=.4,
            nominal_service_bend_radius_mm=10,
            minimum_supplier_bend_radius_and_flex_rating='Must support the actual assembly; not inferred from AWG'),
        pin_order=['GND black','SENSOR_3V45 red','CLK blue','DO green','CSN yellow'],
        pose_samples=len(FF),maximum_preliminary_length_mm=max(r['preliminary_cut_each_of_five_wires_mm'] for r in rows),
        preliminary_active_m_each_color=sum(r['preliminary_cut_each_of_five_wires_mm'] for r in rows)/1000,
        physical_pinch_and_fatigue_verified=False,electrical_long_cable_signal_integrity_verified=False,
        note='Tie saddles are printed CAD geometry. These flexible routes are dimensional guides, not a collision-free cable or fatigue simulation. Trim only after first-article fitting.')
    put(out/'routing_plan.json',report)
    with (out/'preliminary_cut_list.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['传感轴','背板接口','位号','单根预留长度mm','根数','状态'])
        for r in rows:writer.writerow([r['raw_id'],r['connector'],r['carrier_reference'],r['preliminary_cut_each_of_five_wires_mm'],5,'试装后裁线'])
    print('HARNESS',len(rows),'CAPACITY',report['capacity_passed'],'MAX',report['maximum_preliminary_length_mm'],flush=True)
    print('CAPACITY FAILURES',[r for r in capacities if not r['passed']],flush=True)


if __name__=='__main__':main()
