from layout_fullbody import *
from verify_kinematics import groups_for
from o15_kinematics import semantic_matrix
_,_,st,_,prof=build('quinn',{},geometry=False);groups=groups_for(prof,st);out={}
for name in ('waist','chest'):
 g=next(g for g in groups if g['id']==name);targets=[semantic_matrix(g['semantic_axes'],v) for v in itertools.product(*[[lo,0,hi] for lo,hi in g['semantic_limits_deg']])];candidates=[]
 for az,el,phase,bias in itertools.product(range(0,360,45),(-45,0,45,90),range(0,360,45),(35,42,48,55)):
  azr,elr=np.deg2rad([az,el]);F=frame([np.cos(elr)*np.cos(azr),np.cos(elr)*np.sin(azr),np.sin(elr)])@rot(2,phase);V=F@rot(1,-bias);valid=True;qq=[]
  for M in targets:
   q,e=three_axis.inverse(F.T@M@V)
   if e>1e-7 or abs(q[0])>168 or abs(q[1])>44.99 or not -89.99<=q[2]<=-.01:valid=False;break
   qq.append(q)
  if valid:candidates.append({'az':az,'el':el,'phase':phase,'bias':bias,'F':F.tolist(),'V':V.tolist(),'minimum_margin_deg':float(min(min(170-abs(q[0]),45-abs(q[1]),q[2]+90,-q[2]) for q in qq))})
 out[name]=candidates;print(name,'valid',len(candidates),flush=True)
save('trunk_orientation_candidates.json',{'groups':out,'scope':'27 semantic Euler corners/midpoints per module; raw joint ranges only.'})
