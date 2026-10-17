"""Try a coordinated loose fit: right follows a chest-clear path, left can move freely before tightening."""
from o22f7_animation import *
from build_revo22_assembly import b
from scipy.optimize import minimize
from types import SimpleNamespace
import time
class Feasible(Exception):
 def __init__(self,x):self.x=x.copy()
x=Build();x.begin(x.g['steps'][3]);lm=x.mount.copy();li=np.linalg.inv(lm);x.begin(x.g['steps'][10]);rm=x.mount.copy();ri=np.linalg.inv(rm)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),li@x.mats[k])
lbase=shape('frame/clavicle_l.protract_frame');rbase=shape('frame/clavicle_r.protract_frame');fixed=[shape(k) for k in ['frame/chest']+[mod+'/'+s for mod in ['clavicle_l.protract','clavicle_r.protract'] for s in ['M3_nut','M3_reaction_washer','inner_M4_wide']]];bounds=[np.array(s.bounding_box()) for s in fixed]
def M(q):
 r=np.eye(4);r[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);r[:3,3]=q[:3];return r
def right(q):
 s=b.g.move(rbase,li@rm@M(q)@ri@lm);return s,np.array(s.bounding_box())
def maxvol(q,r,bb):
 l=b.g.move(lbase,M(q));lb=np.array(l.bounding_box());v=0
 for f,bo in zip([*fixed,r],[*bounds,bb]):
  if np.any(np.minimum(lb[3:],bo[3:])<=np.maximum(lb[:3],bo[:3])+1e-6):continue
  v=max(v,float((l^f).volume()))
 return v
rpath=np.array(read(WORK/'clavicle_right_goal_0_1_path.json')['path']);path=[rpath[0]]
for p,q in zip(rpath,rpath[1:]):
 n=max(1,int(np.ceil(np.linalg.norm((q-p)*[1,1,1,2,2,2])/1.5)));path.extend(p+(q-p)*t for t in np.arange(1,n+1)/n)
lp=np.zeros(6);pairs=[{'left':lp.tolist(),'right':path[0].tolist()}];tic=time.time();scale=np.array([1,1,1,3,3,3]);calls=0;failure=None
for index,(rp,rq) in enumerate(zip(path,path[1:])):
 fractions=[.25,.5,.75,1.];rightsamples=[right(rp+(rq-rp)*t) for t in fractions];cache={}
 def collision(v):
  global calls
  k=tuple(v)
  if k in cache:return cache[k]
  calls+=1;result=max(maxvol(lp+v*scale*t,*r) for t,r in zip(fractions,rightsamples));cache[k]=result;return result
 delta=np.zeros(6)
 if collision(delta)>.02:
  def cost(v):return .02*np.dot(v,v)
  def callback(v):
   if collision(v)<=.012:raise Feasible(v)
  try:res=minimize(cost,delta,method='SLSQP',bounds=[(-4,4)]*3+[(-2,2)]*3,constraints={'type':'ineq','fun':lambda v:.01-collision(v)},callback=callback,options={'maxiter':35,'ftol':1e-6,'eps':.003})
  except Feasible as f:res=SimpleNamespace(x=f.x,success=True)
  delta=res.x
 lq=lp+delta*scale;peak=collision(delta)
 if peak>.02:failure={'step':index,'overlap_mm3':peak,'left':arr(lp),'right':arr(rq)};break
 n=max(1,int(np.ceil(max(np.linalg.norm((lq-lp)*[1,1,1,2,2,2]),np.linalg.norm((rq-rp)*[1,1,1,2,2,2]))/.3)))
 for t in np.arange(1,n+1)/n:
  peak=max(peak,maxvol(lp+(lq-lp)*t,*right(rp+(rq-rp)*t)))
 if peak>.02:failure={'step':index,'edge_overlap_mm3':peak};break
 lp=lq;pairs.append({'left':arr(lp),'right':arr(rq)});put(WORK/'clavicle_coordinated_optimized_progress.json',{'pairs':pairs,'right_samples':len(path),'calls':calls,'seconds':time.time()-tic})
 if index%15==0 or np.linalg.norm(delta)>.01:print('pair',index,'left',arr(lp),'calls',calls,'seconds',round(time.time()-tic),flush=True)
 if time.time()-tic>600:failure={'timeout':True,'step':index};break
if failure:put(WORK/'clavicle_coordinated_optimized_failure.json',failure);print('FAILED',failure,flush=True)
else:put(WORK/'clavicle_coordinated_optimized_path.json',{'pairs':pairs,'calls':calls,'seconds':time.time()-tic,'full_swept_volume_certified':False});print('FOUND COORDINATED',len(pairs),flush=True)
