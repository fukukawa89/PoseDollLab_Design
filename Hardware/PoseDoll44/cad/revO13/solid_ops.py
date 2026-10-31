"""O13 local solid operations; immutable O9 inputs, no O9 output writes.
Mesh coordinates are welded at 1e-5 mm before Boolean operations; this is
recorded and not equivalent to recovering analytic CAD from the source STL.
"""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
import manifold3d as md
H=Path(__file__).resolve().parents[2];R=H.parents[1]
G9=H/'generated/revO9/runs/o9_20260926_r1'
G8=H/'generated/revO8/runs/o8_20260925_r1'
OUT=H/'generated/revO13/runs/o13_20260929_r1'
OUT.mkdir(parents=True,exist_ok=True)
CORE=G9/'cup_relief_L3_R0p35/core_meshes.npz'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rot(axis,deg):
 a=np.eye(3)[axis] if isinstance(axis,int) else np.asarray(axis,float);a=a/np.linalg.norm(a);x,y,z=a;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);q=np.deg2rad(deg)
 return np.eye(3)+np.sin(q)*K+(1-np.cos(q))*(K@K)
def from_tri(t):
 v,inv=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True)
 m=md.Manifold(md.Mesh64(np.ascontiguousarray(v),np.ascontiguousarray(inv.reshape(-1,3),dtype=np.uint64)))
 if m.status()!=md.Error.NoError:raise ValueError(m.status())
 return m
def tri(s):
 m=s.to_mesh64();return np.array(m.vert_properties)[:,:3][np.array(m.tri_verts)]
def pose(s,M=np.eye(3),p=(0,0,0)):return s.transform(np.c_[M,p])
def cylinder(r,z0,z1):return md.Manifold.cylinder(z1-z0,r,circular_segments=144).translate([0,0,z0])
def box(low,high):return md.Manifold.cube(np.asarray(high)-low).translate(low)
def sector(r0,r1,a,b,z0,z1,step=.5):
 angles=np.deg2rad(np.linspace(a,b,int(np.ceil((b-a)/step))+1));outer=np.c_[r1*np.cos(angles),r1*np.sin(angles)];inner=np.c_[r0*np.cos(angles[::-1]),r0*np.sin(angles[::-1])]
 return md.CrossSection([np.r_[outer,inner]]).extrude(z1-z0).translate([0,0,z0])
def axis_frame(axis):
 # Positive determinant; local Z becomes joint X or Y; local XY is its radial plane.
 return np.array([[0,0,1],[1,0,0],[0,1,0]]) if axis==0 else np.array([[1,0,0],[0,0,1],[0,-1,0]]) if axis==1 else np.eye(3)
def along(s,axis):return pose(s,axis_frame(axis))
def export_stl(path,t):
 cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);nn=cr/np.maximum(np.linalg.norm(cr,axis=1,keepdims=True),1e-14)
 d=np.zeros(len(t),dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]));d['n']=nn;d['v']=t
 Path(path).write_bytes(b'PoseDoll O13 design study; mm; NOT manufacturing release'.ljust(80,b' ')+struct.pack('<I',len(t))+d.tobytes())
def record(s):
 return {'status':str(s.status()),'solid_components':len(s.decompose()),'volume_mm3':s.volume(),'bounds_mm':list(s.bounding_box()),'triangles':s.num_tri()}

