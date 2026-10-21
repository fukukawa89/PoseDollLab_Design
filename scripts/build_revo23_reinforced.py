"""Add broad, internal load paths while preserving the accepted D exterior."""
from revo23_reinforcement import *
from audit_revo23_load_paths import screen
import itertools,time


def spaced_points(v,spacing=5.,limit=40):
    if not len(v):return v
    # Deterministic coverage: extrema, then farthest point from the chosen set.
    chosen=list(dict.fromkeys(np.r_[np.argmax(v,axis=0),np.argmin(v,axis=0)].tolist()))
    dist=np.min(np.linalg.norm(v[:,None]-v[chosen],axis=2),axis=1)
    while len(chosen)<limit:
        n=int(np.argmax(dist))
        if dist[n]<spacing:break
        chosen.append(n);dist=np.minimum(dist,np.linalg.norm(v-v[n],axis=1))
    return v[chosen]


def padded_hull(s,r):
    v,_=vf(s)
    offsets=np.array(list(itertools.product((-1,1),repeat=3)))*r
    return md.Manifold.hull_points(np.vstack([v+o for o in offsets]))


def obstacle_transforms(key,parts,p,poses,bb):
    part=parts[key];seen=set();families=[]
    for k,item in parts.items():
        if k==key or not adjacent(part,item,p):continue
        v,_=vf(item['s']);bounds=np.r_[v.min(0),v.max(0)]
        corners=np.array(list(itertools.product(*zip(bounds[:3],bounds[3:]))))
        families.append((k,item,corners))
    for name,F in poses.items():
        I=np.linalg.inv(F[part['token']])
        for k,item,corners in families:
            M=I@F[item['token']];sig=(k,tuple(np.round(M,6).ravel()))
            if sig in seen:continue
            seen.add(sig);q=corners@M[:3,:3].T+M[:3,3]
            obb=np.r_[q.min(0),q.max(0)]
            if np.any(np.minimum(bb[3:],obb[3:])-np.maximum(bb[:3],obb[:3])<=0):continue
            yield k,name,move(item['s'],M),obb


