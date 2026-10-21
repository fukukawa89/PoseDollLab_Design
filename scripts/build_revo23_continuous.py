"""O23D: smooth end-connected openings in structural anatomical walls.

The wall is constructed as a continuous radial strip whose two end boundaries
follow conservative swept-obstacle masks. It cannot contain isolated punctures.
Functional lands are retained separately and joined by bounded internal webs.
The source is the immutable O23C snapshot; trials do not change the assembly.
"""
from revo23_daily import *
from present_revo23 import load_current
from scipy.ndimage import maximum_filter1d,minimum_filter1d,gaussian_filter1d,maximum_filter
from PIL import Image,ImageDraw
import time

DROOT=B/'design/continuous_candidate'
ANGLES=128
BUILDER_ID='D12-precision-collar-shortened-back-mounts'


def profile_signature(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,default=plain,separators=(',',':')).encode()).hexdigest()


def load_c():
    z=np.load(C_HISTORY/'assembly.npz');out={}
    for item in read(C_HISTORY/'assembly.json')['items']:
        i=str(item['index']);out[item['key']]=dict(item,s=solid(z[i+'v'],z[i+'f']))
    overrides=DROOT/'source/part_overrides.npz'
    if overrides.exists():
        z=np.load(overrides)
        for key,item in out.items():
            if key+'|v' in z:item['s']=solid(z[key+'|v'],z[key+'|f'])
    return out


def canonical(body,F,cfg):
    shell,outer,rows=anatomy(body,F,cfg['scale'],cfg)
    if shell is None:return None
    A=np.eye(4);A[:3,3]=F[:3,3]
    if body.startswith(('foot_','ball_')):
        A[:3,:3]=np.array([[0,0,1],[0,1,0],[-1,0,0.]])
        if body.startswith('foot_'):
            rows=[[-24,17,0,13,16],[-16,20,0,17,21],[7,20,0,20,23],[35,18,0,16,24],[49,16,0,11,24]]
        else:rows=[[-4,15,0,10,24],[8,14,0,11,24],[23,13,0,10,22],[34,11,0,4,16]]
    else:
        rows=np.asarray(rows);rows[:,:3]-=F[:3,3][[2,0,1]]
    return move(shell,np.linalg.inv(A)),move(outer,np.linalg.inv(A)),np.asarray(rows),A


def mark_opening(shape,rows,low,high,gap=1.6,end=None):
    """Project actual triangles; retain height variation around each opening.

    Using a component's full height for its entire angular span overcuts a
    curved chest. A periodic angular/height raster keeps that local detail,
    then merges each opening with its nearest end without isolated pinholes.
    """
    fn=PchipInterpolator(rows[:,0],rows[:,1:],axis=0,extrapolate=True)
    step=2*np.pi/ANGLES
    dz=.75;z0,z1=rows[0,0],rows[-1,0];nz=int(np.ceil((z1-z0)/dz))+2
    for component in shape.decompose():
        if component.volume()<.005:continue
        v,faces=vf(component)
        if not len(v):continue
        z=np.clip(v[:,2],z0,z1);a=fn(z)
        theta=np.mod(np.arctan2((v[:,1]-a[:,1])/a[:,3],(v[:,0]-a[:,0])/a[:,2]),2*np.pi)
        image=Image.new('1',(ANGLES*3,nz));draw=ImageDraw.Draw(image)
        for face in faces:
            tt=theta[face];xx=(tt[0]+np.mod(tt-tt[0]+np.pi,2*np.pi)-np.pi)/step
            zz=(z[face]-z0)/dz
            for offset in (0,ANGLES,2*ANGLES):
                draw.polygon([(float(x+offset),float(h)) for x,h in zip(xx,zz)],fill=1)
        mask=np.asarray(image,dtype=bool)[:,ANGLES:2*ANGLES]
        mask=maximum_filter(mask,size=(int(np.ceil(gap/dz))*2+1,5),mode=('constant','wrap'))
        occupied=mask.any(axis=0)
        if not occupied.any():continue
        first=np.argmax(mask,axis=0);last=nz-1-np.argmax(mask[::-1],axis=0)
        zlo=z0+first*dz;zhi=z0+(last+1)*dz
        if end=='lower' or (end is None and (float(z.min())+float(z.max()))/2 < (z0+z1)/2):
            low[occupied]=np.maximum(low[occupied],zhi[occupied])
        else:high[occupied]=np.minimum(high[occupied],zlo[occupied])


