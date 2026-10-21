"""Integral, accessible tie saddles in the real O23E structural prints.

The saddle is positive geometry bonded to the inside wall. Its strap tunnel
does not perforate that wall. Candidate saddle and reserved wire volume must
clear the actual adjacent mechanisms in all declared ordinary-use samples.
"""
from revo23_reinforcement import *
from build_revo23_reinforced import obstacle_transforms
import math,time


def load_e():
    parts,p,cfg=load_d()
    for key,item in parts.items():
        path=EROOT/(key.replace('/','__')+'.npz')
        if path.exists():
            z=np.load(path);item['s']=solid(z['v'],z['f'])
    return parts,p,cfg


def saddle(width,half=6):
    # Local X across wire bundle, Y inward from inner skin, Z along the limb.
    base=box([-width/2-3,-4,-half],[width/2+3,4.8,half])
    tunnel=box([-width/2-3.1,.6,-1.7],[width/2+3.1,2.4,1.7])
    # Broad, rounded shoulders protect the wire; no teeth or tight snap-fit.
    lips=union([capsule([s*(width/2+1),4.3,-4],[s*(width/2+1),4.3,4],.7)
                for s in (-1,1)])
    return (base+lips)-tunnel,tunnel


def candidate_positions(body,N,cfg,needed,host=None):
    geom=canonical(body,N,cfg)
    if geom is None:
        v,f=vf(host);tri=v[f];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        area=np.linalg.norm(norm,axis=1);norm/=np.maximum(area[:,None],1e-12)
        centroid=tri.mean(1);back=N[:3,:3].T@np.array([-1.,0,0])
        ranking=np.argsort(-(area*(1+.5*np.maximum(0,norm@back))))
        # Fine level-set faces must not be excluded merely because each
        # triangle is small. Cover the full carrier surface in 4 mm cells.
        _,first=np.unique(np.floor(centroid[ranking]/4).astype(int),axis=0,return_index=True)
        order=ranking[np.sort(first)]
        used=[]
        axis=np.eye(3)[np.argmax(np.ptp(v,axis=0))]
        for n in order:
            if area[n]<.01:continue
            center=centroid[n]
            if any(np.linalg.norm(center-x)<4 for x in used):continue
            used.append(center);inward=norm[n];up=axis-inward*np.dot(axis,inward)
            if np.linalg.norm(up)<.1:continue
            up/=np.linalg.norm(up);across=np.cross(inward,up)
            C=np.eye(4);C[:3,:3]=np.c_[across,inward,up];C[:3,3]=center+inward*1.5
            yield C,None,dict(surface_triangle=int(n),carrier_surface=True)
        return
    _,outer,rows,A=geom
    fn=PchipInterpolator(rows[:,0],rows[:,1:],axis=0)
    d=read(DHISTORY/'candidates'/('frame__'+body+'.json'))
    lows=np.asarray(d['lower_boundary_mm']);highs=np.asarray(d['upper_boundary_mm'])
    angles=list(range(64,128,4))+list(range(60,-1,-4))
    # Prefer two spaced seats on the same intact back-wall strip.
    for i in angles:
        margin=6 if body.startswith('forearm_') else 8
        lo=lows[i]+margin;hi=highs[i]-margin
        if hi<lo:continue
        for fraction in (.25,.75,.5,.1,.9):
            z=lo+(hi-lo)*fraction
            cx,cy,rx,ry=fn(z);theta=2*np.pi*i/128
            out=np.array([np.cos(theta)/rx,np.sin(theta)/ry,0.]);out/=np.linalg.norm(out)
            inward=-out;up=np.array([0.,0.,1.]);across=np.cross(inward,up)
            wall=cfg['wall_mm']
            center=np.array([cx+(rx-wall)*np.cos(theta),cy+(ry-wall)*np.sin(theta),z])
            C=np.eye(4);C[:3,:3]=np.c_[across,inward,up];C[:3,3]=center+inward*1.5
            yield np.linalg.inv(N)@A@C,move(outer,np.linalg.inv(N)@A),dict(theta_index=i,z_mm=z)


