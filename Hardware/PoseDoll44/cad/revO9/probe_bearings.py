import itertools,numpy as np
from common import *
from rigid_collision import Body
m=dict(np.load(OUT/'cup_relief_L3_R0p35/core_meshes.npz'));rows=[]
for yoke,ring in itertools.product(('C01','C02'),('C14','C15')):
 target=Body(m[ring]);pts=np.unique(np.r_[m[yoke].reshape(-1,3),m[yoke].mean(1)],axis=0)
 for angle in (-30,0,30):
  M=rot([1,0,0],angle) if yoke=='C01' else rot([0,1,0],-angle);q=pts@M;ds=np.array([target.distance.EvaluateFunction(p) for p in q]);k=int(np.argmin(ds));r={'pair':[yoke,ring],'angle_deg':angle,'minimum_sampled_signed_distance_mm':float(ds[k]),'source_witness_mm':pts[k].tolist(),'target_witness_mm':q[k].tolist()};rows.append(r);print(r,flush=True)
save('bearing_clearance_probes.json',{'scope':'Signed vertices and triangle-centroid probes only; upper bounds on the actual minimum clearance, not a whole-surface certificate.','cases':rows})
