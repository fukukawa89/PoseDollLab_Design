"""O23G: full-section connections and broad, fully seated shell landings."""
from revo23_clean import *
from build_revo23_clean_connections import source_keep
from present_revo23 import load_current
from scipy.ndimage import distance_transform_edt
from audit_revo23_load_paths import raster
import time

FHASH='47c788b92b3b43d5d2cc2d55be1483198d99cd313e275613233daa0848e6a752'
FHISTORY=B/'history/O23F_before_smooth_connections_20261021'
GROOT=B/'design/smooth_candidate'
GREV='O23G-smooth-seated-connections-20261021'

def archive_f():
    if (FHISTORY/'snapshot.json').exists():
        assert sha(FHISTORY/'assembly.npz')==FHASH
        return
    assert sha(B/'assembly.npz')==FHASH
    names=['assembly.npz','assembly.json','retained_interfaces.npz','DELIVERY.json',
           'DESIGN.zh-CN.md','CLEAN_SYMMETRIC_WALLS.zh-CN.md','CONTINUOUS_WALLS.zh-CN.md','FINGERS_STRUCTURE_HARNESS.zh-CN.md']
    for directory in ('profiles','verification','images','harness','preview'):
        names += [x.relative_to(B).as_posix() for x in (B/directory).rglob('*') if x.is_file()]
    for rel in names:
        src=B/rel;dst=FHISTORY/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    shutil.copy2(CFG,FHISTORY/'parameters.json')
    put(FHISTORY/'snapshot.json',dict(geometry_sha256=FHASH,reason='User requested whole-body smooth connectors, fully supported landings and visible bilateral symmetry.',files={rel:sha(FHISTORY/rel) for rel in names}))
    GROOT.mkdir(parents=True,exist_ok=True)

def load_g():
    archive_f();z=np.load(FHISTORY/'assembly.npz');parts={}
    for item in read(FHISTORY/'assembly.json')['items']:
        k=str(item['index']);path=GROOT/(item['key'].replace('/','__')+'.npz')
        if path.exists():
            n=np.load(path);s=solid(n['v'],n['f'])
        else:s=solid(z[k+'v'],z[k+'f'])
        parts[item['key']]=dict(item,s=s)
    return parts,read(FHISTORY/'profiles/device_profile.json'),read(FHISTORY/'parameters.json')

def cyl(a,b,r,rb=None):
    a=np.asarray(a);b=np.asarray(b);d=b-a;length=np.linalg.norm(d)
    z=d/length;x=np.cross(np.eye(3)[np.argmin(abs(z))],z);x/=np.linalg.norm(x)
    return md.Manifold.cylinder(length,r,r if rb is None else rb,48).transform(np.c_[x,np.cross(z,x),z,a])

def tapered(a,b,r0,r1):
    """Smooth monotone radius; flat buried ends, no spheres or clipped sides."""
    a=np.asarray(a);b=np.asarray(b);z=b-a;z/=np.linalg.norm(z)
    x=np.cross(np.eye(3)[np.argmin(abs(z))],z);x/=np.linalg.norm(x);y=np.cross(z,x)
    t=np.linspace(0,1,13);angle=np.linspace(0,2*np.pi,48,endpoint=False)
    radii=r0+(r1-r0)*(t*t*(3-2*t));v=[];f=[]
    for u,r in zip(t,radii):v.extend(a+(b-a)*u+r*(np.cos(angle)[:,None]*x+np.sin(angle)[:,None]*y))
    for k in range(len(t)-1):
        for i in range(48):
            j=(i+1)%48;a0=k*48+i;b0=k*48+j;c=(k+1)*48+i;d=(k+1)*48+j
            f.extend([[a0,b0,c],[b0,d,c]])
    v.extend([a,b]);end=(len(t)-1)*48
    for i in range(48):j=(i+1)%48;f.extend([[len(v)-2,j,i],[len(v)-1,end+i,end+j]])
    return solid(v,f)

