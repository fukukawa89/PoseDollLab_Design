import itertools,numpy as np
from common import *
from rigid_collision import Body
m=core();target=Body(m['C02']);pts=np.unique(np.r_[m['C01'].reshape(-1,3),m['C01'].mean(1)],axis=0);rows=[]
for a,b in itertools.product((0,5,10,15,20,25,30),(0,50,100)):
 q=pts@pose_matrices(a,b)['C02'];d=np.array([target.distance.EvaluateFunction(p) for p in q]);k=np.argmin(d);row={'alpha':a,'beta':b,'minimum_sampled_signed_distance_mm':float(d[k]),'witness_C01':pts[k].tolist()};rows.append(row);print(row,flush=True)
save('surface_distance_probes.json',{'scope':'Vertices and face centroids only, upper bounds on minimum signed clearance. Not a whole-surface certificate.','cases':rows})
