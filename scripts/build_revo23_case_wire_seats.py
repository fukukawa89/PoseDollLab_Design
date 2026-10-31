"""Two wide strain-relief saddles at the real side entries of the rear case."""
from build_revo23_wire_seats import *
parts,p,cfg=load_e();F=frames(p,p['neutral_raw_deg'])
key='o22/controller_housing';item=parts[key]
C=np.array(read(B/'design/compact_revision.json')['controller_frame_neutral_mm'])
C[:3,3]=cfg['controller_front_corner_neutral_mm'];T=np.linalg.inv(F['f:chest'])@C
oldparts,_,_=load_d();host=oldparts[key]['s']
poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
FF={n:frames(p,q) for n,q in poses.items()}
records=[];pad,tunnel=saddle(16)
wire=box([-8,4.95,-6],[8,10.95,6])
for side,u in [('left',-8),('right',72)]:
    for level,values in [('upper',(43,39,47,35))]:
        for v in values:
            M=np.eye(4);M[:3,:3]=np.array([[0,0,1],[1,0,0],[0,1,0.]])
            M[:3,3]=[u,v,30.5];L=T@M
            shape=move(pad,L)^move(box([-30,-10,0],[95,75,50]),T)
            # Keep the lid free: the strap bridge stands outside the side rim.
            shape=shape-move(box([-5.3,-5.3,31.9],[69.3,65.3,50]),T)
            strap=move(tunnel,L);reserve=move(wire,L);bond=(shape^host).volume()
            if bond<30 or (strap^host).volume()>.01 or (reserve^host).volume()>.01:continue
            test=shape+strap+reserve;bb=np.array(test.bounding_box())
            collision=any((test^ob).volume()>.01 for _,_,ob,_ in obstacle_transforms(key,parts,p,FF,bb))
            if collision:continue
            host=host+shape
            records.append(dict(id='case:'+side+':'+level,part=key,body='chest',token='f:chest',
                transform_body_mm=L,origin_body_mm=L[:3,3],
                wire_center_body_mm=(L@np.array([0,7.95,0,1]))[:3],
                reserved_channel_width_mm=16,reserved_channel_height_mm=6,
                maximum_cores_at_OD_0p7=120,strap_tunnel_mm=[3.4,1.8],
                zip_tie_nominal_width_mm=2.5,wall_bond_volume_mm3=bond,
                exterior_perforation=False,motion_samples_checked=len(FF)))
            print('CASE SEAT',records[-1]['id'],round(bond,2),flush=True);break
assert len(records)==2,('case seats missing',len(records))
v,f=vf(host);assert trimesh.Trimesh(v,f,process=False).is_watertight
np.savez_compressed(EROOT/'o22__controller_housing.npz',v=v,f=f)
put(EROOT/'o22__controller_housing.json',dict(key=key,wire_seats=records,
    input_geometry_sha256=DHASH,added_volume_mm3=host.volume()-oldparts[key]['s'].volume()))
d=read(EROOT/'wire_seats.json');d['seats']=[r for r in d['seats'] if r['part']!=key]+records
put(EROOT/'wire_seats.json',d)
