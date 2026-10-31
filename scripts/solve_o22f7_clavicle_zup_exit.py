"""Search arbitrary straight exits from a verified reachable pose."""
from o22f7_animation import *
from build_revo22_assembly import b
import numpy as np,time,itertools
x=Build();x.begin(x.g['steps'][3]);key='frame/'+x.st['child'];inv=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inv@x.mats[k])
moving=shape(key);fixed=[shape(k) for k in ['frame/chest',x.st['id']+'/M3_nut',x.st['id']+'/M3_reaction_washer',x.st['id']+'/inner_M4_wide']];bounds=[np.array(f.bounding_box()) for f in fixed];calls=0;tic=time.time();cache={}
def valid(q):
 global calls
 key=tuple(q)
 if key in cache:return cache[key]
 calls+=1;M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];s=b.g.move(moving,M);bb=np.array(s.bounding_box())
 for f,bo in zip(fixed,bounds):
  if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
  if (s^f).volume()>.02:cache[key]=False;return False
 cache[key]=True;return True
source=WORK/'clavicle_corner_zup_progress.json';path=read(source)['best_path'];directions=[unit(v) for v in itertools.product([-1,0,1],repeat=3) if any(v)]
for i in range(120):
 z=1-2*(i+.5)/120;r=np.sqrt(1-z*z);a=i*np.pi*(3-np.sqrt(5));directions.append(np.array([r*np.cos(a),r*np.sin(a),z]))
for si in [len(path)-1]:
 p=np.array(path[si]);print('seed',si,arr(p),flush=True)
 for d in directions:
  end=p.copy();end[:3]+=d*220
  if not all(valid(p+(end-p)*t) for t in np.linspace(0,1,111)):continue
  if not all(valid(p+(end-p)*t) for t in np.linspace(0,1,881)):continue
  put(WORK/'clavicle_sphere_exit_path.json',{'path':path[:si+1]+[end.tolist()],'source':str(source),'part':key,'passed_sampled_search':True,'calls':calls});print('FOUND',si,arr(d),calls,flush=True);sys.exit()
 print('failed',si,'calls',calls,'seconds',round(time.time()-tic),flush=True)
 if time.time()-tic>350:break
print('NO SPHERICAL EXIT',calls,flush=True)


