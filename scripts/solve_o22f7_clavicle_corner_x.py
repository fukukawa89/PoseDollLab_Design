"""Local constrained rigid motion near the narrow passage; no manufacturing edits."""
from o22f7_animation import *
from build_revo22_assembly import b
from scipy.optimize import minimize
from types import SimpleNamespace
class FeasibleStep(Exception):
 def __init__(self,x):self.x=x.copy()
import numpy as np,time
x=Build();x.begin(x.g['steps'][3]);key='frame/'+x.st['child'];inv=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inv@x.mats[k])
moving=shape(key);fixed=[shape(k) for k in ['frame/chest',x.st['id']+'/M3_nut',x.st['id']+'/M3_reaction_washer',x.st['id']+'/inner_M4_wide']];bounds=[np.array(f.bounding_box()) for f in fixed];calls=0;cache={};tic=time.time()

def volume(q):
 global calls
 key=tuple(q)
 if key in cache:return cache[key]
 calls+=1;M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];s=b.g.move(moving,M);bb=np.array(s.bounding_box());vol=0
 for f,bo in zip(fixed,bounds):
  if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
  vol=max(vol,float((s^f).volume()))
 cache[key]=vol;return vol

def edge(p,q,step=.4):
 n=max(1,int(np.ceil(np.linalg.norm((q-p)*[1,1,1,1.7,1.7,1.7])/step)))
 return all(volume(p+(q-p)*(i/n))<=.02 for i in range(1,n+1))

path=read(WORK/'clavicle_corner_resume_progress.json')['best_path'];p=np.array(path[-1],float);found=False;scale=np.array([1,1,1,3,3,3],float)
for n in range(90):
 def cost(v):return -v[0]+.004*np.dot(v,v)
 constraint={'type':'ineq','fun':lambda v:.012-max(volume(p+v*scale*f) for f in [.05,.1,.25,.5,.75,1])}
 def callback(v):
  if v[0]>.999 and max(volume(p+v*scale*f) for f in [.05,.1,.25,.5,.75,1])<=.014:raise FeasibleStep(v)
 try:result=minimize(cost,np.zeros(6),method='SLSQP',bounds=[(0,1.),(-2,2),(-2,2),(-2,2),(-2,2),(-2,2)],constraints=constraint,callback=callback,options={'maxiter':70,'ftol':1e-7,'eps':.002})
 except FeasibleStep as f:result=SimpleNamespace(x=f.x,success=True)

 q=p+result.x*scale;vol=volume(q)
 print('opt',n,'pose',arr(q),'x gain',round(q[0]-p[0],4),'vol',round(vol,5),'success',result.success,'calls',calls,'seconds',round(time.time()-tic),flush=True)
 accepted=None
 for f in [1,.8,.6,.4,.2,.1]:
  trial=p+(q-p)*f
  if trial[0]-p[0]>.005 and volume(trial)<=.02 and edge(p,trial):accepted=trial;break
 if accepted is None:break
 q=accepted
 path.append(q.tolist());p=q;put(WORK/'clavicle_corner_x_progress.json',{'best_path':path,'calls':calls,'seconds':time.time()-tic})
 for axis in [2,0,1]:
  for sign in [-1,1]:
   end=p.copy();end[axis]+=sign*160
   if all(volume(p+(end-p)*t)<=.02 for t in np.linspace(0,1,81)) and edge(p,end,.5):path.append(end.tolist());found=True;break
  if found:break
 if found:break
 if time.time()-tic>600:break
if found:put(WORK/'clavicle_corner_x_path.json',{'path':path,'part':key,'passed_sampled_search':True});print('FOUND',len(path),calls,flush=True)
else:print('NO PATH',calls,flush=True)


