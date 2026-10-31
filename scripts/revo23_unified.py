"""O23I: continuous mounting envelopes over the verified H load paths."""
from repair_revo23_endfaces import *
from functools import lru_cache

HHASH='538c5c2bb9ba8445058fc95251ed41d3908bbbb6c48ac6ece0d92314f5e09459'
IROOT=B/'design/unified_candidate'
IHISTORY=B/'history/O23H_before_unified_mounts_20261021'
IREV='O23I-unified-mount-contours-20261021'

def initialize_i():
    IROOT.mkdir(exist_ok=True)
    if (IHISTORY/'snapshot.json').exists():
        assert sha(IHISTORY/'assembly.npz')==HHASH;return
    assert sha(B/'assembly.npz')==HHASH
    IHISTORY.mkdir(exist_ok=True)
    files=['assembly.npz','assembly.json','retained_interfaces.npz','DELIVERY.json','DESIGN.zh-CN.md','CONNECTION_END_FACES.zh-CN.md']
    for folder in ('profiles','harness','preview'):
        files += [p.relative_to(B).as_posix() for p in (B/folder).rglob('*') if p.is_file()]
    files += [p.relative_to(B).as_posix() for p in (B/'verification').glob('*.json')]
    for rel in files:
        dst=IHISTORY/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/rel,dst)
    shutil.copy2(CFG,IHISTORY/'parameters.json')
    shutil.copytree(GHISTORY/'skins',IHISTORY/'skins',dirs_exist_ok=True)
    shutil.copytree(HROOT/'mount_reinforcement',IROOT/'mount_reinforcement',dirs_exist_ok=True)
    (IHISTORY/'connections').mkdir(exist_ok=True)
    parts,p,cfg=load_h()
    for key,item in parts.items():
        if item['role']!='structure':continue
        name=key.replace('/','__')
        shutil.copy2(HROOT/(name+'.json'),IHISTORY/'connections'/(name+'.json'))
        shutil.copy2(HROOT/(name+'.json'),IROOT/(name+'.json'))
        shutil.copy2(HROOT/(name+'.npz'),IROOT/(name+'.npz'))
    shutil.copytree(B/'profiles',IROOT/'profiles',dirs_exist_ok=True)
    shutil.copytree(B/'harness',IROOT/'harness',dirs_exist_ok=True)
    (IROOT/'verification').mkdir(exist_ok=True)
    put(IHISTORY/'snapshot.json',dict(revision=HREV,geometry_sha256=HHASH,files={f:sha(IHISTORY/f)for f in files}))
    put(IROOT/'WORK_IN_PROGRESS.json',dict(revision=IREV,status='designing_continuous_mounts',baseline_geometry_sha256=HHASH))

def load_i():
    initialize_i();z=np.load(IHISTORY/'assembly.npz');parts={}
    for row in read(IHISTORY/'assembly.json')['items']:
        path=IROOT/(row['key'].replace('/','__')+'.npz');i=str(row['index'])
        if path.exists():
            q=np.load(path);s=solid(q['v'],q['f'])
        else:s=solid(z[i+'v'],z[i+'f'])
        parts[row['key']]=dict(row,s=s)
    return parts,read(IHISTORY/'profiles/device_profile.json'),read(IHISTORY/'parameters.json')

@lru_cache(maxsize=None)
def h_part(key):
    z=np.load(IHISTORY/'assembly.npz');item=next(x for x in read(IHISTORY/'assembly.json')['items']if x['key']==key);i=str(item['index'])
    return solid(z[i+'v'],z[i+'f'])

def i_records(key):return read(IROOT/(key.replace('/','__')+'.json'))

def stage_i():
    parts,p,cfg=load_i();out={};changed=[]
    for key,item in parts.items():
        i=str(item['index']);out[i+'v'],out[i+'f']=vf(item['s'])
        if item['role']=='structure':changed.append(key)
    np.savez_compressed(IROOT/'assembly.npz',**out)
    put(IROOT/'assembly.json',dict(revision=IREV,items=[{k:v for k,v in r.items()if k!='s'}for r in parts.values()]))
    put(IROOT/'staging.json',dict(input_geometry_sha256=HHASH,geometry_sha256=sha(IROOT/'assembly.npz'),changed_parts=changed,candidate_files={k:sha(IROOT/(k.replace('/','__')+'.npz'))for k in changed}))
    cfg['revision']=IREV;put(IROOT/'parameters.json',cfg)
    return parts,p,cfg

