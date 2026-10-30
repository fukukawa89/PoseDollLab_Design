"""Comparative elastic screening, not a physical strength certification.
Voxel H8 solids, 2x2x2 Gauss integration, homogeneous E=1500 MPa, nu=.35.
Two opposed 1 N loads represent printed-fork side loading, NOT A8 preload.
"""
from build_stock import *
from matplotlib.path import Path as Poly
from scipy import sparse
from scipy.sparse.linalg import cg,LinearOperator
import time

def get(root,name):
 a=load(root/'production_assembly.json')['parts'];z=np.load(root/'production_meshes.npz');p=next(p for p in a if p['name']==name);i=str(p['i'])
 return md.Manifold(md.Mesh64(np.array(z[i+'v'],copy=True),np.array(z[i+'f'],dtype=np.uint64,copy=True))),p

def stiffness(h):
 E=1500.;nu=.35;la=E*nu/((1+nu)*(1-2*nu));mu=E/(2*(1+nu));D=np.zeros((6,6));D[:3,:3]=la
 for i in range(3):D[i,i]+=2*mu
 for i in range(3,6):D[i,i]=mu
 offs=np.array([[x,y,z] for z in [0,1] for y in [0,1] for x in [0,1]]);sign=2*offs-1;K=np.zeros((24,24))
 for xx in [-1/np.sqrt(3),1/np.sqrt(3)]:
  for yy in [-1/np.sqrt(3),1/np.sqrt(3)]:
   for zz in [-1/np.sqrt(3),1/np.sqrt(3)]:
    g=np.array([xx,yy,zz]);d=np.zeros((8,3))
    for j in range(3):d[:,j]=sign[:,j]*np.prod(1+sign[:,[k for k in range(3) if k!=j]]*g[[k for k in range(3) if k!=j]],axis=1)/(4*h)
    B=np.zeros((6,24))
    for a,(dx,dy,dz) in enumerate(d):
     B[0,3*a]=dx;B[1,3*a+1]=dy;B[2,3*a+2]=dz;B[3,3*a]=dy;B[3,3*a+1]=dx;B[4,3*a+1]=dz;B[4,3*a+2]=dy;B[5,3*a]=dz;B[5,3*a+2]=dx
    K+=B.T@D@B*(h/2)**3
 return K,offs

def solve(s,h):
 start=time.time();lo,hi=e.bounds(s);lo=np.floor(lo/h)*h-h;shape=np.ceil((hi-lo)/h).astype(int)+1
 xs=lo[0]+(np.arange(shape[0])+.5)*h;ys=lo[1]+(np.arange(shape[1])+.5)*h;xx,yy=np.meshgrid(xs,ys,indexing='ij');grid=np.c_[xx.ravel(),yy.ravel()];vox=np.zeros(shape,bool)
 for iz,z in enumerate(lo[2]+(np.arange(shape[2])+.5)*h):
  inside=np.zeros(len(grid),bool)
  for poly in s.slice(float(z)).to_polygons():inside^=Poly(poly).contains_points(grid)
  vox[:,:,iz]=inside.reshape(shape[:2])
 cells=np.argwhere(vox);ke,offs=stiffness(h);raw=cells[:,None,:]+offs[None,:,:];ids=np.ravel_multi_index(raw.reshape(-1,3).T,shape+1);unique,ix=np.unique(ids,return_inverse=True);xyz=lo+np.array(np.unravel_index(unique,shape+1)).T*h;conn=ix.reshape(-1,8);dof=(conn[:,:,None]*3+np.arange(3)).reshape(-1,24);n=len(xyz)*3
 I=np.repeat(dof,24,axis=1).ravel();J=np.tile(dof,(1,24)).ravel();K=sparse.coo_matrix((np.tile(ke.ravel(),len(cells)),(I,J)),shape=(n,n)).tocsr();del I,J,raw,ids
 fixed=np.flatnonzero(xyz[:,2]>40.5);fixedD=(fixed[:,None]*3+np.arange(3)).ravel();free=np.setdiff1d(np.arange(n),fixedD);force=np.zeros(n);patches=[]
 for side in [-1,1]:
  p=np.flatnonzero((xyz[:,1]*side>8.4)&(xyz[:,1]*side<10.6)&(abs(xyz[:,0])<4.5)&(abs(xyz[:,2])<4.5));assert len(p)>0
  force[p*3+1]=-side/len(p);patches.append(p)
 A=K[free][:,free];b=force[free];M=LinearOperator(A.shape,matvec=lambda x:x/A.diagonal());u=np.zeros(n);count=[0]
 def cb(x):count[0]+=1
 u[free],info=cg(A,b,rtol=1e-8,atol=1e-11,maxiter=6000,M=M,callback=cb);assert info==0,info
 residual=K@u-force;disp=u.reshape(-1,3);closure=float(disp[patches[0],1].mean()-disp[patches[1],1].mean());result=dict(pitch_mm=h,elements=len(cells),nodes=len(xyz),closure_mm=closure,max_displacement_mm=float(np.linalg.norm(disp,axis=1).max()),compliance_N_mm=float(force@u),free_residual_N=float(np.linalg.norm(residual[free])),reaction_force_N=residual.reshape(-1,3)[fixed].sum(0).tolist(),iterations=count[0],seconds=time.time()-start)
 return result

def main():
 old=H/'bench/revO24E_LArm_Stock';roots=[('R1',old),('R2',OUT)];rows=[];M=F0['l_elbow_flex']@rot([0,0,1],180)
 for label,root in roots:
  s,p=get(root,'UPPER_ARM');s=moved(s,np.linalg.inv(M)@F0[p['frame']]);res=[]
  for h in [1.2,.9,.6]:
   r=solve(s,h);res.append(r);print(label,r,flush=True)
  bridge=(s^box([-8,-.1,-8],[8,.1,8])).volume()/.2
  sections=[]
  for z in np.linspace(12,38,53):sections.append(dict(z_mm=float(z),area_mm2=s.slice(float(z)).area()))
  rows.append(dict(revision=label,source_sha256=sha(root/'production_meshes.npz'),near_joint_bridge_area_mm2=bridge,central_shaft_min_section_mm2=min(r['area_mm2'] for r in sections),solutions=res))
 ratio=rows[1]['solutions'][-1]['closure_mm']/rows[0]['solutions'][-1]['closure_mm']
 put(OUT/'verification/structure_comparison.json',dict(status='PASS_COMPARATIVE_SCREEN' if ratio<.7 else 'REVIEW_REQUIRED',geometry_sha256=sha(OUT/'production_meshes.npz'),assumptions=dict(E_MPa=1500,poisson=.35,load_N_each_side=1,clamp='H local z > 40.5 mm at RU rotor',load_patch='H y +/-8.4..10.6, abs(x,z)<4.5, two opposed inward forces',physical_tested=False),rows=rows,R2_over_R1_closure=ratio,scope='Comparative homogeneous linear elastic voxel H8 model of P007 only. Staircase geometry and omitted steel contacts. Equal printed-side-load boundary conditions in both versions. Mesh-dependent screening values, not converged stress results. Does not infer actual spring force, FDM anisotropy, creep, fatigue, strength or full-arm qualification. Other parts receive geometric section/core/interface review, not FEA.'))
if __name__=='__main__':main()