def radial_wall(rows,low,high,wall):
    # Dilate before smoothing so filleted boundaries contain the sampled cuts.
    bottom=gaussian_filter1d(maximum_filter1d(low,size=9,mode='wrap'),2,mode='wrap')
    top=gaussian_filter1d(minimum_filter1d(high,size=9,mode='wrap'),2,mode='wrap')
    bottom=np.maximum(low,bottom+.35);top=np.minimum(high,top-.35)
    bottom=np.clip(bottom,rows[0,0],rows[-1,0]);top=np.clip(top,rows[0,0],rows[-1,0])
    active=top-bottom>=6
    fn=PchipInterpolator(rows[:,0],rows[:,1:],axis=0,extrapolate=True)
    height=rows[-1,0]-rows[0,0];levels=max(8,int(height/2)+1)
    v=[];faces=[]
    for inward in (0,1):
        for i in range(ANGLES):
            theta=i*2*np.pi/ANGLES
            for t in np.linspace(0,1,levels):
                z=bottom[i]+t*(top[i]-bottom[i]);cx,cy,rx,ry=fn(z)
                v.append([cx+max(.3,rx-inward*wall)*np.cos(theta),cy+max(.3,ry-inward*wall)*np.sin(theta),z])
    def vid(inner,i,j):return inner*ANGLES*levels+(i%ANGLES)*levels+j
    def quad(a,b,c,d):faces.extend([[a,b,c],[a,c,d]])
    used=[bool(active[i] and active[(i+1)%ANGLES]) for i in range(ANGLES)]
    for i in range(ANGLES):
        if not used[i]:continue
        k=(i+1)%ANGLES
        for j in range(levels-1):
            quad(vid(0,i,j),vid(0,k,j),vid(0,k,j+1),vid(0,i,j+1))
            quad(vid(1,i,j+1),vid(1,k,j+1),vid(1,k,j),vid(1,i,j))
        quad(vid(0,i,0),vid(1,i,0),vid(1,k,0),vid(0,k,0))
        quad(vid(0,k,levels-1),vid(1,k,levels-1),vid(1,i,levels-1),vid(0,i,levels-1))
        if not used[(i-1)%ANGLES]:
            for j in range(levels-1):quad(vid(0,i,j+1),vid(1,i,j+1),vid(1,i,j),vid(0,i,j))
        if not used[k]:
            for j in range(levels-1):quad(vid(0,k,j),vid(1,k,j),vid(1,k,j+1),vid(0,k,j+1))
    if not faces:return md.Manifold(),bottom,top,0
    s=solid(v,faces)
    return s,bottom,top,sum(used)


