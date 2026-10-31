import time,numpy as np
from common import *
from continuous_clearance import Certificate
m=dict(np.load(OUT/'cup_relief_L3_R0p35/core_meshes.npz'));rows=[]
for x,y in [('C01','C14'),('C14','C01')]:
 t=time.perf_counter();r=Certificate(m[x],m[y]).cell((0,0),(0,0),.01,max_tri_depth=10,max_queries=200000);rows.append({'source':x,'target':y,'seconds':time.perf_counter()-t,**r});print(rows[-1],flush=True)
save('bearing_certification_preflight.json',{'cases':rows,'scope':'Static preflight to select the less conservative source tessellation; not motion acceptance.'})
