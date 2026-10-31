"""Conservative discrete-pose clearance bounds using the 1-Lipschitz distance property.
Every source triangle is bounded by distance(center,target)-max vertex radius.
Unresolved triangles subdivide; exhaustion is UNKNOWN, never a pass.
"""
import json,hashlib
import numpy as np
import vtk
from reference_assembly import OUT,at_pose
from mesh_collision import polydata

def certify(a,b,required=.6,max_depth=10):
 distance=vtk.vtkImplicitPolyDataDistance();distance.SetInput(polydata(b));stack=[(t,0) for t in a];count=0;max_seen=0;lower=float('inf');unresolved=0;sample=float('inf')
 while stack:
  t,depth=stack.pop();p=t.mean(0);d=abs(float(distance.EvaluateFunction(p)));radius=float(np.linalg.norm(t-p,axis=1).max());lb=d-radius;count+=1;max_seen=max(max_seen,depth);sample=min(sample,d)
  if d<required-1e-6:return {'status':'INSUFFICIENT_CLEARANCE','required_mm':required,'distance_at_witness_mm':d,'witness_mm':p.tolist(),'queries':count}
  if lb>=required:lower=min(lower,lb);continue
  if depth>=max_depth:unresolved+=1;continue
  x,y,z=t;xy=(x+y)/2;yz=(y+z)/2;zx=(z+x)/2
  stack.extend((q,depth+1) for q in (np.array([x,xy,zx]),np.array([xy,y,yz]),np.array([zx,yz,z]),np.array([xy,yz,zx])))
 return {'status':'CERTIFIED_NOMINAL_CLEARANCE' if not unresolved else 'UNKNOWN','required_mm':required,'conservative_lower_bound_mm':lower,'smallest_evaluated_distance_mm':sample,'queries':count,'max_subdivision_depth':max_seen,'unresolved_triangles':unresolved}

def main():
 cases=[]
 for length in (0,1,2,3,4):
  meshes=dict(np.load(OUT.parent/f'fork_extension_{length}mm/core_meshes.npz'))
  for alpha,beta in ((0,0),(0,95),(0,100),(95,0),(100,0)):
   m=at_pose(meshes,alpha,beta);r=certify(m['C01'],m['C02']);cases.append({'extension_mm':length,'alpha_deg':alpha,'beta_deg':beta,**r});print(length,alpha,beta,r['status'],r.get('conservative_lower_bound_mm',r.get('distance_at_witness_mm')),flush=True)
   (OUT.parent/'fork_clearance.json').write_text(json.dumps({'scope':'Non-mating yoke-to-yoke nominal triangle surfaces at listed isolated angles only. Unsigned distance is not a replacement for collision checks. 0.6 mm is an initial pairwise allowance derived from two 0.3 mm service tolerances, not a verified tolerance model.','cases':cases,'physical_tested':False},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