def connect_inside(shape,keep,forbidden,outer,radius=3.0,carve=True,progress_label=None,extra_targets=False):
    """Straight ribs first; short in-body detours only when needed."""
    records=[];obounds=np.array([bb for _,bb in forbidden])
    for attempt in range(16):
        cc=sorted([s for s in shape.decompose() if s.volume()>.01],key=lambda s:-s.volume())
        if len(cc)<2:break
        if progress_label:print('WEB',progress_label,'attempt',attempt+1,'components',len(cc),flush=True)
        vv,_=vf(cc[0]);tree=cKDTree(vv);success=False
        for comp in sorted(cc[1:],key=lambda c:-c.volume()):
            v,_=vf(comp);dist,idx=tree.query(v);chosen=[]
            extreme=set(np.argmax(v,axis=0))|set(np.argmin(v,axis=0))
            order=list(extreme)+list(np.argsort(dist))
            for n in order:
                if any(np.linalg.norm(v[n]-v[j])<4 for j in chosen):continue
                chosen.append(n)
                if len(chosen)>=24:break
            pairs=[(v[n],vv[idx[n]]) for n in chosen]
            if extra_targets:
                # The nearest face may be a bearing rim. Seek other real
                # primary-surface targets instead of repeatedly routing back
                # to that same blocked face.
                for n in chosen[::2]:
                    targets=[vv[idx[n]]]
                    for distance in (25.,50.):
                        for direction in np.r_[np.eye(3),-np.eye(3)]:
                            _,bi=tree.query(v[n]+distance*direction);b=vv[bi]
                            if any(np.linalg.norm(b-c)<6 for c in targets):continue
                            targets.append(b);pairs.append((v[n],b))
            for a,b in pairs:
                d=b-a;length=np.linalg.norm(d)
                if length<1e-5:continue
                axis=d/length;u=np.cross(np.eye(3)[np.argmin(abs(axis))],axis);u/=np.linalg.norm(u);w=np.cross(axis,u)
                offsets=[np.zeros(3),u*5,-u*5,w*5,-w*5]
                if not carve:offsets += [u*12,-u*12,w*12,-w*12,u*24,-u*24,w*24,-w*24]
                for offset in offsets:
                    mid=(a+b)/2+offset;beam=capsule(a,mid,radius)+capsule(mid,b,radius)
                    cb=np.asarray(beam.bounding_box())
                    indices=np.flatnonzero(np.all(np.minimum(cb[3:],obounds[:,3:])-np.maximum(cb[:3],obounds[:,:3])>0,axis=1))
                    for number,ni in enumerate(indices):
                        if not carve:
                            # Most candidate ribs miss a solid altogether.
                            # Intersect first so the expensive subtraction of
                            # the precision lands operates on a small contact,
                            # rather than retriangulating all lands per trial.
                            contact=beam^forbidden[ni][0]
                            if contact.volume()>.02 and (contact-keep).volume()>.02:
                                beam=md.Manifold();break
                            continue
                        beam=beam-forbidden[ni][0]
                        if beam.is_empty():break
                        if number%8==0:
                            linking=[x for x in beam.decompose() if (x^comp).volume()>.03 and (x^cc[0]).volume()>.03]
                            if not linking:
                                beam=md.Manifold();break
                            beam=union(linking)
                    if beam.is_empty():continue
                    candidates=[x for x in beam.decompose() if (x^comp).volume()>.03 and (x^cc[0]).volume()>.03]
                    if not candidates:continue
                    bridge=union(candidates)
                    # Preserve a connection to protruding lands, but disallow
                    # long new exposed rods far outside the anatomical volume.
                    if (bridge-outer-keep).volume()>bridge.volume()*.55:continue
                    shape=shape+bridge;records.append(dict(length_mm=float(length),radius_mm=radius,detour_mm=float(np.linalg.norm(offset)),volume_mm3=bridge.volume()));success=True;break
                if success:break
            if success:break
        if not success:break
    cc=sorted([s for s in shape.decompose() if s.volume()>.001],key=lambda s:-s.volume())
    # Unattached wall islands may be discarded; functional lands may not.
    discarded=[];selected=cc[:1]
    for c in cc[1:]:
        if (c^keep).volume()>.005:selected.append(c)
        else:discarded.append(c.volume())
    return union(selected),records,discarded