def reinforce(key,parts,p,cfg,pose_frames,thickness=4.0,relax_core=False,precise=False,fill=False,padding=8,distributed=False):
    started=time.time();item=parts[key];old=item['s']
    kz=np.load(DHISTORY/'source/retained_interfaces.npz')
    keep=solid(kz[key+'|v'],kz[key+'|f']);skin=local_skin(key,p,cfg)
    lands=sorted([s for s in keep.decompose() if s.volume()>50],key=lambda s:-s.volume())
    F=frames(p,p['neutral_raw_deg']);N=F[item['token']]
    geom=canonical(item['body'],N,cfg)
    outer=move(geom[1],np.linalg.inv(N)@geom[3]) if geom else padded_hull(old,padding if relax_core else 0)
    # The permission envelope only bounds added material. It is not printed solid.
    limit=outer+keep.hull()+old
    bridges=old-keep-skin
    additions=[];routes=[]
    for b in bridges.decompose():
        if b.volume()>.5:
            grow=padded_hull(b,thickness)
            additions.append(grow if distributed else grow^limit)
    for li,land in enumerate(lands):
        target=skin
        if target.is_empty():target=union([c for j,c in enumerate(lands) if j!=li])
        if target.is_empty():continue
        v,_=vf(land);tv,_=vf(target)
        source=spaced_points(v,spacing=5,limit=55)
        tree=cKDTree(tv);dist,idx=tree.query(source)
        selected=[]
        for n in np.argsort(dist):
            a=source[n];b=tv[idx[n]];d=float(dist[n])
            if d>90 or d<.25:continue
            if any(np.linalg.norm(a-x)<5.5 for x in selected):continue
            # Constant ribs plus rounded broad landings, never a tangent-only weld.
            beam=capsule(a,b,thickness)+ball(a,thickness+1.5)+ball(b,thickness+1.5)
            additions.append(beam if distributed else beam^limit);selected.append(a)
            routes.append(dict(land=li,a=a,b=b,radius_mm=thickness,length_mm=d))
            if len(selected)>=12:break
        if distributed:
            for a in spaced_points(v,spacing=14,limit=8):
                for direction in np.r_[np.eye(3),-np.eye(3)]:
                    _,idx2=tree.query(a+direction*35);b=tv[idx2]
                    if np.linalg.norm(a-b)>120:continue
                    additions.append(capsule(a,b,thickness)+ball(a,thickness+2)+ball(b,thickness+2))
    # Retain finite overlap with the original land. Subtracting old here and
    # adding it back later creates coincident sliver faces at precision seats.
    if fill:raw=limit
    elif distributed:
        raw=md.Manifold()
        for start in range(0,len(additions),8):
            raw=union([raw]+additions[start:start+8]).simplify(.025)
            print('DISTRIBUTED WEB',key,start,'of',len(additions),flush=True)
        raw=(raw^limit.simplify(.025)).simplify(.025)
    else:raw=union(additions)
    print('REINFORCE',key,'raw added',round(raw.volume(),1),'routes',len(routes),flush=True)
    # Retain exact negative spaces around the original precision core and the
    # original magnet seats. All original positive material remains unchanged.
    anchors=interface_anchors(item['body'],p,F)
    core=union([ball((np.linalg.inv(N)@np.r_[a['point'],1])[:3],a['guard_radius']*.65) for a in anchors])
    if not relax_core:raw=raw-(core-keep)
    rz=np.load(DHISTORY/'source/interface_edge_reliefs.npz')
    if key+'|v' in rz and not (relax_core and key=='frame/chest'):
        raw=raw.simplify(.015)-solid(rz[key+'|v'],rz[key+'|f']).simplify(.01)
    print('PRECISION SPACES',key,flush=True)
    seed=raw.simplify(.015);bb=np.array(raw.bounding_box());cuts={};contacts=[];number=0
    for other,pose,ob,obb in obstacle_transforms(key,parts,p,pose_frames,bb):
        hit=seed^ob
        if hit.volume()<.002:continue
        # Grow only the measured local contact, not a whole moving module hull.
        # This leaves a 0.6 mm nominal trimming margin around the actual obstacle.
        # Aggregate the measured contact sweep for each real neighbouring part.
        # A conservative convex sweep is substantially more stable than hundreds
        # of overlapping small Boolean cuts. It only removes new reinforcement.
        for contact in hit.decompose():
            if contact.volume()<.001:continue
            hv,_=vf(contact)
            group=(other,tuple(np.floor(hv.mean(0)/4).astype(int))) if precise else other
            if group in cuts:
                hv=np.vstack([hv,cuts[group]])
            cuts[group]=vf(md.Manifold.hull_points(hv))[0]
        contacts.append(dict(other=other,pose=pose,overlap_mm3=hit.volume()))
        number+=1
        if number%100==0:print('TRIM',key,number,flush=True)
    if cuts:
        print('TRIM SWEEPS',key,len(cuts),flush=True)
        cutters=[padded_hull(md.Manifold.hull_points(v),.4 if precise else .6) for v in cuts.values()]
        raw=seed
        for start in range(0,len(cutters),24):
            raw=(raw-union(cutters[start:start+24])).simplify(.025)
            if start%120==0:print('CUT BATCH',key,start,'of',len(cutters),flush=True)
    candidate=old+raw
    cc=candidate.decompose();main=[c for c in cc if (c^old).volume()>old.volume()*.9]
    assert len(main)==1,(key,'lost original connected component')
    candidate=main[0]
    loss=max(0.,(old-candidate).volume())
    print('PRESERVED',key,'old volume difference',loss,flush=True)
    if loss>.05:
        qv,qf=vf(candidate)
        np.savez_compressed(EROOT/(key.replace('/','__')+'_needs_review.npz'),v=qv,f=qf)
        raise RuntimeError((key,'unexpected original material difference',loss))
    v,f=vf(candidate);mesh=trimesh.Trimesh(v,f,process=False)
    report=dict(key=key,input_geometry_sha256=DHASH,method='Internal rounded ribs and widened landing pads; original D material preserved.',
        radius_mm=thickness,maximum_allowed_envelope_filled=fill,
        exact_motion_space_instead_of_spherical_guard=relax_core,
        local_contact_sweep_bins_mm=4 if precise else None,routes=routes,trim_contacts=contacts,
        source_watertight=bool(mesh.is_watertight),component_count=1,
        original_material_lost_mm3=loss,
        added_volume_mm3=max(0.,candidate.volume()-old.volume()+loss),seconds=time.time()-started,
        physical_strength_verified=False,manufacturing_release=False)
    EROOT.mkdir(parents=True,exist_ok=True);path=EROOT/(key.replace('/','__')+'.npz')
    np.savez_compressed(path,v=v,f=f);put(path.with_suffix('.json'),report)
    result=screen(key,candidate,keep,skin,1.0)
    put(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'),result)
    print('REINFORCED',key,round(report['added_volume_mm3'],1),'mm3',round(time.time()-started,1),'seconds',flush=True)
    return candidate


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*')
    ap.add_argument('--radius',type=float,default=4.0)
    ap.add_argument('--relax-core',action='store_true');ap.add_argument('--precise',action='store_true')
    ap.add_argument('--fill',action='store_true')
    ap.add_argument('--reset-collars',action='store_true')
    ap.add_argument('--padding',type=float,default=8);ap.add_argument('--distributed',action='store_true')
    ap.add_argument('--background-d',nargs='*',default=[])
    args=ap.parse_args()
    parts,p,cfg=load_d();original={k:dict(v) for k,v in parts.items()}
    for key,item in parts.items():
        path=EROOT/(key.replace('/','__')+'.npz')
        if item['role']=='structure' and path.exists():
            z=np.load(path);item['s']=solid(z['v'],z['f'])
        if args.reset_collars and key.startswith('frame/clavicle_'):
            parts[key]=dict(original[key])
        if key in args.background_d:parts[key]=dict(original[key])
    poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
    poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
    pose_frames={k:frames(p,v) for k,v in poses.items()}
    keys=args.keys or [k for k,v in parts.items() if v['role']=='structure']
    for key in keys:
        parts[key]=dict(original[key])
        parts[key]['s']=reinforce(key,parts,p,cfg,pose_frames,args.radius,args.relax_core,args.precise,args.fill,args.padding,args.distributed)


if __name__=='__main__':main()
