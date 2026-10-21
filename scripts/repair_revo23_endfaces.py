"""Search seated connectors. No clipping, no extra rods, no spherical patches."""
from revo23_endfaces import *
from seat_revo23_round_roots import wire_spaces as documented_wire_spaces
from scipy.optimize import linear_sum_assignment
import copy
from scipy.ndimage import minimum_filter

_functional_cache={}
def wire_spaces(key):
    """Retain wire fixtures and the original fastener/magnet aperture clearances."""
    if key in _functional_cache:return _functional_cache[key]
    keepout=documented_wire_spaces(key)
    row=next((r for r in read(B/'design/export_repair_G/repair.json')['rows'] if r['key']==key),None)
    if row:
        path=B/'print_optimization_G/guards_v5'/(row['id']+'.npz');z=np.load(path);guard=solid(z['v'],z['f'])
        original=read(GHISTORY/'assembly.json');item=next(x for x in original['items'] if x['key']==key);n=np.load(GHISTORY/'assembly.npz');i=str(item['index'])
        # Remove the baseline CAD, resolving only its STL quantization boundary;
        # every originally empty aperture remains a geometric keepout.
        guard=guard-solid(n[i+'v'],n[i+'f']);keepout+=guard
    _functional_cache[key]=keepout;return keepout

def rectangular_bases(host,radius,near,rotated=True):
    """Dense erosion locates thin flanges that sparse sphere-oriented seeds miss."""
    import hashlib
    verts,faces=vf(host);digest=hashlib.sha256(verts.tobytes()+faces.tobytes()+str((radius,rotated,near.tolist(),'v2')).encode()).hexdigest()
    cache=HROOT/'search_cache'/(digest+'.json')
    if cache.exists():return read(cache)
    pitch=.5;bb=np.array(host.bounding_box());origin=np.floor((bb[:3]-2)/pitch)*pitch
    shape=tuple((np.ceil((bb[3:]+2-origin)/pitch).astype(int)+1).tolist());mask=raster(host,origin,shape,pitch)
    sizes=[(4.,14.),(14.,4.),(3.,18.),(18.,3.),(6.,10.),(10.,6.),(8.,8.),(5.,11.),(11.,5.),(3.,14.),(14.,3.),(2.5,20.),(20.,2.5),(4.,11.),(11.,4.)] if radius>=4 else [(4.,11.),(11.,4.),(3.,15.),(15.,3.),(6.,8.),(8.,6.),(5.,9.),(9.,5.)]
    proposals=[]
    for axis in range(3):
        uaxis=(axis+1)%3;vaxis=(axis+2)%3
        for w,h in sizes:
            extent=np.zeros(3);extent[axis]=.8;extent[uaxis]=w;extent[vaxis]=h
            sz=2*np.maximum(0,np.floor((extent/2-.3)/pitch).astype(int))+1
            indices=np.argwhere(minimum_filter(mask,size=tuple(sz),mode='constant',cval=0))
            if not len(indices):continue
            pp=origin+indices*pitch;pp=pp[np.argsort(np.linalg.norm(pp-near,axis=1))]
            for a in pp[:180]:
                for sign in (1,-1):
                    d=np.eye(3)[axis]*sign;u=np.eye(3)[uaxis]
                    f=dict(base_world_mm=a,normal_world=d,u_world=u,width_mm=w,height_mm=h,depth_mm=8.,top_radius_mm=radius+.8)
                    if socket_base_witness(host,f)['passed']:proposals.append(f)
    if rotated:
        vertices,faces=vf(host);mesh=trimesh.Trimesh(vertices,faces,process=False)
        order=np.argsort(-mesh.area_faces);basis=[]
        for i in order:
            n=mesh.face_normals[i]
            if all(abs(n@a)<.995 for a in basis):basis.append(n)
            if len(basis)>=5:break
        if len(basis)>=2:
            z=basis[0];y=next((v for v in basis[1:] if abs(v@z)<.1),None)
            if y is not None:
                y=y-z*(y@z);y/=np.linalg.norm(y);x=np.cross(y,z);Q=np.c_[x,y,z]
                if np.max(abs(Q),axis=0).min()<.995:
                    T=np.eye(4);T[:3,:3]=Q.T
                    for f in rectangular_bases(move(host,T),radius,Q.T@near,False):
                        f['base_world_mm']=Q@f['base_world_mm'];f['normal_world']=Q@f['normal_world'];f['u_world']=Q@f['u_world'];proposals.append(f)
    proposals.sort(key=lambda f:np.linalg.norm(np.array(f['base_world_mm'])-near))
    put(cache,proposals)
    return proposals

