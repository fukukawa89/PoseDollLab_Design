"""Search rotations about contact points as well as translation; retain exact-mesh checks."""
from o22f7_animation import *
from build_revo22_assembly import b
from scipy.spatial.transform import Rotation
import warnings,time,numpy as np
warnings.filterwarnings('ignore',message='Gimbal lock detected')
x=Build();st=x.g['steps'][3];x.begin(st);key='frame/'+st['child'];inv=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inv@x.mats[k])
moving=shape(key);fixed=shape('frame/chest');stock=[shape(st['id']+'/'+k) for k in ['M3_nut','M3_reaction_washer','inner_M4_wide']];fbb=np.array(fixed.bounding_box());calls=0;tic=time.time();rng=np.random.default_rng(987);lastlog=0

def matrix(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return M

def unmatrix(M,ref):
 e=Rotation.from_matrix(M[:3,:3]).as_euler('XYZ',degrees=True);alt=np.array([e[0]+180,180-e[1],e[2]+180]);v=[]
 for a in [e,alt]:a+=360*np.round((np.array(ref[3:])-a)/360);v.append(a)
 e=min(v,key=lambda a:np.linalg.norm(a-ref[3:]));return np.r_[M[:3,3],e]

def collision(q,detail=False):
 global calls
 calls+=1;s=b.g.move(moving,matrix(q));hit=s^fixed;v=max(0.,float(hit.volume()))
 if v>.02:return (False,hit) if detail else False
 for f in stock:
  if (s^f).volume()>.02:return (False,s^f) if detail else False
 return (True,None) if detail else True

def edge(a,c):
 n=max(2,int(np.ceil(np.linalg.norm((a-c)*[1,1,1,1.7,1.7,1.7])/.7)))
 return all(collision(a+(c-a)*(i/n)) for i in range(1,n+1))

def measure(q):
 bb=np.array(b.g.move(moving,matrix(q)).bounding_box());ov=np.maximum(0,np.minimum(bb[3:],fbb[3:])-np.maximum(bb[:3],fbb[:3]));clear=bool(np.any(bb[:3]>fbb[3:]+4) or np.any(bb[3:]<fbb[:3]-4));return -np.log1p(np.prod(ov))+.015*np.linalg.norm(q[:3]),clear

tree=[];parents=[]
for name in ['S04_rigid_refined_progress.json','clavicle_goal_2_1.json','clavicle_goal_1_-1.json']:
 seed=read(WORK/name)['best_path'];start=len(tree)
 for j,q in enumerate(seed):tree.append(np.array(q,float));parents.append(start+j-1 if j else -1)
scores=[measure(q)[0] for q in tree];attempts=[0]*len(tree);contacts={};found=None
for it in range(20000):
 candidates=rng.integers(len(tree),size=30);ix=int(candidates[np.argmax([scores[i]-np.log1p(attempts[i])*.6+rng.gumbel()*.35 for i in candidates])]);q=tree[ix];attempts[ix]+=1;M=matrix(q)
 if ix not in contacts:
  pivots=[M[:3,3],M[:3,:3]@np.array([40,-20,-14])+M[:3,3],M[:3,:3]@np.array([70,-40,-20])+M[:3,3]]
  for ax in range(3):
   for sg in [-1,1]:
    p=q.copy();p[ax]+=sg*2;valid,hit=collision(p,True)
    if not valid and hit.volume()>.02:
     bb=np.array(hit.bounding_box());pivots.append((bb[:3]+bb[3:])/2)
  contacts[ix]=pivots
 if rng.random()<.25:
  qq=q.copy();qq[:3]+=rng.normal(0,1,3)*rng.choice([.3,1,2.5,5])
 else:
  pivot=contacts[ix][int(rng.integers(len(contacts[ix])))];ax=int(rng.integers(3));sg=int(rng.choice([-1,1]));angle=sg*float(rng.choice([.75,1.5,3,6]));Q=b.b.rot(ax,angle);N=np.eye(4);N[:3,:3]=Q@M[:3,:3];N[:3,3]=pivot+Q@(M[:3,3]-pivot);qq=unmatrix(N,q)
 if not collision(qq) or not edge(q,qq):continue
 score,clear=measure(qq);tree.append(qq);parents.append(ix);scores.append(score);attempts.append(0);ni=len(tree)-1
 if clear:found=ni;break
 if it%5==0:
  for ax in range(3):
   for sg in [-1,1]:
    end=qq.copy();end[ax]+=sg*160
    # Reject rays rapidly with coarse samples, then validate finely before accepting.
    if all(collision(qq+(end-qq)*t) for t in np.linspace(0,1,81)) and edge(qq,end):tree.append(end);parents.append(ni);found=len(tree)-1;break
   if found:break
  if found:break
 if time.time()-lastlog>35:
  lastlog=time.time();print('pivot',it,'nodes',len(tree),'calls',calls,'score',round(max(scores),3),'seconds',round(time.time()-tic),flush=True)
  j=int(np.argmax(scores));path=[]
  while j>=0:path.append(tree[j].tolist());j=parents[j]
  put(WORK/'clavicle_pivot_progress.json',{'iterations':it,'nodes':len(tree),'calls':calls,'best_path':path[::-1],'seconds':time.time()-tic})
 if time.time()-tic>600:break
if found is not None:
 path=[];j=found
 while j>=0:path.append(tree[j].tolist());j=parents[j]
 put(WORK/'clavicle_pivot_path.json',{'path':path[::-1],'part':key,'calls':calls,'passed_sampled_search':True});print('FOUND',len(path),calls,flush=True)
else:
 np.savez_compressed(WORK/'clavicle_pivot_tree.npz',nodes=np.array(tree),parents=np.array(parents));print('NO PATH',it,len(tree),calls,flush=True)
