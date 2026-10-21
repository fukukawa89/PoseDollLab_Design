"""Bidirectional rigid-motion search, using the verified local path as a seed."""
from o22f7_animation import Build,WORK,put,arr
from build_revo22_assembly import b
import numpy as np,time,json
x=Build();st=x.g['steps'][3];x.begin(st);key='frame/'+st['child'];cache={}
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return b.g.move(cache[o['mesh']],x.mats[k])
moving=shape(key);fix={k:shape(k) for k in ['frame/'+st['parent'],st['id']+'/M3_nut',st['id']+'/M3_reaction_washer',st['id']+'/inner_M4_wide']};bounds={k:np.array(v.bounding_box()) for k,v in fix.items()};inverse=np.linalg.inv(x.mount);calls=0;rng=np.random.default_rng(327)
def trans(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return x.mount@M@inverse
def valid(q):
 global calls
 ss=b.g.move(moving,trans(q));bb=np.array(ss.bounding_box());calls+=1
 for k,v in fix.items():
  if np.any(np.minimum(bb[3:],bounds[k][3:])<=np.maximum(bb[:3],bounds[k][:3])+1e-6):continue
  if float((ss^v).volume())>.02:return False
 return True
def distance(a,c):return np.linalg.norm((np.array(a)-c)*[1,1,1,1.3,1.3,1.3])
def edge(a,c,step=.8):
 n=max(2,int(np.ceil(distance(a,c)/step))+1)
 return all(valid(np.array(a)+(np.array(c)-a)*t) for t in np.linspace(0,1,n)[1:])
seed=json.loads((WORK/'S04_rigid_refined_progress.json').read_text('utf8'))['best_path'];A=[np.array(q) for q in seed];AP=[i-1 for i in range(len(A))];AP[0]=-1
end=np.array([0,110,0,0,0,0],float);assert valid(end);Z=[end];ZP=[-1];starttime=time.time();connected=None
for n in range(16000):
 # Both trees grow alternately; all joints remain rigid, with the same fixed obstacles.
 left=n%2==0;tree,parent=(A,AP) if left else (Z,ZP);other,op=(Z,ZP) if left else (A,AP)
 if n%5==0:target=other[int(rng.integers(len(other)))]
 elif n%4==0:target=np.r_[rng.uniform([-65,-65,-35],[75,115,65]),rng.uniform(-130,130,3)]
 else:
  base=np.array(seed[int(rng.integers(len(seed)))]);target=base+np.r_[rng.normal(0,22,3),rng.normal(0,32,3)]
 nodes=np.array(tree);ix=int(np.argmin(np.sum(((nodes-target)*[1,1,1,1.3,1.3,1.3])**2,axis=1)));p=tree[ix];dist=distance(p,target);q=p+(target-p)*min(1,3.0/max(dist,1e-10))
 if not edge(p,q):continue
 tree.append(q);parent.append(ix);newix=len(tree)-1
 oi=int(np.argmin(np.sum(((np.array(other)-q)*[1,1,1,1.3,1.3,1.3])**2,axis=1)))
 for z in range(100):
  p=other[oi];dist=distance(p,q);qq=p+(q-p)*min(1,3.0/max(dist,1e-10))
  if not edge(p,qq):break
  other.append(qq);op.append(oi);oi=len(other)-1
  if dist<=3.0:
   connected=(newix,oi) if left else (oi,newix);break
 if connected:break
 if n%100==0:print('RRT',n,len(A),len(Z),calls,round(time.time()-starttime),flush=True)
 if n%500==0:put(WORK/'clavicle_rrt_progress.json',{'iterations':n,'tree_sizes':[len(A),len(Z)],'calls':calls,'seconds':time.time()-starttime})
if connected:
 def trace(tree,parents,i):
  path=[]
  while i!=-1:path.append(tree[i].tolist());i=parents[i]
  return path[::-1]
 path=trace(A,AP,connected[0])+trace(Z,ZP,connected[1])[::-1][1:]
 put(WORK/'clavicle_rrt_path.json',{'part':key,'path':path,'calls':calls,'seconds':time.time()-starttime,'passed_sampled_search':True})
 print('FOUND',len(path),calls,round(time.time()-starttime),flush=True)
else:print('NO PATH',len(A),len(Z),calls,flush=True)
