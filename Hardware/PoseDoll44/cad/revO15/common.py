"""O15 independent geometry helpers; immutable O14/older inputs."""
from pathlib import Path
import sys,json,hashlib,struct,itertools,math
import numpy as np
import manifold3d as md
H=Path(__file__).resolve().parents[2];R=H.parents[1];OUT=H/'generated/revO15/runs/o15_20260929_r1';BENCH=H/'bench/revO15'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,d):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def rot(axis,deg):
 a=np.eye(3)[axis] if isinstance(axis,int) else np.asarray(axis,float);a=a/np.linalg.norm(a);x,y,z=a;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);q=np.deg2rad(deg);return np.eye(3)+np.sin(q)*K+(1-np.cos(q))*(K@K)
def pose(s,M=np.eye(3),p=(0,0,0)):return s.transform(np.c_[M,p])
def tri(s):
 m=s.to_mesh64();return np.array(m.vert_properties)[:,:3][np.array(m.tri_verts)]
def from_tri(t):
 v,idx=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True);s=md.Manifold(md.Mesh64(np.ascontiguousarray(v),np.ascontiguousarray(idx.reshape(-1,3),dtype=np.uint64)))
 if s.status()!=md.Error.NoError:raise ValueError(s.status())
 return s
def cyl(r,z0,z1,n=96):return md.Manifold.cylinder(z1-z0,r,circular_segments=n).translate([0,0,z0])
def box(lo,hi):return md.Manifold.cube(np.asarray(hi)-lo).translate(lo)
def hexagon(af,z0,z1):
 a=np.arange(6)*np.pi/3;return md.CrossSection([np.c_[np.cos(a),np.sin(a)]*af/np.sqrt(3)]).extrude(z1-z0).translate([0,0,z0])
def washer(ro,ri,z0,t):return cyl(ro,z0,z0+t)-cyl(ri,z0-.1,z0+t+.1)
def screw(d,length,head_d,head_h,z0):return (cyl(d/2,z0-length,z0)+cyl(head_d/2,z0,z0+head_h))-hexagon(3 if d==4 else 2.5 if d==3 else 1.5,z0+head_h/2,z0+head_h+.1)
def nut(d,af,t,z0):return hexagon(af,z0,z0+t)-cyl(d/2+.05,z0-.1,z0+t+.1)
def beam(a,b,r):
 a=np.array(a);b=np.array(b);v=b-a;l=np.linalg.norm(v);z=v/l;seed=np.eye(3)[np.argmin(np.abs(z))];x=np.cross(seed,z);x/=np.linalg.norm(x);return pose(cyl(r,0,l,48),np.c_[x,np.cross(z,x),z],a)
def solid_count(s):
 # decompose() separates boundary shells; a negative-volume shell is a cavity,
 # not another disconnected lump of material. Retain every shell in exports.
 return sum(v.volume()>1e-7 for v in s.decompose())

def mesh_record(s):
 t=tri(s);v=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2]))/6;com=(v[:,None]*(t[:,0]+t[:,1]+t[:,2])/4).sum(0)/v.sum()
 return {'status':str(s.status()),'components':solid_count(s),'boundary_shells':len(s.decompose()),'enclosed_void_shells':sum(v.volume()<-1e-7 for v in s.decompose()),'volume_mm3':float(s.volume()),'COM_mm':com.tolist(),'bounds_mm':list(s.bounding_box())}
def hits(parts,allowed=(),eps=1e-4):
 out=[];bb={k:np.array(s.bounding_box()) for k,s in parts.items()};skip={frozenset(x) for x in allowed}
 for a,b in itertools.combinations(parts,2):
  if frozenset((a,b)) in skip:continue
  aa,ab=bb[a][:3],bb[a][3:];ba,bb_=bb[b][:3],bb[b][3:]
  if np.any(np.minimum(ab,bb_)<=np.maximum(aa,ba)+1e-8):continue
  v=float((parts[a]^parts[b]).volume())
  if v>eps:out.append({'pair':[a,b],'overlap_mm3':v})
 return out

def from_tri_exact(t):
 v,idx=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);s=md.Manifold(md.Mesh64(np.ascontiguousarray(v),np.ascontiguousarray(idx.reshape(-1,3),dtype=np.uint64)))
 if s.status()!=md.Error.NoError:raise ValueError(s.status())
 return s