@lru_cache(maxsize=None)
def functional_voids(key):
    row=next(x for x in read(HROOT/'export/repair.json')['rows']if x['key']==key)
    q=np.load(HROOT/'print/guards_v5'/(row['id']+'.npz'))
    return wire_spaces(key)+(solid(q['v'],q['f'])-h_part(key))

@lru_cache(maxsize=None)
def manufacturing_voids(key):
    """Continue existing bores through added fairings, keeping their mouths open."""
    row=next(x for x in read(HROOT/'export/repair.json')['rows']if x['key']==key)
    q=np.load(HROOT/'print/guards_v5'/(row['id']+'_wire.npz'));wires=solid(q['v'],q['f'])
    small=functional_voids(key)-wires;extended=[functional_voids(key)];records=[]
    for part in small.decompose():
        if part.volume()<.1:continue
        vertices=vf(part)[0];center=vertices.mean(0);_,_,axes=np.linalg.svd(vertices-center,full_matrices=False)
        options=[]
        for direction in list(np.eye(3))+list(axes):
            z=direction/np.linalg.norm(direction);x=np.cross(np.eye(3)[np.argmin(abs(z))],z);x/=np.linalg.norm(x);R=np.array([x,np.cross(z,x),z]);T=np.eye(4);T[:3,:3]=R
            local=move(part,T);cs=local.project();span=np.array(cs.bounds());width=span[2:]-span[:2]
            if min(width)<.05:continue
            # A bore axis projects a compact nearly circular/hexagonal mouth,
            # independently of whether its length exceeds its diameter.
            perimeter=sum(np.linalg.norm(np.roll(loop,-1,axis=0)-loop,axis=1).sum()for loop in cs.to_polygons())
            compactness=4*np.pi*abs(cs.area())/max(perimeter**2,1e-9)
            score=1-compactness+.1*abs(np.log(width[0]/width[1]))
            options.append((score,R,cs,local.bounding_box()))
        _,R,cs,bb=min(options,key=lambda a:a[0]);T=np.eye(4);T[:3,:3]=R.T
        extension=move(cs.extrude(bb[5]-bb[2]+80).translate([0,0,bb[2]-40]),T)
        extended.append(extension);records.append(dict(bore_volume_mm3=part.volume(),axis_body=R[2],extension_each_end_mm=40))
    for seat in read(IHISTORY/'harness/wire_seats.json')['seats']:
        if seat['part']!=key:continue
        T=np.array(seat['transform_body_mm'])
        extended.append(move(box([-35,.6,-1.7],[35,2.4,1.7]),T))
    result=union(extended);dest=IROOT/'manufacturing_voids';dest.mkdir(exist_ok=True)
    path=dest/(key.replace('/','__')+'.npz');save_s(path,result)
    put(path.with_suffix('.json'),dict(part=key,baseline_geometry_sha256=HHASH,bores=records,method='Extend existing small-hole projections and tie-slot mouths through added material only. Original H material is never removed.'))
    return result

def segment_prefix(points,length):
    points=np.asarray(points);dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    length=min(length,dist[-1]*.38)
    j=np.searchsorted(dist,length);j=max(1,min(j,len(points)-1))
    a=(length-dist[j-1])/(dist[j]-dist[j-1]);end=points[j-1]+a*(points[j]-points[j-1])
    return np.vstack([points[:j],end])

def unified_envelope(native,attachments,paths,radius=.5):
    """One convex mounting volume with rounded outside edges and tapered exits."""
    seed=union([native]+attachments)
    hull=md.Manifold.hull_points(vf(seed)[0]);vertices=vf(hull)[0]
    sphere=trimesh.creation.icosphere(subdivisions=2,radius=radius).vertices
    points=[(vertices[:,None,:]+sphere).reshape(-1,3)]
    for pts,r in paths:
        short=segment_prefix(pts,12.)
        points.append(vf(positive_round_sweep(short,r))[0])
    return md.Manifold.hull_points(np.vstack(points))

def wall_groups(records):
    groups=[]
    for i,r in enumerate(records):
        if 'target_mount'in r:continue
        pos=np.array(r['wall_landing_world_mm'])
        near=[g for g in groups if any(np.linalg.norm(pos-np.array(records[j]['wall_landing_world_mm']))<14 for j in g)]
        if near:
            joined=[i]+[j for g in near for j in g];groups=[g for g in groups if g not in near];groups.append(joined)
        else:groups.append([i])
    return groups

