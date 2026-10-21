"""A small explicit set of broad connections, contained in verified E space.

The E mesh is a collision-free permission envelope, not a retained web.
Each recorded centreline is one nonbranching rod. No hidden lattice is added.
"""
from revo23_clean import *
from audit_revo23_load_paths import raster,grid_graph
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
import time
_grid_cache={}


def safe_route(envelope,source,target,pitch=1.2):
    sig=(id(envelope),pitch)
    if sig not in _grid_cache:
        bounds=np.array(envelope.bounding_box())
        origin=np.floor((bounds[:3]-3)/pitch)*pitch
        shape=tuple((np.ceil((bounds[3:]+3-origin)/pitch).astype(int)+1).tolist())
        mask=raster(envelope,origin,shape,pitch)
        coords,ids,a,b=grid_graph(mask)
        clearance=distance_transform_edt(mask)*pitch
        c=clearance[mask]
        weights=pitch*(1+15/np.maximum(1.,np.minimum(c[a],c[b]))**2)
        graph=coo_matrix((np.r_[weights,weights],(np.r_[a,b],np.r_[b,a])),
                         shape=(len(coords),len(coords))).tocsr()
        _grid_cache[sig]=(origin,shape,mask,coords,ids,clearance,graph)
    origin,shape,mask,coords,ids,clearance,graph=_grid_cache[sig]
    src=raster(source,origin,shape,pitch)&mask
    targets=target if isinstance(target,list) else [target]
    dst=np.zeros(shape,dtype=bool)
    for t in targets:dst|=raster(t,origin,shape,pitch)
    dst &= mask
    if not src.any() or not dst.any():return None
    # Start inside a mounting land, not at the nearest thin edge of a bore.
    core=distance_transform_edt(src)*pitch
    src &= core>=min(3.0,float(core.max())*.7)
    target_core=distance_transform_edt(dst)*pitch
    dst &= target_core>=min(3.0,float(target_core.max())*.7)
    dist,pred=dijkstra(graph,indices=ids[dst],return_predecessors=True,min_only=True)[:2]
    candidates=ids[src]
    chosen=int(candidates[np.argmin(dist[candidates])])
    if not np.isfinite(dist[chosen]):return None
    path=[];cur=chosen
    while cur>=0:
        path.append(coords[cur]*pitch+origin);cur=int(pred[cur])
    path=np.array(path)
    if len(path)<2:return path
    # Shortcut grid stair steps, preserving the route's available clearance.
    def minimum(a,b):
        q=np.linspace(a,b,max(3,int(np.linalg.norm(a-b)/.6)+1))
        ij=np.round((q-origin)/pitch).astype(int)
        ij=np.clip(ij,0,np.array(shape)-1)
        return float(clearance[tuple(ij.T)].min())
    chosen=[path[0]];i=0
    while i<len(path)-1:
        best=i+1
        for j in range(len(path)-1,i,-1):
            floor=min(3.8,minimum(path[i],path[i]),minimum(path[j],path[j]))
            if minimum(path[i],path[j])>=max(1.1,floor-.4):
                best=j;break
        chosen.append(path[best]);i=best
    return np.array(chosen)


def route_shape(points,radius=5.0):
    if len(points)<2:return ball(points[0],radius)
    return union([capsule(a,b,radius) for a,b in zip(points,points[1:])])


