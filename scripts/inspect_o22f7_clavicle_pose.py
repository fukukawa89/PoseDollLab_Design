"""Search a rigid insertion motion for the two integrated clavicle frames."""
from o22f7_animation import Build,WORK,put,arr
from build_revo22_assembly import b
import numpy as np,heapq,time,itertools,json
x=Build();solutions={};meshcache={}
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in meshcache:meshcache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return b.g.move(meshcache[o['mesh']],x.mats[k])
def local_transform(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return x.mount@M@np.linalg.inv(x.mount)

st=x.g['steps'][3];x.begin(st);q=__import__('json').loads((WORK/'S04_rigid_search_progress.json').read_text('utf8'))['best_path'][-1];key='frame/'+st['child'];o=shape(key);M=local_transform(q);moved=b.g.move(o,M);print('pose',q,'moving bbox',moved.bounding_box(),'parentbbox',shape('frame/chest').bounding_box())
fix={k:shape(k) for k in ['frame/chest',st['id']+'/M3_nut',st['id']+'/M3_reaction_washer',st['id']+'/inner_M4_wide']}
for axis in range(3):
 for sign in [-1,1]:
  qq=q.copy();qq[axis]+=sign*2;ss=b.g.move(o,local_transform(qq));print(axis,sign,{k:round(float((ss^v).volume()),5) for k,v in fix.items()})
