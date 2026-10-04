"""Full-resolution collision tests of new features, including stops outside limits."""
from pathlib import Path
import sys,json,itertools,time
import numpy as np
H=Path(__file__).resolve().parents[2];OUT=H/'generated/revO10/runs/o10_20260926_r1'
sys.path.insert(0,str(H/'cad/revO9'));from rigid_collision import Body,Pair
from common import rot,pose_matrices

def main():
 mesh=dict(np.load(OUT/'internal_stops/parts.npz'));fast=dict(np.load(H/'generated/revO8/runs/o8_20260925_r1/fastened_core/fasteners.npz'));mesh['fasteners']=np.concatenate(list(fast.values()))
 bodies={k:Body(t) for k,t in mesh.items()};pairs={(a,b):Pair(bodies[a],bodies[b]) for a,b in itertools.combinations(mesh,2) if (a,b) not in [('C14','C15'),('C14','fasteners'),('C15','fasteners')]}
 rows=[]
 grid=list(itertools.product((-28,-25,-15,0,15,25,28),(-98,-96.2,-75,-50,-25,0,25,50,75,96.2,98)))
 grid+=list(itertools.product((-29,-30,29,30),(0,)))+list(itertools.product((0,),(-99,-100,99,100)))
 if '--quick' in sys.argv:grid=[(0,0),(25,96.2),(-25,-96.2),(28,0),(29,0),(0,98),(0,99)]
 for a,b in grid:
  mats=pose_matrices(a,b);hits=[]
  for (x,y),pair in pairs.items():
   r=pair.check(mats[x],mats[y],tol=.005)
   if not r['status'].startswith('CLEAR'):hits.append({'pair':[x,y],**r})
  row={'alpha':a,'beta':b,'inside_nominal_stops':abs(a)<28 and abs(b)<98,'findings':hits};rows.append(row)
  print(a,b,hits if '--quick' in sys.argv else [(r['pair'],r['status']) for r in hits],flush=True)
 (OUT/'internal_stops/collision_grid.json').write_text(json.dumps({'scope':'Full closed meshes, nominal discrete poses. Stop-face contact at boundaries is expected.','cases':rows,'manufacturing_released':False},indent=2)+'\n')
if __name__=='__main__':main()

