from o22f7_animation import *
from build_revo22_assembly import b
import numpy as np,itertools,time
x=Build();x.begin(x.g['steps'][3]);inv=np.linalg.inv(x.mount);key='frame/'+x.st['child']
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inv@x.mats[k])
moving=shape(key);fixed=[shape(k) for k in ['frame/chest',x.st['id']+'/M3_nut',x.st['id']+'/M3_reaction_washer',x.st['id']+'/inner_M4_wide']];bounds=[np.array(f.bounding_box()) for f in fixed];calls=0

def valid(q):
 global calls
 calls+=1;M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];s=b.g.move(moving,M);bb=np.array(s.bounding_box())
 for f,bo in zip(fixed,bounds):
  if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
  if (s^f).volume()>.02:return False
 return True
for name in ['clavicle_goal_2_1.json','clavicle_goal_1_-1.json']:
 path=read(WORK/name)['best_path'];p=np.array(path[-1],float);print('endpoint',name,p.tolist(),flush=True)
 for d in sorted([v for v in itertools.product([0,-1,1],repeat=3) if any(v)],key=lambda v:sum(z*z for z in v)):
  end=p.copy();end[:3]+=np.array(d)*160/np.linalg.norm(d)
  if not all(valid(p+(end-p)*t) for t in np.linspace(0,1,81)):continue
  if all(valid(p+(end-p)*t) for t in np.linspace(0,1,321)):
   result={'path':path+[end.tolist()],'part':key,'source':name,'passed_sampled_search':True,'calls':calls};put(WORK/'clavicle_escape_path.json',result);print('FOUND',name,d,calls,flush=True);sys.exit()
 print('no escape',name,calls,flush=True)