def build_one(key,parts,p,cfg,poses,ffcache,keepers,planned,reuse_incomplete=False):
    started=time.time();part=parts[key];F=frames(p,p['neutral_raw_deg']);N=F[part['token']]
    geom=canonical(part['body'],N,cfg)
    print('START WALL',key,flush=True)
    collar=geom is None
    if collar:
        A=N;I=np.linalg.inv(A);keep=keepers[key];shell=part['s']-keep
        # A re-clocked attachment can extend outside the former connector's
        # box. Use both actual attachment lands for routing permission and
        # obstacle collection; the envelope itself is never added as material.
        outer=part['s'].hull()+keep.hull();bb=np.asarray(outer.bounding_box());rows=None;lo=hi=0
    else:
        shell,outer,rows,A=geom;I=np.linalg.inv(A);bb=np.asarray(outer.bounding_box());lo,hi=rows[0,0],rows[-1,0]
        keep=move(keepers[key],I@N)
    if key=='frame/chest':
        # Direct back-case fasteners have new lands outside the F7 keep archive.
        oldp=read(C_HISTORY/'profiles/device_profile.json');oldN=frames(oldp,oldp['neutral_raw_deg'])[part['token']]
        world=move(part['s'],oldN)
        # Nut pockets end at X=-49.8 mm. The old forward extensions to
        # X=-30 mm are not precision interfaces and collide with the shoulder.
        # End the bosses at X=-45, retaining 4.8 mm beyond the pocket.
        pads=union([box([-55,y-7,z-8],[-45,y+7,z+8]) for y in (-40.,40.) for z in (500.,521.)])
        keep=keep+move(world^pads,I@N@np.linalg.inv(oldN))
        # The rear screw lands sit outside the anatomical ellipse. Allow a
        # short backing web between each vertical pair, while still checking
        # it against the actual case and every moving neighbour. Without this
        # allowance the rib router wrongly rejected every route as external.
        backing=union([box([-55,y-7,492],[-45,y+7,529]) for y in (-40.,40.)])
        outer=outer+move(backing,I@N@np.linalg.inv(oldN))
        # Neck and collar bearing lands protrude above/behind the torso loft.
        # Permit short webs inside their existing convex envelope. This adds
        # no bulk material; each actual rib must still clear every obstacle.
        outer=outer+keep.hull()
    # Protect the precision core of each actual joint. A convex hull of a
    # whole connected carrier would wrongly classify its hollow body as a bore.
    anchors=interface_anchors(part['body'],p,F)
    core=union([ball((I@np.r_[a['point'],1])[:3],a['guard_radius']*.65) for a in anchors])
    voids=core-keep
    saved_reliefs=DROOT/'source/interface_edge_reliefs.npz'
    if saved_reliefs.exists():
        rz=np.load(saved_reliefs)
        if key+'|v' in rz:
            assert read(saved_reliefs.with_suffix('.json'))['profile_sha256']==profile_signature(p)
            voids=voids+move(solid(rz[key+'|v'],rz[key+'|f']),I@N)
    # Routing may use protruding attachment lands; collect their obstacles too.
    kb=np.asarray(keep.bounding_box());bb=np.r_[np.minimum(bb[:3],kb[:3]),np.maximum(bb[3:],kb[3:])]
    low=np.full(ANGLES,lo);high=np.full(ANGLES,hi)
    if not collar:mark_opening(shell^voids,rows,low,high)
    neighbour_keys=[k for k,v in parts.items() if k!=key and adjacent(part,v,p)]
    # Use actual solids for the skin mask. A whole joint/body convex hull fills
    # intentional internal cavities and would overcut most of the chest.
    # Only web-routing guards, later, are convex swept envelopes.
    owner_members={};owner_shapes={}
    opening_ends={}
    graph={}
    for joint in p['joints']:
        graph.setdefault(joint['parent'],[]).append((joint['child'],joint['id']))
        graph.setdefault(joint['child'],[]).append((joint['parent'],joint['id']))
    def connected_anchor(other):
        # The cut follows the physical connecting joint in every pose. A shoulder
        # sweeping below mid-arm must not switch its opening to the elbow end.
        target=other['body'].split('/')[0]
        queue=[(part['body'],None)];seen=set()
        while queue:
            body,first=queue.pop(0)
            if body in seen:continue
            seen.add(body)
            if body==target and first:return next((a for a in anchors if a['joint']==first),None)
            queue.extend((child,first or jid) for child,jid in graph.get(body,[]) if child not in seen)
        if other['token'].startswith('j:'):
            jid=other['token'].split(':')[1]
            match=next((a for a in anchors if a['joint']==jid),None)
            if match:return match
        vv,_=vf(other['s']);center=(F[other['token']]@np.r_[vv.mean(0),1])[:3]
        return min(anchors,key=lambda a:np.linalg.norm(a['point']-center)) if anchors else None
    for k in neighbour_keys:
        other=parts[k];owner=(other['token'],anatomical_body(other),k)
        if not collar:
            anchor=connected_anchor(other)
            opening_ends[owner]='lower' if anchor is not None and (I@np.r_[anchor['point'],1])[2]<(lo+hi)/2 else 'upper'
        if collar and other['role']=='structure':
            path=DROOT/(k.replace('/','__')+'.npz')
            if path.exists():
                z=np.load(path);owner_shapes[owner]=solid(z['v'],z['f'])
            else:owner_shapes[owner]=other['s']
        else:owner_shapes[owner]=planned.get(k,other['s'])
        owner_members[owner]=[k]
    unique={};records=[];obstacles={}
    # Deduplicate transform families before doing expensive solid intersections.
    for qname,ff in ffcache.items():
        T=I@N@np.linalg.inv(ff[part['token']])
        for owner in owner_shapes:
            M=T@ff[owner[0]];sig=(owner,tuple(np.round(M,6).ravel()))
            if sig in unique:continue
            unique[sig]=(qname,M)
    print('TRANSFORMS',key,len(unique),flush=True)
    for (owner,_),(qname,M) in unique.items():
        ob=move(owner_shapes[owner],M);obbox=np.asarray(ob.bounding_box())
        if np.any(np.minimum(bb[3:]+4,obbox[3:])-np.maximum(bb[:3]-4,obbox[:3])<=0):continue
        clipped=ob^box(bb[:3]-4,bb[3:]+4)
        if clipped.is_empty():continue
        contact=shell^clipped
        # Actual geometry masks the wall. A coherent angular-to-end cut,
        # rather than the obstacle's tessellated imprint, defines the boundary.
        if contact.volume()>.005:
            if not collar:mark_opening(contact,rows,low,high,end=opening_ends[owner])
            records.append(dict(obstacle_owner=owner[0],members=owner_members[owner],pose=qname,wall_overlap_mm3=contact.volume()))
        # Also protect internal ribs from moving neighbours and fixed PCBs.
        # Full native meshes are unnecessary for most detached ribs; retain
        # only the nearby actual geometry for bounded connection queries.
        obstacles.setdefault(owner[0],[]).append(clipped)
    if collar:clean=md.Manifold();bottom=top=np.array([]);segments=0
    else:clean,bottom,top,segments=radial_wall(rows,low,high,cfg['wall_mm'])
    # Preserve the closed crown/fist end and its simple thumb where unaffected.
    body=part['body']
    if body=='head' and np.all(top>hi-2):
        clean=clean+(shell^box([-200,-200,hi-3.0],[200,200,hi+1]))
    if body.startswith('hand_') and np.all(bottom<lo+2):
        clean=clean+(shell^box([-200,-200,lo-1],[200,200,lo+3]))
        side=1 if body.endswith('_l') else -1
        thumb=md.Manifold.sphere(1,48).scale([10,10,18]).translate([10,side*15,-20])
        # The thumb's upper shoulder joins the wrist opening, without pinholes.
        thumb=thumb^box([-100,-100,lo-2],[100,100,min(-12,float(top.min())-2)])
        clean=clean+thumb
    print('MASK',key,'overlaps',len(records),'owner sweeps',len(obstacles),'sectors',segments,flush=True)
    # One swept convex guard per rigid owner makes internal web routing
    # conservative, without an enormous union of near-coincident screw meshes.
    swept=[md.Manifold.hull_points(np.vstack([vf(s)[0] for s in ss])) for ss in obstacles.values()]
    forbidden=[(s,np.asarray(s.bounding_box())) for s in swept+[voids] if not s.is_empty()]
    if not collar:
        vv,ff=vf(clean);np.savez_compressed(DROOT/(key.replace('/','__')+'_skin.npz'),v=vv,f=ff)
    # Keep ribs and any end-cap additions clear without perforating the new wall.
    candidate=keep+clean
    prior=None;resume_hash=None
    previous=DROOT/(key.replace('/','__')+'.json')
    if reuse_incomplete and previous.exists():
        prior=read(previous)
        assert prior.get('validated_profile_sha256',prior['construction_profile_sha256'])==profile_signature(p)
        assert prior.get('validated_pose_sha256',prior['construction_pose_sha256'])==sha(B/'profiles/daily_poses.json')
        assert prior.get('validated_keeps_sha256',prior['construction_keeps_sha256'])==sha(DROOT/'source/retained_interfaces.npz')
        assert prior['construction_configuration']==cfg
        resume_hash=sha(previous.with_suffix('.npz'))
        checkpoint=DROOT/'checkpoints';checkpoint.mkdir(exist_ok=True)
        for suffix in ('.npz','.json'):
            shutil.copy2(previous.with_suffix(suffix),checkpoint/(previous.stem+'_'+resume_hash[:12]+suffix))
        z=np.load(previous.with_suffix('.npz'))
        candidate=move(solid(z['v'],z['f']),I@N)
        print('RESUME VERIFIED INPUT',key,'components',prior['component_count'],flush=True)
    if key=='frame/chest':
        # Whole-owner convex sweeps close every torso cavity. Test the actual
        # obstacle solids directly for these long, straight internal webs.
        ribs=list(prior['ribs']) if prior else [];discarded=[]
    else:
        candidate,ribs,discarded=connect_inside(candidate,keep,forbidden,outer)
    if len([s for s in candidate.decompose() if s.volume()>.01])>1:
        print('EXACT WEB ROUTING',key,flush=True)
        exact=[(s,np.asarray(s.bounding_box())) for ss in obstacles.values() for s in ss]
        if not voids.is_empty():exact.append((voids,np.asarray(voids.bounding_box())))
        # Uncut clear ribs avoid multiplying nearly-coincident Boolean seams.
        # Reuse the untouched wall, including islands a conservative hull rejected.
        seed=candidate if prior else keep+clean
        candidate,r2,d2=connect_inside(seed,keep,exact,outer,carve=key!='frame/chest',
                                     progress_label=key if key=='frame/chest' else None,
                                     extra_targets=key=='frame/chest')
        ribs.extend(r2);discarded.extend(d2)
        if len([s for s in candidate.decompose() if s.volume()>.01])>1:
            candidate,r3,d3=connect_inside(candidate,keep,exact,outer,radius=2.5,carve=key!='frame/chest',
                                         progress_label=key if key=='frame/chest' else None,
                                         extra_targets=key=='frame/chest')
            ribs.extend(r3);discarded.extend(d3)
    relief_path=DROOT/'source/interface_edge_reliefs.npz'
    if relief_path.exists():
        rz=np.load(relief_path)
        if key+'|v' in rz:
            assert read(relief_path.with_suffix('.json'))['profile_sha256']==profile_signature(p)
            cutter=move(solid(rz[key+'|v'],rz[key+'|f']),I@N)
            candidate=candidate-cutter
    # Bounded Boolean debris only; never discard a functional island. The
    # independent topology audit uses the same 1e-4 mm3 reporting threshold.
    cc=sorted(candidate.decompose(),key=lambda c:-c.volume())
    debris=[c for c in cc[1:] if 0<c.volume()<.01]
    assert sum(c.volume() for c in debris)<.02,('excess Boolean debris',key)
    if debris:candidate=union([c for c in cc if c not in debris])
    v,f=vf(candidate);m=trimesh.Trimesh(v,f,process=False)
    result=dict(key=key,source_geometry_sha256=C_HASH,seconds=round(time.time()-started,2),
        resumed_candidate_sha256=resume_hash,
        construction_profile_sha256=profile_signature(p),builder_id=BUILDER_ID,
        construction_configuration=cfg,
        construction_pose_sha256=sha(B/'profiles/daily_poses.json'),
        construction_extra_pose_sha256=sha(B/'profiles/edge_path_poses.json') if (B/'profiles/edge_path_poses.json').exists() else None,
        construction_keeps_sha256=sha(DROOT/'source/retained_interfaces.npz'),
        mask_method='Straight bounded connections between preserved collar lands' if collar else 'Conservative swept intersections extended to nearest open end; circular dilation and smoothing',
        isolated_holes_in_radial_wall=0,angular_segments_remaining=segments,
        lower_boundary_mm=bottom,upper_boundary_mm=top,canonical_frame_mm=A,
        retained_interface_loss_mm3=max(0.,(keep-candidate).volume()),
        component_count=len([c for c in candidate.decompose() if c.volume()>1e-4]),source_watertight=bool(m.is_watertight),
        source_winding=bool(m.is_winding_consistent),volume_mm3=candidate.volume(),
        old_volume_mm3=part['s'].volume(),ribs=ribs,discarded_unattached_wall_mm3=discarded,
        cut_records=records,continuous_motion_proven=False,structural_strength_proven=False)
    return move(candidate,np.linalg.inv(N)@A),result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');ap.add_argument('--apply',action='store_true');ap.add_argument('--skip-existing',action='store_true');ap.add_argument('--repair-current',action='store_true');args=ap.parse_args()
    archive_c();DROOT.mkdir(parents=True,exist_ok=True)
    if args.apply:
        old=np.load(C_HISTORY/'assembly.npz');out={k:old[k] for k in old.files};doc=read(C_HISTORY/'assembly.json');changed=[]
        overrides=DROOT/'source/part_overrides.npz'
        extra=np.load(overrides) if overrides.exists() else {}
        profile=read(DROOT/'source/device_profile.json') if (DROOT/'source/device_profile.json').exists() else read(B/'profiles/device_profile.json')
        for item in doc['items']:
            if item['key']+'|v' in extra:
                i=str(item['index']);out[i+'v']=extra[item['key']+'|v'];out[i+'f']=extra[item['key']+'|f']
            path=DROOT/(item['key'].replace('/','__')+'.npz')
            if item['role']=='structure':
                assert path.exists(),('missing structural candidate',item['key'])
                report=read(path.with_suffix('.json'))
                assert report.get('validated_profile_sha256',report['construction_profile_sha256'])==profile_signature(profile)
                assert report.get('builder_id')==BUILDER_ID
                assert report.get('validated_pose_sha256',report.get('construction_pose_sha256'))==sha(B/'profiles/daily_poses.json')
                assert report.get('validated_keeps_sha256',report.get('construction_keeps_sha256'))==sha(DROOT/'source/retained_interfaces.npz')
                assert report['component_count']==1 and report['source_watertight'],('invalid structure',item['key'])
                assert report['retained_interface_loss_mm3']<.02,('retained land loss',item['key'])
            if not path.exists():continue
            z=np.load(path);i=str(item['index']);out[i+'v']=z['v'];out[i+'f']=z['f'];changed.append(item['key'])
        assert changed
        np.savez_compressed(B/'assembly.npz',**out);doc['revision']='O23D-continuous-walls-20261020';put(B/'assembly.json',doc)
        cfg=read(DROOT/'source/parameters.json') if (DROOT/'source/parameters.json').exists() else read(CFG)
        cfg['revision']=doc['revision'];cfg['motion_acceptance_policy']='ordinary_adjacent';put(CFG,cfg)
        if (DROOT/'source/device_profile.json').exists():
            shutil.copy2(DROOT/'source/device_profile.json',B/'profiles/device_profile.json')
            shutil.copy2(DROOT/'source/retained_interfaces.npz',B/'retained_interfaces.npz')
            spec=read(B/'profiles/daily_poses.json');spec['profile_sha256']=sha(B/'profiles/device_profile.json');put(B/'profiles/daily_poses.json',spec)
        compact=read(C_HISTORY/'design/compact_revision.json')
        rise=profile['o23_design'].get('upper_torso_raise_mm',0)
        compact['controller_frame_neutral_mm'][2][3]+=rise
        for point in compact['mount_heads_world_mm']:point[2]+=rise
        compact['o23d_upper_torso_raise_mm']=rise
        compact['revision']=doc['revision']
        compact['source_geometry_sha256']=C_HASH
        compact['geometry_sha256']=sha(B/'assembly.npz')
        compact['final_geometry_sha256']=compact['geometry_sha256']
        compact['profile_sha256']=sha(B/'profiles/device_profile.json')
        cfg['controller_front_corner_neutral_mm']=np.array(compact['controller_frame_neutral_mm'])[:3,3].tolist()
        cfg['notes']=[
            'UE-proportioned limb landmarks retained. Both physical hip pivots now coincide with the femur origins.',
            'Chest and descendants raised 22 mm; waist pivot has an 8 mm axial offset. See device_profile.json for the actual transforms.',
            'Forearm twist modules shift 8 mm toward the elbow; the right mount clocks 180 degrees. Coaxial inverse child transforms preserve body motion.',
            'Both clavicle protraction modules clock 90 degrees to move their sensor boards away from the shoulder sweep; bone frames remain unchanged.',
            'O22F7 metal, magnet, PCB and friction interface dimensions retained; anatomical walls and connector spans redesigned.',
            'Wall setting is a radial offset. Slicing, minimum normal thickness, physical fit, strength and holding-pose tests remain required.'
        ]
        put(CFG,cfg)
        put(B/'design/compact_revision.json',compact)
        put(B/'design/continuous_revision.json',dict(revision=doc['revision'],source_geometry_sha256=C_HASH,
            geometry_sha256=sha(B/'assembly.npz'),changed_structures=changed,
            user_policy='Ordinary adjacent movement required; nonadjacent contact and extreme-only failure advisory',
            manufacturing_release=False))
        print('APPLIED',len(changed),sha(B/'assembly.npz'),flush=True);return
    parts=load_c();source=DROOT/'source'
    p=read(source/'device_profile.json') if (source/'device_profile.json').exists() else read(B/'profiles/device_profile.json')
    cfg=read(source/'parameters.json') if (source/'parameters.json').exists() else read(CFG)
    spec=read(B/'profiles/daily_poses.json');poses=spec['poses']
    extra_path=B/'profiles/edge_path_poses.json'
    if extra_path.exists():poses.update(read(extra_path)['poses'])
    ffcache={name:frames(p,q) for name,q in poses.items()};F=frames(p,p['neutral_raw_deg'])
    kz=np.load(source/'retained_interfaces.npz' if (source/'retained_interfaces.npz').exists() else C_HISTORY/'retained_interfaces.npz')
    keepers={k:solid(kz[k+'|v'],kz[k+'|f']) for k,v in parts.items() if v['role']=='structure'}
    planned={}
    for k,v in parts.items():
        if v['role']!='structure':continue
        geom=canonical(v['body'],F[v['token']],cfg)
        if geom:
            shell,_,_,A=geom
            planned[k]=keepers[k]+move(shell,np.linalg.inv(F[v['token']])@A)
    for key,part in sorted(parts.items(),key=lambda item:item[0].startswith('frame/clavicle')):
        if part['role']!='structure' or (args.keys and key not in args.keys):continue
        previous=DROOT/(key.replace('/','__')+'.json')
        if args.skip_existing and previous.exists():
            row=read(previous)
            if row.get('validated_profile_sha256',row.get('construction_profile_sha256'))==profile_signature(p) and row.get('builder_id')==BUILDER_ID and row.get('component_count')==1 and row.get('validated_pose_sha256',row.get('construction_pose_sha256'))==sha(B/'profiles/daily_poses.json') and row.get('validated_keeps_sha256',row.get('construction_keeps_sha256'))==sha(source/'retained_interfaces.npz'):
                print('REUSE',key,flush=True);continue
        built=build_one(key,parts,p,cfg,poses,ffcache,keepers,planned,args.repair_current)
        if built is None:continue
        s,report=built;stem=key.replace('/','__');v,f=vf(s)
        np.savez_compressed(DROOT/(stem+'.npz'),v=v,f=f);put(DROOT/(stem+'.json'),report)
        print('WALL',key,'components',report['component_count'],'land loss',report['retained_interface_loss_mm3'],
              'sectors',report['angular_segments_remaining'],'ribs',len(report['ribs']),'seconds',report['seconds'],flush=True)


if __name__=='__main__':main()
