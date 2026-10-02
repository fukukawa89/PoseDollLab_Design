import json,numpy as np
from common import *
from clearance import certify
rows=[]
for length in (2,3):
 p=OUT/f'cup_relief_L{length}_R0p35/core_meshes.npz';m=dict(np.load(p));r=certify(m['C01'],m['C02']@pose_matrices(15,100)['C02'].T);rows.append({'length_mm_each':length,'alpha_deg':15,'beta_deg':100,**r})
save('extension_midangle_counterexample.json',{'scope':'Same local cup relief, comparison of the 2 and 3 mm fork extensions at an interior mixed angle.','cases':rows,'physical_tested':False});print(rows)