def structural_connectors(records):
    solids=[]
    for r in records:
        solids.append(rod_body(r))
        if 'target_mount' not in r:solids.append(wall_pad(r))
        solids.extend(tapered(f['start_world_mm'],f['end_world_mm'],f['r0_mm'],f['r1_mm']) for f in r.get('source_feet',[]))
        if 'source_socket' in r:solids.append(socket_solid(r['source_socket']))
        if 'target_socket' in r:solids.append(socket_solid(r['target_socket']))
    return union(solids)

def preserved_material(key,parts,p,N,include_residual=True):
    """Remove old connectors, but preserve original native lands, skins and seats."""
    M=N[parts[key]['token']];old=read(GHISTORY/'connections'/(key.replace('/','__')+'.json'))['rods']
    z=np.load(GHISTORY/'assembly.npz');idx=str(parts[key]['index']);original=move(solid(z[idx+'v'],z[idx+'f']),M)
    protected=move(native_keep(key)+clean_skin(key)+mount_reinforcement(key),M)
    for r in read(GHISTORY/'harness/wire_seats.json')['seats']:
        if r['part']!=key:continue
        w=r['reserved_channel_width_mm'];h=4.5 if r['body'].startswith('forearm_') else 6.
        # Preserve actual printed seat geometry, not a nominal replacement.
        envelope=move(box([-w/2-3.2,-4.2,-h-.2],[w/2+3.2,5.2,h+.2]),M@np.array(r['transform_body_mm']))
        protected+=original^envelope
    residual=original-structural_connectors(old)
    if not include_residual:return protected
    return protected+union([s for s in residual.decompose() if s.volume()>.0001])

def quick_face(host,a,d,r):
    probe=cyl(a-d*.84,a+d*.64,r)
    return (probe^host).volume()/probe.volume()>=.98 and face_witness(host,a,d,r)['passed']

def endpoints(r,host):
    pts=np.array(r['centerline_world_mm']);b=pts[-1];d=b-pts[-2];d/=np.linalg.norm(d)
    if r.get('internal_waypoint'):return [b]
    opts=[b]
    if len(pts)>4:opts.extend(pts[-j] for j in (2,3,4))
    if 'target_mount' not in r:
        pos=np.array(r['wall_landing_world_mm']);n=pos-b;n/=np.linalg.norm(n)
        opts.extend(b+n*t for t in (.8,1.6,-.8))
    else:
        e=pts[-2]-pts[-3];e/=np.linalg.norm(e)
        opts.extend(pts[-2]+e*t for t in (-4.,-2.,1.,2.,4.,6.,10.))
    return opts

def curve(a,d,b,e,scale):
    length=np.linalg.norm(b-a);s=scale
    # Straight first and last intervals establish the true flat-end normals.
    a1=a+d*1.6;b1=b-e*1.6
    ctrl=[a1,a1+d*s,b1-e*s,b1];t=np.linspace(0,1,max(16,int(max(length,2*s)*1.5)))[:,None]
    q=(1-t)**3*ctrl[0]+3*(1-t)**2*t*ctrl[1]+3*(1-t)*t*t*ctrl[2]+t**3*ctrl[3]
    return np.vstack([a,a+d*.8,q,b-e*.8,b])

def sensible(points,r):
    steps=np.diff(points,axis=0);length=np.linalg.norm(steps,axis=1)
    if min(length)<.00001:return False
    u=steps/length[:,None];angle=np.arccos(np.clip((u[:-1]*u[1:]).sum(1),-1,1))
    return np.all((length[:-1]+length[1:])*.5/np.maximum(angle,1e-9)>r*1.15)

