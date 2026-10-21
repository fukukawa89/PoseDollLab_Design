"""Goal-directed search from the seated frame, not the previous local maximum."""
from o22f7_animation import *
from build_revo22_assembly import b
import heapq,time,numpy as np
x=Build();st=x.g['steps'][10];x.begin(st);key='frame/'+st['child'];inverse=np.linalg.inv(x.mount)
raw=dict(x.raw);raw['clavicle_l.protract/r0']=-20;ff,oo=kin.owners(raw)
for k in x.mats:
 mm=x.meta['meta'][k]
 if 'clavicle_l.protract' in k:
  owner=ff[mm['body']] if mm['owner']=='rigid_frame' else oo[mm['module'],mm['owner']];x.mats[k]=owner@np.array(x.bind[x.idx[k]]['local']).reshape(4,4)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];s=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3));return b.g.move(s,inverse@x.mats[k])
moving=shape(key);fixed=[shape(k) for k in ['frame/'+st['parent'],'frame/clavicle_l.protract_frame',st['id']+'/M3_nut',st['id']+'/M3_reaction_washer',st['id']+'/inner_M4_wide']];bounds=[np.array(s.bounding_box()) for s in fixed];lo=np.min([r[:3] for r in bounds],axis=0);hi=np.max([r[3:] for r in bounds],axis=0);cache={};calls=0
starttime=time.time();goalaxis=int(sys.argv[1]) if len(sys.argv)>1 else 1;goalsign=int(sys.argv[2]) if len(sys.argv)>2 else -1
def shapeq(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return b.g.move(moving,M)
def valid(q):
 global calls
 q=tuple(q)
 if q in cache:return cache[q]
 s=shapeq(q);bb=np.array(s.bounding_box());calls+=1
 for f,bo in zip(fixed,bounds):
  if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
  if (s^f).volume()>.02:cache[q]=False;return False
 cache[q]=True;return True
start=(0.,)*6;queue=[(0,0,start)];parents={start:None};cost={start:0};found=None;best=start
for n in range(1800):
 if not queue:break
 _,g,p=heapq.heappop(queue)
 if cost[p]!=g:continue
 if goalsign*p[goalaxis]>goalsign*best[goalaxis]:best=p
 if n%25==0 and goalsign*p[goalaxis]>8:
  end=np.array(p);end[goalaxis]+=goalsign*170
  if all(valid(np.array(p)+(end-p)*t) for t in np.linspace(0,1,171)):
   end=tuple(end);parents[end]=p;found=end;break
 for ax in [goalaxis,*(i for i in range(6) if i!=goalaxis)]:
  for sg in [goalsign,-goalsign]:
   q=list(p);q[ax]+=sg*(1 if ax<3 else 3);q=tuple(q);ng=g+1
   if max(abs(v) for v in q[:3])>110 or max(abs(v) for v in q[3:])>170 or ng>=cost.get(q,1e9):continue
   if not valid(q) or not valid((np.array(p)+q)*.5):continue
   parents[q]=p;cost[q]=ng
   score=ng*.035-goalsign*q[goalaxis]-.02*np.linalg.norm(q[3:])-.03*np.linalg.norm(q[:3]);heapq.heappush(queue,(score,ng,q))
 if n%150==0:
  path=[];q=best
  while q is not None:path.append(q);q=parents[q]
  put(WORK/f'clavicle_right_parked_left_goal_{goalaxis}_{goalsign}.json',{'nodes':n,'calls':calls,'seconds':time.time()-starttime,'best_path':path[::-1]})
  print('goal',goalaxis,goalsign,n,'calls',calls,'reach',best[:3],round(time.time()-starttime),flush=True)
 if time.time()-starttime>450:break
if found:
 path=[];q=found
 while q is not None:path.append(q);q=parents[q]
 put(WORK/f'clavicle_right_parked_left_goal_{goalaxis}_{goalsign}_path.json',{'path':path[::-1],'part':key,'calls':calls,'passed_sampled_search':True});print('FOUND',goalaxis,goalsign,len(path),flush=True)
else:print('NO PATH',goalaxis,goalsign,n,calls,flush=True)

