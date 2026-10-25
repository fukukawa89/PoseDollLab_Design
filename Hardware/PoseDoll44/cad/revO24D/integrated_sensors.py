"""Native sensor-board tail outlets; frozen Hall datums are never relocated."""
from fullbody import *

def apply(D):
    layout=load(HERE/'sensor_mount_layout.json')['rows']
    variants=load(OUT/'electronics/sensors/manifest.json')['variants']
    records=[];routes={r['sensor']:r for r in load(HERE/'wire_tail_routes.json')['rows']}
    for row in layout:
        v=next(v for v in variants if row['sensor'] in v['instances'])
        pcb=next(p for p in D.parts if p['name']==row['pcb_part'])
        plug=next(p for p in D.parts if p['name']==row['connector_part'])
        verts,_=a.mesh_data(pcb['s']);c=(verts.min(0)+verts.max(0))/2
        world=F0[pcb['frame']]@np.r_[c,1]
        assert np.linalg.norm(world[:3]-row['board_center_N_mm'])<1e-5,row['sensor']
        W=np.eye(4);W[:3,:3]=np.array([row['u_world'],row['v_to_pigtail_world'],row['normal_to_magnet']]).T
        W[:3,3]=row['board_center_N_mm'];half=row['board_uv_mm'][1]/2;sg=v['tail_side_v']
        lo,hi=sorted([sg*(half+.1),sg*(half+3.1)])
        plug['s']=moved(box([-3.2,lo,-.8],[3.2,hi,.8]),np.linalg.inv(F0[plug['frame']])@W)
        plug['notes']='Six factory-soldered AWG30 wires, potted flat tail outside PCB edge; native sensor PCB variant '+v['variant']+'. Not a separable board connector.'
        plug['sku']='6_CORE_POTTED_TAIL'
        clo,chi=sorted([sg*(half-.5),sg*(half+3.4)])
        cutter=box([-3.4,clo,-1.0],[3.4,chi,1.0])
        holder=row['sensor']+'_sensor_holder' if not row['sensor'].endswith('wrist') else row['sensor'][0]+'_wrist_bridge'
        match=[p for p in D.parts if p['name']==holder]
        assert match,holder
        route=routes[row['sensor']];ep=np.array(route['exit_board_mm']);ed=np.array(route['direction_board'])
        cutter+=beam(ep-ed*.5,ep+ed*8,1.2)
        for p in match:
            p['s']-=moved(cutter,np.linalg.inv(F0[p['frame']])@W)
            _=p['s'].volume()  # Evaluate local CSG before later mirror/clip transforms.
        q=(np.linalg.inv(F0[plug['frame']])@W@np.r_[ep,1])[:3]
        direction=np.linalg.inv(F0[plug['frame']])[:3,:3]@W[:3,:3]@ed
        records.append(dict(**row,variant=v['variant'],tail_side_v=sg,tail_exit_local_mm=q,tail_direction_local=direction,holder=holder))
    D.sensor_tails=records
    put(OUT/'electronics/sensor_tails.json',dict(rows=records,scope='Actual populated-board envelopes, potted wire-tail outlets and matching holder passages. Hall centre unchanged. Free bend radius is checked outside potting.'))
