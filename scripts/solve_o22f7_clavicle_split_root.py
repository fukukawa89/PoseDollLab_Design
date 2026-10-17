"""Find a complete escape for the candidate proximal half using already known motion."""
from o22f7_animation import *
from build_revo22_assembly import b
import itertools,time
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);key='frame/clavicle_l.protract_frame';inverse=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),x.mats[k])
orig=shape(key);root=orig^b.b.box([-200,-200,250],[-28,200,550]);root=b.g.move(root,inverse);fixed=[b.g.move(shape(k),inverse) for k in ['frame/chest']+['clavicle_l.protract/'+t for t in ['M3_nut','M3_reaction_washer','inner_M4_wide']]];bounds=[np.array(f.bounding_box()) for f in fixed]
def M(q):
 mat=np.eye(4);mat[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);mat[:3,3]=q[:3];return mat
def valid(q):
 s=b.g.move(root,M(q));bb=np.array(s.bounding_box())
 for f,bo in zip(fixed,bounds):
  if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
  if(s^f).volume()>.02:return False
 return True
D=[np.array(v,float)/np.linalg.norm(v) for v in itertools.product([0,-1,1],repeat=3) if any(v)];source=read(WORK/'clavicle_corner_zup_progress.json');path=source.get('best_path',source.get('path'));found=None
for i in range(0,min(180,len(path)),4):
 q=np.array(path[i]);assert valid(q)
 for d in D:
  end=q.copy();end[:3]+=d*160
  if all(valid(q+(end-q)*t) for t in np.linspace(0,1,161)):
   found=path[:i+1]+[end.tolist()];break
 if found:break
 if i%20==0:print('ROOT',i,q[:3].tolist(),flush=True)
put(C/'root_escape_candidate.json',{'status':'PATH_CANDIDATE' if found else 'NO_PATH_FOUND','path':found,'split_world_x':-28,'source_prefix_end':i,'base_path_sha256':sha(WORK/'clavicle_corner_zup_progress.json'),'checked_coarse_only':True})
print('RESULT',i,'FOUND',bool(found),flush=True)