def search(r,source,target,space,wires,other=None,ospace=None,owires=None,source_common=None):
    radius=r['radius_mm'];old=np.array(r['centerline_world_mm']);reflection=np.diag([1.,-1.,1.,1.])
    common=source if source_common is None else source_common
    points=source_points(common,pitch=1.,limit=600)
    points=points[np.argsort(np.linalg.norm(points-old[0],axis=1))]
    endopts=endpoints(r,target);fails={};valid=[];attempts=0
    def accept(pts,method,socket=None):
        nonlocal attempts
        attempts+=1
        if attempts%2500==0:print('SEARCH',space.key,r['mount'],attempts,fails,flush=True)
        if not sensible(pts,radius):fails['curvature']=fails.get('curvature',0)+1;return None
        a=pts[0];d=pts[1]-a;d/=np.linalg.norm(d)
        b=pts[-1];e=pts[-2]-b;e/=np.linalg.norm(e)
        shost=common if socket is None else socket_solid(socket)
        if not quick_face(shost,a,d,radius):fails['start face']=fails.get('start face',0)+1;return None
        if not quick_face(target,b,e,radius):fails['target face']=fails.get('target face',0)+1;return None
        if socket is not None:
            if (shost^wires).volume()>.01:fails['foot wire']=fails.get('foot wire',0)+1;return None
            ok,why=space.clear(shost)
            if ok and ospace:ok,why=ospace.clear(move(shost,reflection))
            if ok and owires is not None and (move(shost,reflection)^owires).volume()>.01:ok=False;why={'part':'mirror wire'}
            if not ok:fails['foot '+why['part']]=fails.get('foot '+why['part'],0)+1;return None
        candidate=cyl(a,b,radius) if len(pts)==2 else positive_round_sweep(pts,radius)
        if candidate.genus()!=0 or len(candidate.decompose())!=1:return None
        if socket is not None:candidate+=shost
        if (candidate^wires).volume()>.01:fails['wire']=fails.get('wire',0)+1;return None
        ok,why=space.clear(candidate)
        if ok and ospace:ok,why=ospace.clear(move(candidate,reflection))
        if ok and owires is not None and (move(candidate,reflection)^owires).volume()>.01:ok=False;why={'part':'mirror wire'}
        if not ok:fails[why['part']]=fails.get(why['part'],0)+1;return None
        rec=copy.deepcopy(r);rec.pop('mirrored_from',None);rec.pop('source_feet',None);rec.pop('foot_only',None)
        rec.pop('source_socket',None)
        if socket is not None:rec['source_socket']=socket
        rec.update(centerline_world_mm=pts,positive_cells=True,method=method,
            source_end_face=face_witness(shost,a,d,radius),target_end_face=face_witness(target,b,e,radius))
        rec['source_cap_embedded_fraction']=rec['source_end_face']['first_stem_coverage']
        rec['source_cap_host']='native_land' if socket is None else 'source_socket'
        rec['land_overlap_mm3']=(candidate^source).volume()
        if 'target_mount' not in r:rec['wall_foot_reference_endpoint_world_mm']=r.get('wall_foot_reference_endpoint_world_mm',old[-1])
        return rec
    # Most locations need a few millimetres more axial purchase, not new routing.
    direct=sorted([(np.linalg.norm(b-a)+.1*np.linalg.norm(a-old[0]),a,b)for a in points for b in endopts],key=lambda x:x[0])
    for _,a,b in direct:
        rr=accept(np.array([a,b]),'Full-section straight stem; both flat end faces buried in independently checked hosts.')
        if rr:return rr,fails
    # Search fixed normals through native plate material, then a smooth approach.
    vv,ff=vf(common);mm=trimesh.Trimesh(vv,ff,process=False);axes=list(np.r_[np.eye(3),-np.eye(3)])
    for ii in np.argsort(-mm.area_faces)[:40]:
        normal=mm.face_normals[ii]
        if all(abs(normal@ax)<.995 for ax in axes):axes.extend([normal,-normal])
        if len(axes)>=16:break
    axes=np.array(axes)
    for a in points:
        for d in axes:
            if quick_face(common,a,d,radius):valid.append((a,d))
    print('SEATED STARTS',space.key,r['mount'],len(valid),'failures',fails,flush=True)
    # Connect to either the final wall foot or a tangent on the existing safe path.
    goals=[]
    for b in endopts:
        n=(np.array(r['wall_landing_world_mm'])-b) if 'target_mount' not in r else old[-1]-old[-2]
        n/=np.linalg.norm(n);goals.append((b,n,None))
    if len(old)>3 and not r.get('internal_waypoint'):
        tails=[]
        for cut in (1,2,3):
            tail=old[:-cut];e=tail[-2]-tail[-1];e/=np.linalg.norm(e)
            if sensible(tail[3:],radius) and quick_face(target,tail[-1],e,radius):tails.append(tail)
        if 'target_mount' in r:
            direction=old[-2]-old[-3];direction/=np.linalg.norm(direction)
            for length in (1.,2.,4.,6.,10.):
                b0=old[-2]+direction*length;tail=np.vstack([old[:-1],b0])
                if quick_face(target,b0,-direction,radius):tails.append(tail)
        if 'target_mount' not in r:
            for trim in (10,18,28,40):
                if trim>=len(old)-4:continue
                j=len(old)-trim;a0=old[j];d0=old[j]-old[j-1];d0/=np.linalg.norm(d0)
                for b0 in endopts:
                    e0=np.array(r['wall_landing_world_mm'])-b0;e0/=np.linalg.norm(e0)
                    for sc in (4.,8.,14.):
                        endcurve=curve(a0,d0,b0,e0,sc)
                        q=np.vstack([old[:j],endcurve])
                        # The original source may have a cusp; inspect only the tail.
                        if sensible(q[3:],radius):tails.append(q)
        tails.append(old)
        distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old,axis=0),axis=1))]
        for s in (8,14,22,32,42):
            j=int(np.argmin(abs(distance-s)))
            if j<3 or j>=len(old)-3:continue
            for fixed in tails:
                if j>=len(fixed)-3:continue
                tail=fixed[j:];e=fixed[j+1]-fixed[j];e/=np.linalg.norm(e)
                goals.append((fixed[j],e,tail))
    options=sorted([(np.linalg.norm(b-a)+.2*np.linalg.norm(a-old[0]),a,d,b,e,tail) for a,d in valid for b,e,tail in goals],key=lambda x:x[0])
    for _,a,d,b,e,tail in options:
        if np.dot(b-a,d)<-1:continue
        for scale in (4.,8.,14.,22.):
            pts=curve(a,d,b,e,scale)
            if tail is not None:pts=np.vstack([pts,tail[1:]])
            rr=accept(pts,'Full-section stem with constrained straight end tangents and seated flat caps.')
            if rr:return rr,fails
    # A thin mounting flange cannot contain a full round cap. Use an explicit
    # broad rectangular foot with its entire flat base seated on that flange.
    sockets=rectangular_bases(common,radius,old[0])
    print('SEATED SOCKETS',space.key,r['mount'],len(sockets),flush=True)
    for f0 in (sockets if r.get('internal_waypoint') or np.linalg.norm(np.diff(old,axis=0),axis=1).sum()>35 else []):
        base=np.array(f0['base_world_mm']);d=np.array(f0['normal_world']);u=np.array(f0['u_world']);v=np.cross(d,u)
        for neck,depth in ((4.,10.),(8.,14.),(12.,18.)):
            f=dict(f0,neck_mm=neck,depth_mm=depth,top_radius_mm=radius+1.4,socket_length_mm=3.5)
            pad=socket_solid(f);a=base+d*(depth-1.5)
            if not quick_face(pad,a,d,radius):continue
            if (pad^wires).volume()>.01:continue
            ok,why=space.clear(pad)
            if ok and ospace:ok,why=ospace.clear(move(pad,reflection))
            if not ok:continue
            for goal,e,tail in goals:
                if tail is None:
                    rr=accept(np.array([a,goal]),'Direct circular stem buried in a full flat mounting foot with a clearance neck.',f)
                    if rr:return rr,fails
                for tangent in (d,-d):
                    for sc in (4.,8.,14.,22.):
                        pts=curve(a,tangent,goal,e,sc)
                        if tail is not None:pts=np.vstack([pts,tail[1:]])
                        rr=accept(pts,'Circular stem and full flat mounting foot with a constant-section clearance neck.',f)
                        if rr:return rr,fails
    # Orient the round socket to the stem, independently of the flat flange base.
    # This is a tapered adapter, not a round rod laid against a mounting edge.
    for shift in (0.,6.,-6.,10.,-10.):
      for f0 in sockets:
        base=np.array(f0['base_world_mm']);normal=np.array(f0['normal_world']);u=np.array(f0['u_world']);v=np.cross(normal,u)
        for neck,depth in ((4.,10.),(8.,14.),(12.,18.),(0.,6.),(0.,9.),(0.,13.)):
            top=base+normal*depth+v*shift
            for goal,tail_e,tail in goals:
                e=goal-top;dist=np.linalg.norm(e)
                if dist<4:continue
                e/=dist
                # Both end planes must be supporting planes of the convex foot.
                if depth-(radius+1.4)*np.sqrt(max(0.,1-(normal@e)**2))<.8:continue
                corners=np.array([base+x*u+y*v for x,y in itertools.product((-f0['width_mm']/2,f0['width_mm']/2),(-f0['height_mm']/2,f0['height_mm']/2))])
                # The rod cap is internal to the adapter. Only the native-facing
                # base must be an extreme plane; a wide flange may extend past
                # the circular socket in the stem direction.
                f=dict(f0,neck_mm=neck,depth_mm=depth,top_radius_mm=radius+1.4,top_normal_world=e,top_offset_world_mm=v*shift,socket_length_mm=3.5)
                a=top-e*1.5
                if tail is None:
                    rr=accept(np.array([a,goal]),'Circular stem enters a complete angled socket on a fully seated flat flange.',f)
                    if rr:return rr,fails
                    if r.get('internal_waypoint'):
                        for sc in (4.,8.,14.):
                            rr=accept(curve(a,e,goal,tail_e,sc),'Circular stem enters a seated angled socket with a continuous tangent at the interior waypoint.',f)
                            if rr:return rr,fails
                else:
                    for sc in (4.,8.,14.):
                        pts=np.vstack([curve(a,e,goal,tail_e,sc),tail[1:]])
                        rr=accept(pts,'Circular stem with seated flat flange and an angled socket; constrained continuous route.',f)
                        if rr:return rr,fails
    for shift in (0.,6.,-6.,10.,-10.):
      for f0 in sockets:
        for depth in (4.,6.,8.,11.):
            f=dict(f0,depth_mm=depth);base=np.array(f['base_world_mm']);d=np.array(f['normal_world']);u=np.array(f['u_world']);v=np.cross(d,u)
            offset=v*shift;f['top_offset_world_mm']=offset;a=base+d*(depth-2.)+offset
            pad=socket_solid(f)
            if (pad^wires).volume()>.01:continue
            ok,why=space.clear(pad)
            if ok and ospace:ok,why=ospace.clear(move(pad,reflection))
            if not ok:fails['foot '+why['part']]=fails.get('foot '+why['part'],0)+1;continue
            for b in endopts:
                rr=accept(np.array([a,b]),'Straight circular stem with a fully seated broad, flat mounting foot.',f)
                if rr:return rr,fails
            for b,e,tail in goals:
                if np.dot(b-a,d)<-2:continue
                for scale in (4.,8.,14.):
                    pts=curve(a,d,b,e,scale)
                    if tail is not None:pts=np.vstack([pts,tail[1:]])
                    rr=accept(pts,'Circular stem seated in a broad flat rectangular mounting foot; full native base contact.',f)
                    if rr:return rr,fails
    return None,dict(fails,seated_starts=len(valid),sources=len(points),seated_sockets=len(sockets))

