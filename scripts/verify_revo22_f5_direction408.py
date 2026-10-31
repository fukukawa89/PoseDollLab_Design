import json,shutil,numpy as np,trimesh
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,md,union
from prune_revo22_f5_contacts402 import rods
from verify_revo22_x062_removal245 import exact_clear
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick
p='X046';a=O/'candidates'/p/'cap396_0';l='direction408';b=O/'candidates'/p/l;n=np.load(a/'parts'/f'{p}.npz');d=json.loads((a/'design'/f'{p}.json').read_text());body=solid(n['v'],n['f']);ts=solid(n['teeth_v'],n['teeth_f']);tm=trimesh.Trimesh(n['v'],n['f'],process=False);ns=tm.face_normals[np.argsort(-tm.area_faces)[:80]];result=True
for i,r,s in rods(d,ts):
 dr=np.array(r['stem_removal_vector'])
 if exact_clear(s-body,body,dr*220)[0]:continue
 dirs=[sg*np.array(d['orientation']['matrix'])[:,k]for k in range(3)for sg in [-1,1]]+[sg*nn for nn in ns for sg in [-1,1]]
 for j in range(100):
  z=1-2*(j+.5)/100;rad=np.sqrt(1-z*z);ang=j*np.pi*(3-np.sqrt(5));dirs.append(np.array([rad*np.cos(ang),rad*np.sin(ang),z]))
 seen=[];good=None
 for dr in dirs:
  dr=dr/np.linalg.norm(dr)
  if any(np.dot(dr,q)>.99999 for q in seen):continue
  seen.append(dr)
  if exact_clear(s-body,body,dr*220)[0]:good=dr;break
 print('DIRECTION408',i,len(seen),None if good is None else good.tolist(),flush=True)
 if good is None:result=False;break
 d['local_route_repairs'][i]['stem_removal_vector']=good.tolist()
if result:
 shutil.copytree(a,b,dirs_exist_ok=True);d['trial']=l;put(b/'design'/f'{p}.json',d)
 out=b/'verification/f5_geometry.json'
 if out.exists():out.unlink()
 g=geo(p,l);assert fit(p,l)['fit_and_pose_geometry_passed'];assert pick(p);print('DIRECTION408_PASS',flush=True)