def round_sweep(points,r):
    """Circular sections transported along a smooth centreline, without ball unions."""
    points=np.asarray(points);tangent=np.gradient(points,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    angle=np.linspace(0,2*np.pi,48,endpoint=False);v=[];f=[];x=None
    for point,z in zip(points,tangent):
        if x is None:x=np.cross(np.eye(3)[np.argmin(abs(z))],z)
        x=x-z*np.dot(x,z);x/=np.linalg.norm(x);y=np.cross(z,x)
        v.extend(point+r*(np.cos(angle)[:,None]*x+np.sin(angle)[:,None]*y))
    for k in range(len(points)-1):
        for i in range(48):
            j=(i+1)%48;a=k*48+i;b=k*48+j;c=(k+1)*48+i;d=(k+1)*48+j
            f.extend([[a,b,c],[b,d,c]])
    v.extend([points[0],points[-1]]);end=(len(points)-1)*48
    for i in range(48):j=(i+1)%48;f.extend([[len(v)-2,j,i],[len(v)-1,end+i,end+j]])
    return solid(v,f)

def positive_round_sweep(points,r):
    """Union positive ring-to-ring cells; close turns cannot create negative lobes."""
    points=np.asarray(points);tangent=np.gradient(points,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    angle=np.linspace(0,2*np.pi,48,endpoint=False);rings=[];x=None
    for point,z in zip(points,tangent):
        if x is None:x=np.cross(np.eye(3)[np.argmin(abs(z))],z)
        x=x-z*np.dot(x,z);x/=np.linalg.norm(x);y=np.cross(z,x)
        rings.append(point+r*(np.cos(angle)[:,None]*x+np.sin(angle)[:,None]*y))
    # Adjacent cells must overlap in VOLUME. Two-ring cells merely meet at a
    # cap and can leave microscopic disconnected membranes in a Boolean union.
    # Three-ring cells share a complete interval, without introducing balls.
    if len(rings)==2:return md.Manifold.hull_points(np.vstack(rings))
    return union([md.Manifold.hull_points(np.vstack(rings[i:i+3])) for i in range(len(rings)-2)])

def raw_keep(key,parts,p,N):
    path=GROOT/(key.replace('/','__')+'_native_keep.npz')
    if path.exists() and not key.startswith('frame/clavicle_'):
        z=np.load(path);s=solid(z['v'],z['f'])
        return union([c for c in s.decompose() if c.volume()>=150.])
    kz=np.load(EHISTORY/'source/retained_interfaces.npz')
    s=source_keep(key,kz,parts[key],p,N)
    # Sub-mm3 disconnected slivers are Boolean leftovers, not mounting lands.
    # Their removal is separately recorded in the G interface audit.
    return union([c for c in s.decompose() if c.volume()>=1.])

def skin_of(key):
    z=np.load(FROOT/(key.replace('/','__')+'_skin.npz'));return solid(z['v'],z['f'])

class Space:
    """All actual neighbouring solids in every declared pose, in neutral world coordinates."""
    def __init__(self,key,parts,p,N,replace_neighbour_structures=True):
        self.key=key;self.parts=parts;self.p=p;self.N=N;self.calls=0;self.tests=0
        item=parts[key];self.M=N[item['token']]
        target=move(item['s'],self.M);bb=np.array(target.bounding_box());bb[:3]-=20;bb[3:]+=20
        corners={};models={};families={}
        for k,o in parts.items():
            if k==key or not adjacent(item,o,p):continue
            s=o['s']
            if o['role']=='structure' and replace_neighbour_structures:
                s=raw_keep(k,parts,p,N)+skin_of(k)
            models[k]=s;bounds=np.array(s.bounding_box())
            corners[k]=np.array(list(itertools.product(*zip(bounds[:3],bounds[3:]))))
            families.setdefault(o['token'],[]).append(k)
        poses=read(FHISTORY/'profiles/daily_poses.json')['poses']
        poses.update(read(FHISTORY/'profiles/edge_path_poses.json')['poses'])
        seen=set();records=[];bounds=[]
        for label,q in poses.items():
            ff=frames(p,q);left=self.M@np.linalg.inv(ff[item['token']])
            for token,keys in families.items():
                T=left@ff[token];sig=(token,tuple(np.round(T,6).ravel()))
                if sig in seen:continue
                seen.add(sig)
                for k in keys:
                    v=corners[k]@T[:3,:3].T+T[:3,3];ob=np.r_[v.min(0),v.max(0)]
                    if np.any(np.minimum(bb[3:],ob[3:])-np.maximum(bb[:3],ob[:3])<=0):continue
                    records.append(dict(key=k,pose=label,transform=T,source=models[k],solid=None))
                    bounds.append(ob)
        self.records=records;self.bounds=np.array(bounds);self.bad=[]
        print('SPACE',key,'states',len(records),flush=True)

    def clear(self,s,tolerance=.02):
        if s.is_empty():return True,None
        self.calls+=1;bb=np.array(s.bounding_box());ids=np.flatnonzero(np.all(np.minimum(bb[3:],self.bounds[:,3:])-np.maximum(bb[:3],self.bounds[:,:3])>1e-6,axis=1))
        candidates=set(ids);order=[i for i in self.bad if i in candidates];order.extend(i for i in ids if i not in set(order))
        for i in order:
            row=self.records[i]
            if row['solid'] is None:row['solid']=move(row['source'],row['transform'])
            self.tests+=1;vol=max(0.,(s^row['solid']).volume())
            if vol>tolerance:
                if i not in self.bad:self.bad.append(i)
                return False,dict(part=row['key'],pose=row['pose'],overlap_mm3=vol)
        return True,None

def source_points(land,pitch=1.5,limit=50):
    bb=np.array(land.bounding_box());origin=np.floor((bb[:3]-pitch)/pitch)*pitch
    shape=tuple((np.ceil((bb[3:]+pitch-origin)/pitch).astype(int)+1).tolist())
    mask=raster(land,origin,shape,pitch);dist=distance_transform_edt(mask)*pitch
    ij=np.argwhere(mask);points=ij*pitch+origin
    if not len(points):return points
    # Include the outward attachment ears. A depth-only ranking misses those
    # ears and incorrectly starts every strut beside a neighbouring rotor.
    selected=list(dict.fromkeys(np.r_[np.argmax(dist[tuple(ij.T)]),np.argmax(points,axis=0),np.argmin(points,axis=0)].tolist()))
    distance=np.min(np.linalg.norm(points[:,None]-points[selected],axis=2),axis=1)
    while len(selected)<min(limit,len(points)):
        i=int(np.argmax(distance))
        if distance[i]<1.8:break
        selected.append(i);distance=np.minimum(distance,np.linalg.norm(points-points[i],axis=1))
    return points[selected]

def skin_landings(key,parts,p,cfg,N,skin,r=4.0):
    """Round pads wholly seated in existing wall, with a buried stem endpoint."""
    item=parts[key];M=N[item['token']];s=move(skin,M);mesh=trimesh.Trimesh(*vf(s),process=False)
    geom=canonical(item['body'],M,cfg)
    if geom is None:return []
    rows,A=geom[2:];center=A[:3,3];tri=mesh.vertices[mesh.faces];c=tri.mean(1);norm=mesh.face_normals
    radial=c-center
    if not item['body'].startswith('ball_'):
        axis=A[:3,2];radial-=np.outer(radial@axis,axis)
    score=np.sum(radial*norm,axis=1)
    valid=np.flatnonzero((score>5)&(mesh.area_faces>.05))
    points=c[valid];chosen=list(dict.fromkeys(np.r_[np.argmin(points,axis=0),np.argmax(points,axis=0)].tolist()))
    dist=np.min(np.linalg.norm(points[:,None]-points[chosen],axis=2),axis=1)
    while len(chosen)<min(600,len(points)):
        ix=int(np.argmax(dist))
        if dist[ix]<3:break
        chosen.append(ix);dist=np.minimum(dist,np.linalg.norm(points-points[ix],axis=1))
    order=valid[chosen]
    choices=[];used=[]
    outer=move(geom[1],np.linalg.inv(M)@A);outer=move(outer,M)
    for ix in order:
        if score[ix]<5 or mesh.area_faces[ix]<.05:continue
        pos=c[ix];normal=norm[ix]
        if any(np.linalg.norm(pos-u)<3 for u in used):continue
        used.append(pos)
        # Flat-ended backing pad sits inside the anatomical wall. All its
        # outer bonding disk must remain embedded away from opening edges.
        radius=r+2.5
        tip=1.3 if item['body'].startswith('ball_') else 1.8
        bond=cyl(pos-normal*(tip+.2),pos-normal*tip,radius)
        fraction=(bond^s).volume()/bond.volume()
        if fraction<.96:continue
        depth=7.0 if item['body'].startswith(('forearm_','elbow_','ball_')) else 13.0
        pad=tapered(pos-normal*depth,pos-normal*tip,r+.8,radius)
        if (pad-outer).volume()>.02:continue
        choices.append(dict(point=pos-normal*((depth+tip)/2),normal=normal,pad=pad,bond_fraction=fraction,outer_point=pos))
        if len(choices)>=200:break
    print('LANDINGS',key,len(choices),flush=True)
    return choices
