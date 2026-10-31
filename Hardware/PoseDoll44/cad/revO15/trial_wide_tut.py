from common import *
from layout_fullbody import libraries
import tut,twist
p,o,sk=libraries()['tut'];p=dict(p)
p['C01']-=cyl(1.25,-22,0)+box([-4.1,-4.1,-2.6],[4.1,4.1,1.6])
AX=np.array([[1,0,0],[0,0,1],[0,-1,0]])
for side in (-1,1):
 cut=twist.sector(6.4,7.8,-141,141,11.4,13.6);cut=pose(pose(cut,rot(0,180)) if side<0 else cut,AX)
 for k in ('C14','C15'):p[k]-=cut
rr=[]
for a,b in itertools.product((-25,0,25),(-98,-105,-110,-115,-120,-125,-130,-135)):
 fs=tut.frames([0,a,b,0]);hh=hits({k:pose(v,fs[o[k]]) for k,v in p.items()});rr.append({'angles':[a,b],'findings':hh});print(a,b,[(h['pair'],round(h['overlap_mm3'],2)) for h in hh],flush=True)
save('tut_wide_trial.json',{'records':rr})
