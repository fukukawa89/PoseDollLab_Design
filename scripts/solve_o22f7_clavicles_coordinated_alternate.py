"""Coordinate two existing chest-clear candidate motions; screening only."""
from o22f7_animation import *
from build_revo22_assembly import b
from functools import lru_cache
import heapq,time,itertools
x=Build();x.begin(x.g['steps'][3]);lk='frame/clavicle_l.protract_frame';rk='frame/clavicle_r.protract_frame';lm=x.mount.copy();x.begin(x.g['steps'][10]);rm=x.mount.copy();paths=[np.array(read(WORK/sys.argv[1])['best_path']),np.array(read(WORK/'clavicle_right_goal_0_1_path.json')['path'])];mounts=[lm,rm];inverses=[np.linalg.inv(lm),np.linalg.inv(rm)];base=[]
for k in [lk,rk]:
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];base.append(b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),x.mats[k]))
def pose(side,q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];s=b.g.move(base[side],mounts[side]@M@inverses[side]);return s,np.array(s.bounding_box())
@lru_cache(48)
def fixed(side,i):return pose(side,paths[side][i])
calls=0
@lru_cache(None)
def valid(i,j):
 global calls
 a,ba=fixed(0,i);c,bc=fixed(1,j);calls+=1
 if np.any(np.minimum(ba[3:],bc[3:])<=np.maximum(ba[:3],bc[:3])+1e-6):return True
 return (a^c).volume()<=.02
@lru_cache(None)
def edge(i,j,ii,jj):
 if not valid(ii,jj):return False
 lp,lq=paths[0][i],paths[0][ii];rp,rq=paths[1][j],paths[1][jj];n=max(1,int(np.ceil(max(np.linalg.norm((lq-lp)*[1,1,1,2,2,2]),np.linalg.norm((rq-rp)*[1,1,1,2,2,2]))/.7)))
 for t in np.arange(1,n)/n:
  a,ba=pose(0,lp+(lq-lp)*t);c,bc=pose(1,rp+(rq-rp)*t)
  if np.any(np.minimum(ba[3:],bc[3:])<=np.maximum(ba[:3],bc[:3])+1e-6):continue
  if (a^c).volume()>.02:return False
 return True
parents={(0,0):None};queue=[(0,0,0)];visited=set();tic=time.time();goal=None
while queue:
 _,i,j=heapq.heappop(queue)
 if (i,j) in visited:continue
 visited.add((i,j))
 if j==len(paths[1])-1:goal=(i,j);break
 for di,dj in [(0,1),(1,1),(1,0)]:
  ii,jj=i+di,j+dj
  if ii>=len(paths[0]) or jj>=len(paths[1]) or (ii,jj) in parents:continue
  if edge(i,j,ii,jj):parents[ii,jj]=(i,j);heapq.heappush(queue,(-jj-.18*ii,ii,jj))
 if len(visited)%100==0:print('nodes',len(visited),'index',i,j,'calls',calls,'seconds',round(time.time()-tic),flush=True)
 if time.time()-tic>420:break
if goal:
 pairs=[];p=goal
 while p is not None:pairs.append(p);p=parents[p]
 pairs=pairs[::-1];put(WORK/('coordinated_'+Path(sys.argv[1]).stem+'_path.json'),{'passed_pair_screening':True,'complete_left_path':False,'pairs':pairs,'left_path':paths[0].tolist(),'right_path':paths[1].tolist(),'goal':goal,'calls':calls,'seconds':time.time()-tic});print('FOUND COORDINATION',goal,len(pairs),calls,flush=True)
else:put(WORK/('coordinated_'+Path(sys.argv[1]).stem+'_review.json'),{'found':False,'nodes':len(visited),'calls':calls,'seconds':time.time()-tic});print('NO COORDINATION',len(visited),calls,flush=True)