def wire_fairing(original,seat,M):
    T=M@np.array(seat['transform_body_mm']);Ti=np.linalg.inv(T)
    w=seat['reserved_channel_width_mm'];half=4.5 if seat['body'].startswith('forearm_')else 6.
    local=move(original,Ti)^box([-w/2-3.6,-7.5,-half-4],[w/2+3.6,5.2,half+4])
    if local.is_empty():return md.Manifold()
    v=vf(md.Manifold.hull_points(vf(local)[0]))[0]
    directions=trimesh.creation.icosphere(subdivisions=1,radius=1).vertices
    # Zero expansion at the two cropped ends keeps the transition flush with
    # the existing carrier; the seat perimeter receives a small rounded edge.
    weight=.4*np.clip(1-(abs(v[:,2])/(half+4))**2,0,1)
    envelope=md.Manifold.hull_points((v[:,None,:]+weight[:,None,None]*directions).reshape(-1,3))
    return move(envelope,T)

def relieve(envelope,original,space,voids):
    candidate=envelope-voids;reliefs=[]
    for _ in range(200):
        ok,why=space.clear(candidate-original)
        if ok:return candidate,reliefs
        row=next(x for x in space.records if x['key']==why['part'] and x['pose']==why['pose'])
        obstacle=row['solid'];v=vf(obstacle)[0]
        # Broad, exact functional reliefs; no overlapping decorative patch solids.
        offsets=np.array(list(itertools.product((-.25,.25),repeat=3)))
        keepout=md.Manifold.hull_points((v[:,None,:]+offsets).reshape(-1,3))
        candidate-=keepout
        reliefs.append(dict(part=why['part'],pose=why['pose'],clearance_mm=.25))
    raise RuntimeError(('Unconverged unified mount',space.key))

def open_added_cavities(key,addition):
    """Keep necessary access recesses open; never discard negative cavity shells."""
    old=h_part(key);records=[]
    for attempt in range(12):
        candidate=old+addition;parts=candidate.decompose()
        cavities=[c for c in parts if c.volume()<-.001]
        if not cavities:
            main=max(parts,key=lambda c:c.volume());missing=max(0.,(old-main).volume())
            assert missing<.01,(key,'discard would remove H material',missing)
            return main,records
        cavity=min(cavities,key=lambda c:c.volume());v=vf(cavity)[0];center=v.mean(0);bb=np.array(candidate.bounding_box())
        corners=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))));best=None
        directions=[np.array(x,float)for x in itertools.product((-1,0,1),repeat=3)if any(x)]
        directions.sort(key=lambda d:np.count_nonzero(d))
        for d in directions:
            d=d/np.linalg.norm(d);length=max((corners-center)@d)-min((v-center)@d)+2
            channel=md.Manifold.hull_points(np.vstack([v-.1*d,v+d*length]))
            trial_add=addition-channel;trial=old+trial_add
            remaining=[c for c in trial.decompose()if c.volume()<-.001]
            if len(remaining)>=len(cavities):continue
            removed=max(0.,addition.volume()-trial_add.volume());score=removed+.05*length
            if best is None or score<best[0]:best=(score,trial_add,channel,dict(cavity_mm3=-cavity.volume(),direction_body=d,opening_length_mm=length,removed_added_material_mm3=removed))
        if best is None:raise RuntimeError((key,'No open access path for a new enclosed recess'))
        _,addition,channel,record=best;records.append(record)
        dest=IROOT/'access_reliefs';dest.mkdir(exist_ok=True);save_s(dest/(key.replace('/','__')+f'__{attempt}.npz'),channel)
    raise RuntimeError((key,'Too many enclosed access pockets'))

