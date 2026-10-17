"""Drive the whole frame beyond an exterior plane, rather than driving only its origin."""
from o22f7_animation import *
from build_revo22_assembly import b
from scipy.optimize import minimize
from scipy.spatial import ConvexHull
from types import SimpleNamespace
import time,itertools
class Feasible(Exception):
 def __init__(self,x):self.x=x.copy()
x=Build();x.begin(x.g['steps'][3]);key='frame/'+x.st['child'];inv=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inv@x.mats[k])
moving=shape(key);fixed=[shape(k) for k in ['frame/chest',x.st['id']+'/M3_nut',x.st['id']+'/M3_reaction_washer',x.st['id']+'/inner_M4_wide']];bounds=[np.array(s.bounding_box()) for s in fixed];vv=np.unique(b.g.tri(moving).reshape(-1,3),axis=0);vv=vv[ConvexHull(vv).vertices];d=unit([1,1,0]);calls=0;cache={};tic=time.time();scale=np.array([1,1,1,3,3,3])
def matrix(q):
 m=np.eye(4);m[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);m[:3,3]=q[:3];return m
def support(q):
 m=matrix(q);return float(((vv@m[:3,:3].T+m[:3,3])@d).min())
def volume(q):
 global calls
 k=tuple(q)
 if k in cache:return cache[k]
 calls+=1;s=b.g.move(moving,matrix(q));bb=np.array(s.bounding_box());peak=0
 for f,bo in zip(fixed,bounds):
  if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
  peak=max(peak,float((s^f).volume()))
 cache[k]=peak;return peak
def edge(p,q,step=.3):
 n=max(1,int(np.ceil(np.linalg.norm((q-p)*[1,1,1,2,2,2])/step)));return all(volume(p+(q-p)*t)<=.02 for t in np.arange(1,n+1)/n)
path=read(WORK/'clavicle_corner_zup_progress.json')['best_path'];p=np.array(path[-1]);found=False
for i in range(70):
 start=support(p)
 def collision(v):return max(volume(p+v*scale*t) for t in [.05,.1,.25,.5,.75,1.])
 def cost(v):return -support(p+v*scale)+.005*np.dot(v,v)
 def callback(v):
  if support(p+v*scale)-start>.9 and collision(v)<=.014:raise Feasible(v)
 try:res=minimize(cost,np.zeros(6),method='SLSQP',bounds=[(-2,2)]*6,constraints={'type':'ineq','fun':lambda v:.012-collision(v)},callback=callback,options={'maxiter':30,'ftol':1e-6,'eps':.003})
 except Feasible as f:res=SimpleNamespace(x=f.x,success=True)
 q=p+res.x*scale;accepted=None
 for frac in [1,.8,.6,.4,.2,.1]:
  trial=p+(q-p)*frac
  if support(trial)-start>.005 and volume(trial)<=.02 and edge(p,trial):accepted=trial;break
 print('plane',i,'gain',support(q)-start,'pose',arr(q),'seconds',round(time.time()-tic),'calls',calls,flush=True)
 if accepted is None:break
 p=accepted;path.append(p.tolist());put(WORK/'clavicle_plane_progress.json',{'best_path':path,'support':support(p),'calls':calls,'seconds':time.time()-tic})
 for direction in [d,*[np.eye(3)[j]*sg for j in range(3) for sg in [-1,1]]]:
  end=p.copy();end[:3]+=direction*220
  if all(volume(p+(end-p)*t)<=.02 for t in np.linspace(0,1,111)) and edge(p,end):path.append(end.tolist());found=True;break
 if found:break
 if time.time()-tic>600:break
if found:put(WORK/'clavicle_plane_path.json',{'path':path,'part':key,'passed_sampled_search':True,'calls':calls});print('FOUND',len(path),calls,flush=True)
else:print('NO EXIT',len(path),calls,flush=True)