def build_seats(keys=None):
    parts,p,cfg=load_e()
    poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
    poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
    FF={k:frames(p,q) for k,q in poses.items()};F=frames(p,p['neutral_raw_deg'])
    existing=EROOT/'wire_seats.json'
    records=read(existing)['seats'] if existing.exists() else []
    allresults=[]
    for key,item in parts.items():
        if item['role']!='structure' or keys and key not in keys:continue
        body=item['body']
        if body.startswith(('ball_','hand_')):continue
        # Conservative capacity, including channels joining closer to the trunk.
        cores=40 if body.startswith(('upperarm_','thigh_','clavicle_')) else 20
        if body in ('pelvis','waist','chest'):cores=80
        if body=='chest':cores=120
        if body=='head':cores=20
        width,height=(16.,6.) if cores==120 else ((12.,6.) if cores==80 else ((6.5,4.5) if cores==40 else (5.,4.)))
        if body.endswith('.protract_frame'):cores=45
        if body.startswith('forearm_'):cores=10;width,height=3.5,3.
        count=2 if body.startswith(('upperarm_','forearm_','thigh_','calf_')) else 1
        if body in ('pelvis','waist','chest'):count=2
        # Restore pre-seats if deliberately rerun; never stack duplicate saddles.
        path=EROOT/(key.replace('/','__')+'.npz')
        backup=EROOT/'checkpoints/before_wire_seats'/path.name;backup.parent.mkdir(parents=True,exist_ok=True)
        if backup.exists():
            z=np.load(backup);item['s']=solid(z['v'],z['f'])
        else:shutil.copy2(path,backup)
        host=item['s'];chosen=[];fails={}
        kz=np.load(DHISTORY/'source/retained_interfaces.npz')
        keep=solid(kz[key+'|v'],kz[key+'|f'])
        skin=local_skin(key,p,cfg)
        half=4.5 if body.startswith('forearm_') else 6.
        seat,tunnel=saddle(width,half)
        reserve=box([-width/2,4.95,-half],[width/2,4.95+height,half])
        # Detach the reusable CSG prototypes before applying many different
        # carrier-face orientations and evaluating dependent Boolean trees.
        seat_mesh=vf(seat);tunnel_mesh=vf(tunnel);reserve_mesh=vf(reserve)
        for position_index,(M,outer,position) in enumerate(candidate_positions(body,F[item['token']],cfg,count,host)):
            center=M[:3,3]
            if any(np.linalg.norm(center-r['origin_body_mm'])<half*2+3 for r in chosen):continue
            pad=move(solid(*seat_mesh),M)
            if outer is not None:pad=pad^outer
            strap=move(solid(*tunnel_mesh),M);wire=move(solid(*reserve_mesh),M)
            channel=wire+strap
            bond=(pad^host).volume()
            if body.startswith('clavicle_') and position_index<4:
                print('CARRIER SEAT TRY',body,position_index,'bond',bond,'host',host.volume(),
                      'position',center.tolist(),'outer',outer is not None,flush=True)
            required_bond=20 if body.startswith('clavicle_') else 35
            reason='bond' if bond<required_bond else ('precision' if (channel^keep).volume()>.01
                    else ('skin' if (channel^skin).volume()>.01 else None))
            if reason:
                fails[reason]=fails.get(reason,0)+1;continue
            removed=(channel^host).volume()
            if removed>1200:
                fails['large_cut']=fails.get('large_cut',0)+1;continue
            shape=(host-channel)+pad
            roof=move(box([-width/2+.2,2.7,-1.5],[width/2-.2,4.5,1.5]),M)
            if (roof^shape).volume()/roof.volume()<.98:
                fails['roof']=fails.get('roof',0)+1;continue
            test=pad+wire+strap;bb=np.asarray(test.bounding_box());bad=False
            for other,pose,ob,obb in obstacle_transforms(key,parts,p,FF,bb):
                if (test^ob).volume()>.01:
                    fails['motion']=fails.get('motion',0)+1;bad=True;break
            if bad:continue
            if len([s for s in shape.decompose() if s.volume()>.001])!=1:continue
            # Clipping a saddle to the outer envelope can leave its strap
            # roof mostly absent even though the saddle still bonds to a rod.
            previous_open=True
            for old in chosen:
                C=np.array(old['transform_body_mm']);w=old['reserved_channel_width_mm'];h=old['reserved_channel_height_mm']
                slot=move(box([-w/2-3.1,.6,-1.7],[w/2+3.1,2.4,1.7]),C)
                clear=move(box([-w/2,4.95,-half],[w/2,4.95+h,half]),C)
                if (shape^(slot+clear)).volume()>.01:previous_open=False;break
            if not previous_open:
                fails['blocks_previous_seat']=fails.get('blocks_previous_seat',0)+1;continue
            number=len(chosen)+1
            row=dict(id=body+':tie'+str(number),part=key,body=body,token=item['token'],
                transform_body_mm=M,origin_body_mm=center,
                wire_center_body_mm=(M@np.array([0,4.95+height/2,0,1]))[:3],
                reserved_channel_width_mm=width,reserved_channel_height_mm=height,
                maximum_cores_at_OD_0p7=cores,packing_fraction=cores*np.pi*.7**2/4/(width*height),
                strap_tunnel_mm=[3.4,1.8],zip_tie_nominal_width_mm=2.5,
                minimum_roof_thickness_mm=2.4,wall_bond_volume_mm3=bond,
                internal_rib_relief_mm3=removed,precision_land_and_original_skin_loss_mm3=0,
                exterior_perforation=False,motion_samples_checked=len(FF),position=position)
            chosen.append(row);host=shape
            print('SEAT',row['id'],'bond',round(bond,1),flush=True)
            if len(chosen)>=count:break
        v,f=vf(host);assert trimesh.Trimesh(v,f,process=False).is_watertight
        np.savez_compressed(path,v=v,f=f);item['s']=host
        records=[r for r in records if r['part']!=key]+chosen
        result=dict(part=key,requested=count,placed=len(chosen),rejections=fails)
        allresults.append(result);print('SEATS DONE',result,flush=True)
        put(existing,dict(source_geometry_sha256=DHASH,seats=records,results=allresults,
            wire_spec=dict(conductor='AWG30 flexible stranded copper',max_insulated_OD_mm=.7,
                five_independent_cores_per_sensor=True,sensors=46,
                bend_radius_design_envelope_mm=10,vendor_minimum_radius_must_not_exceed_design=True),
            physical_cable_fatigue_verified=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');args=ap.parse_args()
    build_seats(args.keys)
