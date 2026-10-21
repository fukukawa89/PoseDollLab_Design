"""Analytic supporting-plane and journal superset regressions."""
import numpy as np
from common import *
from verify_journal_sweeps import split_journals,certify_frusta
from continuous_clearance import Certificate
from test_continuous import box
rows=[]
f=[{'sign':1,'lo':-2.,'hi':2.,'r0':1.,'r1':1.}]
t=np.array([[[0,2,0],[1,2,0],[0,2,1]]],float);r=certify_frusta(t,0,f,.5);assert r['status']=='CERTIFIED_JOURNAL_SUPERSET_SEPARATION';rows.append({'case':'analytic_cylinder_clear_triangle',**r})
t=np.array([[[0,.4,0],[1,.4,0],[0,.4,.1]]],float);r=certify_frusta(t,0,f,.01);assert r['status']!='CERTIFIED_JOURNAL_SUPERSET_SEPARATION';rows.append({'case':'inside_cylinder_never_passes',**r})
m=dict(np.load(OUT/'cup_relief_L3_R0p35/core_meshes.npz'))
for yoke,axis in [('C01',0),('C02',1)]:
 far,frusta,receipt=split_journals(m[yoke],axis);assert receipt['journal_triangles']+receipt['remaining_triangles']==receipt['total_triangles'];rows.append({'case':yoke+'_exhaustive_triangle_partition_and_conical_coverage',**receipt})
# Unsigned bounds are valid for open surface subsets; volume acceptance still
# requires the independent initial check against both complete closed meshes.
a=box([0,0,0],.5);b=box([0,0,5],.5)[:2];r=Certificate(a,b,unsigned=True).cell((-15,15),(-15,15),.5);assert r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE';rows.append({'case':'open_surface_unsigned_exclusion_bound',**r})
save('journal_method_regression.json',{'status':'PASS','cases':rows,'scope':'Independent analytic separating-plane cases and exhaustive partition checks; no physical qualification.'});print('PASS',len(rows),'groups')
