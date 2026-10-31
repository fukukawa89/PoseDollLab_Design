"""Map mixed bend angles with all four plastic pieces and existing fasteners."""
import itertools,json,numpy as np
from common import core,OUT,G8,save,pose_matrices,sha
from rigid_collision import Body,Pair,regression

def main():
 meshes=core();meshes['fasteners']=np.concatenate(list(dict(np.load(G8/'fastened_core/fasteners.npz')).values()));bodies={n:Body(m) for n,m in meshes.items()};pairs={}
 for x,y in itertools.combinations(bodies,2):
  if {x,y}<={'C14','C15','fasteners'}:continue
  pairs[(x,y)]=Pair(bodies[x],bodies[y])
 save('rigid_collision_regression.json',{'scope':'Comparison of compiled rigid transforms against original rebuilt-mesh collision checks','cases':regression(meshes)})
 rows=[]
 for a,b in itertools.product((-75,-60,-45,-30,0,30,45,60,75),(-100,-90,-75,-60,-45,-30,0,30,45,60,75,90,100)):
  mats=pose_matrices(a,b);findings=[]
  for (x,y),pair in pairs.items():
   r=pair.check(mats[x],mats[y])
   if not r['status'].startswith('CLEAR'):findings.append({'pair':[x,y],**r})
  status='FAIL' if any(r['status']=='PENETRATION' for r in findings) else 'REVIEW' if findings else 'CLEAR_NOMINAL_CORE_AND_FASTENERS'
  rows.append({'alpha_deg':a,'beta_deg':b,'status':status,'findings':findings});print(a,b,status,flush=True)
  save('bend_workspace.json',{'status':'RUNNING','cases':rows,'scope':'Discrete bend grid of O8 2 mm core and nominal fasteners. No outer twist housings, wiring or stops yet.','physical_tested':False,'manufacturing_released':False})
 save('bend_workspace.json',{'status':'SCOPED_GRID_COMPLETE','cases':rows,'pass':sum(x['status'].startswith('CLEAR') for x in rows),'fail':sum(x['status']=='FAIL' for x in rows),'review':sum(x['status']=='REVIEW' for x in rows),'input_sha256':{'core':sha(G8/'fork_extension_2mm/core_meshes.npz'),'fasteners':sha(G8/'fastened_core/fasteners.npz')},'scope':'Mixed bend angles, discrete core and fastener geometry only; untested intervals are not accepted.','physical_tested':False,'manufacturing_released':False})
if __name__=='__main__':main()