def build(key,all_mounts=False):
    parts,p,cfg=load_i();N=frames(p,p['neutral_raw_deg']);M=N[parts[key]['token']];I=np.linalg.inv(M)
    original=move(h_part(key),M);record=i_records(key);hosts=native_hosts(key,parts,p,N)
    space=Space(key,parts,p,N,False);voids=move(manufacturing_voids(key),M)
    mounts={i:dict(attachments=[],paths=[],rods=[])for i in range(len(hosts))}
    for i,r in enumerate(record['rods']):
        pts=np.array(r['centerline_world_mm'])
        for end,mount,path in [('source',r['mount'],pts)]+([('target',r['target_mount'],pts[::-1])]if 'target_mount'in r else []):
            q=mounts[mount];q['paths'].append((path,r['radius_mm']));q['rods'].append(i)
            if end+'_socket'in r:q['attachments'].append(socket_solid(r[end+'_socket']))
            if end=='source':q['attachments'] += [tapered(x['start_world_mm'],x['end_world_mm'],x['r0_mm'],x['r1_mm'])for x in r.get('source_feet',[])]
    results=[];added=[];outdir=IROOT/'unified_mounts';outdir.mkdir(exist_ok=True)
    for mount,q in mounts.items():
        if not q['paths']:continue
        has_head=any(read(f)['mount']==mount for f in (HROOT/'mount_reinforcement').glob(key.replace('/','__')+'*.json')if 'mount'in read(f))
        needs=bool(q['attachments'] or has_head or all_mounts)
        if not needs:
            results.append(dict(mount=mount,status='inspected_no_stacked_adapter',rods=q['rods']));continue
        envelope=unified_envelope(hosts[mount],q['attachments'],q['paths'])
        smooth,reliefs=relieve(envelope,original,space,voids)
        delta=smooth-original;volume=max(0.,delta.volume())
        if volume<.5:
            results.append(dict(mount=mount,status='functional_clearances_leave_no_external_fill',added_mm3=volume,reliefs=reliefs,rods=q['rods']));continue
        path=outdir/(key.replace('/','__')+f'__m{mount}.npz');save_s(path,move(smooth,I))
        added.append(smooth);results.append(dict(mount=mount,status='unified_contour',added_mm3=volume,rods=q['rods'],reliefs=reliefs,geometry_sha256=sha(path)))
        print('UNIFIED',key,mount,'added',round(volume,1),'reliefs',len(reliefs),flush=True)
    auxiliary=[]
    for indices in wall_groups(record['rods']):
        # Merge overlapping wall-foot collars into one continuous landing.
        pads=[wall_pad(record['rods'][j])for j in indices]
        paths=[(np.array(record['rods'][j]['centerline_world_mm'])[::-1],record['rods'][j]['radius_mm'])for j in indices]
        envelope=unified_envelope(union(pads),[],paths,.3)
        smooth,reliefs=relieve(envelope,original,space,voids);volume=max(0.,(smooth-original).volume())
        if volume>.5:added.append(smooth)
        auxiliary.append(dict(type='wall_landing',rods=indices,added_mm3=volume,reliefs=reliefs))
    for seat in read(IHISTORY/'harness/wire_seats.json')['seats']:
        if seat['part']!=key:continue
        envelope=wire_fairing(original,seat,M)
        if envelope.is_empty():continue
        smooth,reliefs=relieve(envelope,original,space,voids);volume=max(0.,(smooth-original).volume())
        if volume>.5:added.append(smooth)
        auxiliary.append(dict(type='wire_seat',id=seat['id'],added_mm3=volume,reliefs=reliefs))
    additions=union(added)
    if key.startswith('frame/hand_'):
        frame=np.array(next(r for r in read(FROOT/'skins.json')['skins']if r['key']==key)['canonical_frame_mm'])
        additions=additions^move(box([-150,-150,-21.5],[150,150,150]),frame)
    # Recut the added material in the final body coordinates. This avoids
    # coincident transformed void boundaries being lost in a later union.
    addition_body=(move(additions,I)-h_part(key))-manufacturing_voids(key)
    candidate,access_reliefs=open_added_cavities(key,addition_body)
    cc=[s for s in candidate.decompose()if abs(s.volume())>.001];assert len(cc)==1,(key,'separate surfaces',[(s.volume())for s in cc])
    missing=max(0.,(h_part(key)-cc[0]).volume());intrusion=max(0.,((cc[0]-h_part(key))^functional_voids(key)).volume())
    assert missing<.01,(key,'removed',missing)
    if intrusion>=.03:
        save_s(IROOT/(key.replace('/','__')+'_failed_void.npz'),cc[0])
        raise AssertionError((key,'void_intrusion_mm3',intrusion))
    path=IROOT/(key.replace('/','__')+'.npz');save_s(path,cc[0])
    record.update(revision=IREV,candidate_sha256=sha(path),unified_mounts=results,unified_auxiliary=auxiliary,access_reliefs=access_reliefs,source_geometry_sha256=HHASH)
    put(path.with_suffix('.json'),record)
    return results

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');ap.add_argument('--all-mounts',action='store_true');a=ap.parse_args();initialize_i()
    parts,_,_=load_i()
    for key in a.keys or [k for k,x in parts.items()if x['role']=='structure']:build(key,a.all_mounts)
