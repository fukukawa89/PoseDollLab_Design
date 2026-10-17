"""Test simple turn-and-pull completions from the latest reachable pose."""
from o22f7_animation import *
from build_revo22_assembly import b
from scipy.spatial.transform import Rotation
import numpy as np,time,warnings
warnings.filterwarnings('ignore',message='Gimbal lock detected')
x=Build();x.begin(x.g['steps'][3]);key='frame/'+x.st['child'];inv=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inv@x.mats[k])
moving=shape(key);fixed=[shape(k) for k in ['frame/chest',x.st['id']+'/M3_nut',x.st['id']+'/M3_reaction_washer',x.st['id']+'/inner_M4_wide']];bounds=[np.array(f.bounding_box()) for f in fixed];calls=0;tic=time.time()
def matrix(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return M

def valid(q):
 global calls
 calls+=1;s=b.g.move(moving,matrix(q));bb=np.array(s.bounding_box())
 for f,bo in zip(fixed,bounds):
  if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
  if (s^f).volume()>.02:return False
 return True

def edge(p,q,step=.5):
 n=max(1,int(np.ceil(np.linalg.norm((q-p)*[1,1,1,1.7,1.7,1.7])/step)))
 return all(valid(p+(q-p)*(i/n)) for i in range(1,n+1))
path=read(WORK/'clavicle_corner_progress.json')['best_path'];p=np.array(path[-1]);M=matrix(p)
row=next(r for r in read(R/'Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1/carriers_refined/quinn_routing.json')['frames'] if r['body']=='clavicle_l.protract_frame');points=[np.zeros(3),np.array(moving.bounding_box()).reshape(2,3).mean(0)]+[(inv@np.r_[pt,1])[:3] for pt in row['paths_world_mm'][-1]]
print('start',arr(p),'pivots',len(points),flush=True)
for pi,point in enumerate(points):
 pivot=M[:3,:3]@point+M[:3,3]
 for axis in range(3):
  for sign in [-1,1]:
   prev=p;tail=[]
   for angle in range(3,91,3):
    Q=b.b.rot(axis,sign*angle);N=np.eye(4);N[:3,:3]=Q@M[:3,:3];N[:3,3]=pivot+Q@(M[:3,3]-pivot);e=Rotation.from_matrix(N[:3,:3]).as_euler('XYZ',degrees=True);alt=np.array([e[0]+180,180-e[1],e[2]+180]);e=min([v+360*np.round((prev[3:]-v)/360) for v in [e,alt]],key=lambda v:np.linalg.norm(v-prev[3:]));q=np.r_[N[:3,3],e]
    if not valid(q) or not edge(prev,q):break
    tail.append(q.tolist());prev=q
    for ax in [2,0,1]:
     for sg in [-1,1]:
      end=q.copy();end[ax]+=sg*160
      if all(valid(q+(end-q)*t) for t in np.linspace(0,1,41)) and edge(q,end):
       put(WORK/'clavicle_final_escape_path.json',{'path':path+tail+[end.tolist()],'part':key,'pivot':pi,'axis':axis,'angle':sign*angle,'calls':calls,'passed_sampled_search':True});print('FOUND',pi,axis,sign*angle,'exit',ax,sg,'calls',calls,flush=True);sys.exit()
 print('pivot',pi,'calls',calls,'seconds',round(time.time()-tic),flush=True)
 if time.time()-tic>400:break
print('NO SIMPLE EXIT',calls,flush=True)