def main(key,other=None,indices=None):
    parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);M=N[parts[key]['token']];R=np.diag([1.,-1.,1.,1.])
    report=copy.deepcopy(connection_records(key));hosts=native_hosts(key,parts,p,N);space=Space(key,parts,p,N,False)
    wires=move(wire_spaces(key),M);ospace=None;owires=None;matching={};oreport=None
    if other:
        OM=N[parts[other]['token']];ohosts=native_hosts(other,parts,p,N);ospace=space if other==key else Space(other,parts,p,N,False);owires=move(wire_spaces(other),OM)
        cost=np.array([[np.linalg.norm(np.mean(np.array(a.bounding_box()).reshape(2,3),axis=0)-np.mean(np.array(move(b,R).bounding_box()).reshape(2,3),axis=0))for b in ohosts]for a in hosts])
        ii,jj=linear_sum_assignment(cost);matching=dict(zip(map(int,ii),map(int,jj)));oreport=report if other==key else copy.deepcopy(connection_records(other))
    for i,r in enumerate(report['rods']):
        if indices and i not in indices:continue
        source=hosts[r['mount']];target=hosts[r['target_mount']] if 'target_mount' in r else wall_pad(r)
        common=source^move(ohosts[matching[r['mount']]],R) if other else source
        if other and 'target_mount' in r:target=target^move(ohosts[matching[r['target_mount']]],R)
        result,fails=search(r,source,target,space,wires,other,ospace,owires,common)
        if result is None:
            put(HROOT/(key.replace('/','__')+f'_rod{i}_failed.json'),dict(key=key,rod=i,failures=fails));print('NO ROUTE',key,i,fails,flush=True);continue
        report['rods'][i]=result
        if other:
            j=min(range(len(oreport['rods'])),key=lambda j:np.linalg.norm(np.array(oreport['rods'][j]['centerline_world_mm'])[0]-np.array(r['centerline_world_mm'])[0]*[1,-1,1]))
            q=copy.deepcopy(result);q.update(mount=matching[r['mount']],mirrored_from=key)
            q['centerline_world_mm']=np.array(q['centerline_world_mm'])*[1,-1,1]
            q['wall_landing_world_mm']=np.array(q['wall_landing_world_mm'])*[1,-1,1]
            if 'wall_foot_reference_endpoint_world_mm' in q:q['wall_foot_reference_endpoint_world_mm']=np.array(q['wall_foot_reference_endpoint_world_mm'])*[1,-1,1]
            if 'source_socket' in q:
                f=q['source_socket'];f['base_world_mm']=np.array(f['base_world_mm'])*[1,-1,1];f['normal_world']=np.array(f['normal_world'])*[1,-1,1];f['u_world']=np.array(f['u_world'])*[1,-1,1]
                if 'top_offset_world_mm' in f:f['top_offset_world_mm']=np.array(f['top_offset_world_mm'])*[1,-1,1]
                if 'top_normal_world' in f:f['top_normal_world']=np.array(f['top_normal_world'])*[1,-1,1]
            if 'target_mount' in q:q['target_mount']=matching[r['target_mount']]
            oreport['rods'][j]=q
        for k,rr in [(key,report)]+([(other,oreport)] if other and other!=key else []):
            material=preserved_material(k,parts,p,N)+structural_connectors(rr['rods'])
            inv=np.linalg.inv(N[parts[k]['token']]);s=move(material,inv);path=HROOT/(k.replace('/','__')+'.npz')
            save_s(path,s);rr.update(revision=HREV,candidate_sha256=sha(path),source_geometry_sha256=GHASH,components=len(s.decompose()))
            put(path.with_suffix('.json'),rr);parts[k]['s']=s
        print('REPAIRED',key,i,'start',result['centerline_world_mm'][0],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('--mirror');ap.add_argument('--indices',type=int,nargs='*');a=ap.parse_args();main(a.key,a.mirror,a.indices)
