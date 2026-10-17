"""Adaptive rigid-motion search. Read-only on published geometry."""
from o22f7_animation import *
from build_revo22_assembly import b
import numpy as np,time,os
x=Build();st=x.g['steps'][3];x.begin(st);key='frame/'+st['child'];cache={}
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return b.g.move(cache[o['mesh']],x.mats[k])
inv=np.linalg.inv(x.mount);moving=b.g.move(shape(key),inv);fix={k:b.g.move(shape(k),inv) for k in ['frame/'+st['parent'],st['id']+'/M3_nut',st['id']+'/M3_reaction_washer',st['id']+'/inner_M4_wide']};bounds={k:np.array(s.bounding_box()) for k,s in fix.items()};calls=0;starttime=time.time();rng=np.random.default_rng(351)
lo=np.min([r[:3] for r in bounds.values()],axis=0);hi=np.max([r[3:] for r in bounds.values()],axis=0)
def moved(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return b.g.move(moving,M)
def valid(q):
 global calls
 calls+=1;s=moved(q);bb=np.array(s.bounding_box())
 for k,f in fix.items():
  if np.any(np.minimum(bb[3:],bounds[k][3:])<=np.maximum(bb[:3],bounds[k][:3])+1e-6):continue
  if (s^f).volume()>.02:return False
 return True
def clear(q):
 bb=np.array(moved(q).bounding_box());return bool(np.any(bb[:3]>hi+3) or np.any(bb[3:]<lo-3))
def edge(a,c,step=.6):
 # Rotational degrees are weighted by maximum mesh radius, 1 degree ~ 1.7 mm.
 length=np.linalg.norm((c-a)*[1,1,1,1.7,1.7,1.7]);n=max(1,int(np.ceil(length/step)))
 return all(valid(a+(c-a)*t/n) for t in range(1,n+1))
seed=np.array(read(WORK/'S04_rigid_refined_progress.json')['best_path']);tree=list(seed);parent=list(range(-1,len(seed)-1));scores=[np.linalg.norm(q[:3]) for q in tree];attempts=[0]*len(tree);found=None
# Broadly branch from each reachable pose. Do not commit to a single greedy cul-de-sac.
for n in range(60000):
 if n%20==0:
  nodes=np.array(tree);target=np.r_[rng.uniform(-90,90,3),rng.uniform(-175,175,3)];ix=int(np.argmin(np.sum(((nodes-target)*[1,1,1,.55,.55,.55])**2,axis=1)))
 else:
  # Sparse visitation and mild outward bias keep multiple passages under exploration.
  candidates=rng.integers(len(tree),size=min(24,len(tree)));rank=[scores[i]*.08-np.log1p(attempts[i])+rng.gumbel()*.55 for i in candidates];ix=int(candidates[np.argmax(rank)])
  target=tree[ix]+np.r_[rng.normal(0,5,3),rng.normal(0,9,3)]
 p=tree[ix];attempts[ix]+=1;direction=target-p;direction/=max(np.linalg.norm(direction*[1,1,1,.75,.75,.75]),1e-10)
 scale=float(rng.choice([.25,.5,1,2,4,8,12],p=[.04,.07,.14,.22,.25,.20,.08]));q=p+direction*scale
 if max(abs(q[:3]))>150 or max(abs(q[3:]))>260 or not valid(q):continue
 if not edge(p,q):continue
 tree.append(q);parent.append(ix);scores.append(np.linalg.norm(q[:3]));attempts.append(0);last=len(tree)-1
 if clear(q):found=last;break
 # Each successful node tries to leave in a ray, with ample distance from the whole parent.
 if n%5==0 and scores[-1]>12:
  for axis in [0,1,2]:
   for sign in [-1,1]:
    end=q.copy();end[axis]+=sign*160
    if edge(q,end,1):tree.append(end);parent.append(last);found=len(tree)-1;break
   if found:break
  if found:break
 if n%1000==0:
  best=int(np.argmax(scores));chain=[];j=best
  while j>=0:chain.append(tree[j].tolist());j=parent[j]
  put(WORK/'clavicle_adaptive_progress.json',{'iterations':n,'nodes':len(tree),'calls':calls,'seconds':time.time()-starttime,'best_path':chain[::-1]})
  print('adaptive',n,'nodes',len(tree),'calls',calls,'reach',round(max(scores),2),'seconds',round(time.time()-starttime),flush=True)
 if time.time()-starttime>850:break
if found is not None:
 path=[];j=found
 while j>=0:path.append(tree[j].tolist());j=parent[j]
 put(WORK/'clavicle_adaptive_path.json',{'part':key,'path':path[::-1],'calls':calls,'seconds':time.time()-starttime,'passed_sampled_search':True,'mesh_sha256':sha(G/x.scene['geometry_url'])});print('FOUND',len(path),calls,flush=True)
else:
 np.savez_compressed(WORK/'clavicle_adaptive_tree.npz',nodes=np.array(tree),parents=np.array(parent),attempts=np.array(attempts))
 print('NO PATH',n,len(tree),calls,round(time.time()-starttime),flush=True)