def source_keep(key,kz,item,p,N):
    keep=solid(kz[key+'|v'],kz[key+'|f'])
    extras=[]
    if key=='frame/chest':
        # The compact backpack moved up with the D torso. Use its actual four
        # screw positions, not the pre-raise C coordinates.
        heads=np.array(read(B/'design/compact_revision.json')['mount_heads_world_mm'])
        for side in (-1,1):
            selected=heads[heads[:,1]*side>0]
            center=selected.mean(0)
            w=box([center[0]-3.8,center[1]-8,selected[:,2].min()-8],
                  [center[0]+14.2,center[1]+8,selected[:,2].max()+8])
            land=item['s']^move(w,np.linalg.inv(N[item['token']]))
            pieces=[c for c in land.decompose() if c.volume()>100]
            assert len(pieces)==1,('Backpack rail must be continuous',side)
            extras.append(pieces[0])
        keep=union([keep]+extras)
    return keep


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*')
    ap.add_argument('--radius',type=float,default=5.0);ap.add_argument('--skip-existing',action='store_true')
    args=ap.parse_args()
    parts,p,cfg=load_e_snapshot();N=frames(p,p['neutral_raw_deg'])
    kz=np.load(EHISTORY/'source/retained_interfaces.npz')
    for key,item in parts.items():
        if item['role']!='structure' or args.keys and key not in args.keys:continue
        path=FROOT/(key.replace('/','__')+'.npz')
        if args.skip_existing and path.exists():continue
        started=time.time()
        _grid_cache.clear()
        z=np.load(path.with_name(path.stem+'_skin.npz'));skin=solid(z['v'],z['f'])
        keep=source_keep(key,kz,item,p,N)
        # Saved E is the motion-tested permitted volume for internal rods only.
        envelope=solid(*vf(item['s']+skin))
        candidate=solid(*vf(keep+skin));rods=[];keep_parts=[]
        for i,c in enumerate(sorted(keep.decompose(),key=lambda x:-x.volume())):
            if c.volume()>.05:keep_parts.append((i,c))
        if skin.is_empty():
            root=max(keep_parts,key=lambda t:t[1].volume())[1]
        else:root=skin
        network=[root];beams=[]
        # Every mount uses at most one routed rod in this initial design.
        for li,land in keep_parts:
            if land is root or any((land^t).volume()>5 for t in network):
                if land is not root:network.append(land)
                continue
            points=safe_route(envelope,land,network)
            if points is None:points=safe_route(envelope,land,network,pitch=.6)
            if points is None:
                raise RuntimeError(('No broad route in verified envelope',key,li))
            actual_radius=args.radius
            beam=solid(*vf(route_shape(points,actual_radius)^envelope))
            # Keep only the continuous branch touching both endpoints.
            cc=[c for c in beam.decompose() if (c^land).volume()>.2 and any((c^t).volume()>.2 for t in network)]
            if not cc:
                actual_radius+=2
                beam=solid(*vf(route_shape(points,actual_radius)^envelope))
                cc=[c for c in beam.decompose() if (c^land).volume()>.2 and any((c^t).volume()>.2 for t in network)]
            if not cc:raise RuntimeError(('Clipped beam did not bridge its endpoints',key,li,points.tolist()))
            beam=max(cc,key=lambda s:s.volume())
            beam=solid(*vf(beam))
            target_overlap=sum(max(0.,(beam^t).volume()) for t in network)
            rods.append(dict(id=f'{key}/mount_{li}/rod_1',mount=li,rod_count=1,
                             radius_mm=actual_radius,centerline_body_mm=points,
                             clipped_volume_mm3=beam.volume(),
                             land_overlap_mm3=(beam^land).volume(),
                             target_overlap_mm3=target_overlap))
            print('ROD',key,li,'nodes',len(points),'length',round(np.linalg.norm(np.diff(points,axis=0),axis=1).sum(),1),
                  'overlap',round((beam^land).volume(),1),round(target_overlap,1),flush=True)
            beams.append(beam);network.extend([land,beam])
        candidate=solid(*vf(union([keep,skin]+beams)))
        # Tiny retained interface artifacts are included, and must fuse too.
        cc=sorted(candidate.decompose(),key=lambda s:-s.volume())
        for fragment in cc[1:]:
            if fragment.volume()<.05:continue
            if (fragment^keep).volume()<.05:continue
            target=cc[0]
            points=safe_route(envelope,fragment,target)
            if points is None:raise RuntimeError(('Residual interface disconnected',key,fragment.volume()))
            beam=route_shape(points,args.radius)^envelope
            candidate=solid(*vf(candidate+beam))
            li=min(keep_parts,key=lambda pair:-max(0.,(pair[1]^fragment).volume()))[0]
            count=sum(r['mount']==li for r in rods)
            assert count<3,(key,li,'three rod limit')
            rods.append(dict(id=f'{key}/mount_{li}/rod_{count+1}',mount=li,rod_count=1,
                             radius_mm=args.radius,centerline_body_mm=points,
                             clipped_volume_mm3=beam.volume()))
        cc=candidate.decompose()
        debris=[c for c in cc if c.volume()<.01]
        debris_volume=sum(max(0,c.volume()) for c in debris)
        assert debris_volume<.02,(key,'unexpected detached material',debris_volume)
        candidate=union([c for c in cc if c not in debris])
        candidate=save_s(path,candidate)
        m=trimesh.Trimesh(*vf(candidate),process=False)
        report=dict(key=key,source_geometry_sha256=EHASH,candidate_sha256=sha(path),
                    rods=rods,components=len([c for c in candidate.decompose() if c.volume()>1e-4]),
                    retained_interface_loss_mm3=max(0.,(keep-candidate).volume()),
                    indexed_watertight=bool(m.is_watertight),
                    discarded_boolean_debris_mm3=debris_volume,
                    volume_mm3=candidate.volume(),old_volume_mm3=item['s'].volume(),
                    seconds=time.time()-started)
        put(path.with_suffix('.json'),report)
        print('BUILT',key,'rods',len(rods),'components',report['components'],
              'mass ratio',round(candidate.volume()/item['s'].volume(),2),flush=True)


if __name__=='__main__':
    main()
