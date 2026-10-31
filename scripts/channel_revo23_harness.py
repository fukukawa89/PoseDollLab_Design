"""Clear continuous internal wire corridors between serial limb tie saddles."""
from build_revo23_wire_seats import *
from audit_revo23_load_paths import screen


def sweep(points,xaxis,yaxis,width,height):
    theta=np.linspace(0,2*np.pi,20,endpoint=False)
    rings=[q+np.cos(theta)[:,None]*xaxis*width/2+
           np.sin(theta)[:,None]*yaxis*height/2 for q in points]
    return union([md.Manifold.hull_points(np.vstack([a,b])) for a,b in zip(rings,rings[1:])])


def main(keys=None):
    parts,p,cfg=load_e();data=read(EROOT/'wire_seats.json')
    poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
    poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
    FF={k:frames(p,q) for k,q in poses.items()}
    kz=np.load(DHISTORY/'source/retained_interfaces.npz');records=[]
    bodies=sorted({r['body'] for r in data['seats'] if r['body'].startswith(
        ('upperarm_','forearm_','thigh_','calf_'))})
    for body in bodies:
        if keys and 'frame/'+body not in keys:continue
        seats=[r for r in data['seats'] if r['body']==body]
        if len(seats)<2:continue
        key='frame/'+body;host=parts[key]['s'];keep=solid(kz[key+'|v'],kz[key+'|f'])
        skin=local_skin(key,p,cfg);a,b=seats[:2]
        roofs=union([move(box([-r['reserved_channel_width_mm']/2+.2,2.7,-1.5],
            [r['reserved_channel_width_mm']/2-.2,4.5,1.5]),np.array(r['transform_body_mm'])) for r in seats])
        pa=np.array(a['wire_center_body_mm']);pb=np.array(b['wire_center_body_mm'])
        M=np.array(a['transform_body_mm']);xaxis=M[:3,0];yaxis=M[:3,1]
        width=min(a['reserved_channel_width_mm'],b['reserved_channel_width_mm'])
        height=min(a['reserved_channel_height_mm'],b['reserved_channel_height_mm'])
        if body.startswith('upperarm_'):height=min(height,3.5)
        found=None
        rejections={}
        options=[(0,0),(0,2),(0,-2),(3,0),(-3,0),(0,4),(6,0),(-6,0),(0,6),(9,0),(-9,0)]
        options += [(dx,dy) for dy in (-3,-4,-5,2,4,6) for dx in (0,-3,3,-5,5)]
        for dx,dy in options:
            t=np.linspace(0,1,13);points=(1-t[:,None])*pa+t[:,None]*pb
            points+=4*t[:,None]*(1-t[:,None])*(dx*xaxis+dy*yaxis)
            channel=solid(*vf(sweep(points,xaxis,yaxis,width,height)))
            if (channel^keep).volume()>.01 or (channel^skin).volume()>.01 or (channel^roofs).volume()>.01:
                rejections['protected']=rejections.get('protected',0)+1;continue
            bb=np.array(channel.bounding_box());blocked=False
            for other,pose,ob,_ in obstacle_transforms(key,parts,p,FF,bb):
                overlap=(channel^ob).volume()
                if overlap>.01:
                    blocked=True
                    if dx==0 and dy in (0,-4):print('CHANNEL OBSTACLE',key,dx,dy,other,pose,round(overlap,3),flush=True)
                    break
            if blocked:
                rejections['moving_parts']=rejections.get('moving_parts',0)+1;continue
            result=host-channel
            cc=[s for s in result.decompose() if s.volume()>.001]
            if len(cc)!=1:
                rejections['components']=rejections.get('components',0)+1;continue
            # Do not carve any saddle's strap roof. Its reserved wire envelope
            # begins 0.15 mm above that roof.
            removed=max(0,host.volume()-result.volume())
            if removed>2500:continue
            found=(result,dict(part=key,a=a['id'],b=b['id'],centerline_body_mm=points,
                width_mm=width,height_mm=height,removed_internal_rib_mm3=removed,
                maximum_cores_in_channel=30 if body.startswith('upperarm_') else a['maximum_cores_at_OD_0p7'],
                original_precision_land_and_skin_loss_mm3=0,adjacent_pose_samples=len(FF),
                channel_open_in_actual_print=True));break
        if found is None:
            records.append(dict(part=key,a=a['id'],b=b['id'],channel_open_in_actual_print=False))
            print('CHANNEL NEEDS ROUTE',key,rejections,flush=True);continue
        result,row=found;v,f=vf(result);assert trimesh.Trimesh(v,f,process=False).is_watertight
        path=EROOT/(key.replace('/','__')+'.npz')
        backup=EROOT/'checkpoints/before_wire_channels';backup.mkdir(parents=True,exist_ok=True)
        if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
        np.savez_compressed(path,v=v,f=f);parts[key]['s']=result;records.append(row)
        put(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'),screen(key,result,keep,skin,1.))
        print('CHANNEL',key,'removed',round(removed,2),flush=True)
    if keys and (EROOT/'wire_channels.json').exists():
        records=[r for r in read(EROOT/'wire_channels.json')['rows'] if r['part'] not in keys]+records
    put(EROOT/'wire_channels.json',dict(rows=records,
        passed=all(r['channel_open_in_actual_print'] for r in records),
        scope='Serial fixed spans inside arm and leg prints; flexible joint loops require first-article fitting.'))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');args=ap.parse_args();main(args.keys)
