"""Find proper rigid congruence between frozen F4 material solids."""
import json,itertools,numpy as np,trimesh
from scipy.spatial import cKDTree
from search_revo22_f5_orientation268 import O,OLD,put
from build_revo22_fins import solid

def info(pid):
 n=np.load(OLD/'parts'/f'{pid}.npz');m=trimesh.Trimesh(n['v'],n['f'],process=False);vals,U=np.linalg.eigh(m.moment_inertia);return dict(id=pid,n=n,mesh=m,eig=vals,U=U,center=m.center_mass,volume=m.volume,solid=solid(n['v'],n['f']))
def register(a,b):
 if abs(a['volume']-b['volume'])>1e-4 or np.max(abs(a['eig']-b['eig']))>1e-3:return None
 best=None
 for sig in itertools.product([-1,1],repeat=3):
  Q=b['U']@np.diag(sig)@a['U'].T
  if np.linalg.det(Q)<0:continue
  off=b['center']-Q@a['center'];v=a['n']['v']@Q.T+off;dist=cKDTree(b['n']['v']).query(v)[0]
  if np.quantile(dist,.9)>.01:continue
  aa=a['solid'].transform(np.c_[Q,off]);bb=b['solid'];removed=aa-bb;added=bb-aa;err=float(abs(removed.volume())+abs(added.volume()))
  if err<1e-4:
   rec=dict(from_id=a['id'],to_id=b['id'],rotation=Q.tolist(),translation=off.tolist(),determinant=float(np.linalg.det(Q)),symmetric_material_difference_mm3=err,vertex_nearest_90pct_mm=float(np.quantile(dist,.9)),maximum_vertex_nearest_mm=float(dist.max()),policy='Proper rigid transform, conserved material volume and inertia, bidirectional Boolean material difference below 0.0001 mm3. The final original body vertices are transformed rigidly, never replaced by a sibling body.')
   if best is None or err<best['symmetric_material_difference_mm3']:best=rec
 return best
if __name__=='__main__':
 inv=json.loads((O/'inventory.json').read_text());ids=[r['id']for r in inv['rows']];refs=[];groups=[];mapping={}
 for pid in ids:
  a=info(pid);matched=False
  for j,b in enumerate(refs):
   fit=register(a,b)
   if fit:
    groups[j].append(pid);mapping[pid]=fit;matched=True;break
  if not matched:refs.append(a);groups.append([pid]);mapping[pid]=dict(from_id=pid,to_id=pid,rotation=np.eye(3).tolist(),translation=[0,0,0],determinant=1.,symmetric_material_difference_mm3=0)
 put(O/'rigid_families286.json',dict(groups=groups,mapping=mapping,body_geometry_unchanged=True));print('RIGID_FAMILIES',len(groups),flush=True)
 for g in groups:
  if len(g)>1:print(g,flush=True)
