"""Discrete regression for added sensor retainers/back housing; no continuous proof."""
import sys,json,numpy as np
from pathlib import Path
import build_revo22_assembly as a
b=a.b;g=a.g;D=a.D;B=a.B
from connected import adjacent_pairs
p,m,raw,changed,service,C=a.model();old,oldmeta,st=b.baseline();adj=adjacent_pairs('quinn')
preset=g.read(B/'profiles/default_pose.json')['raw_deg'];cases={'A_STAND_35':preset}
# Include actual encoded UE fixtures as poses, plus single moving joint samples.
for n in ['left_elbow','asymmetric','right_forearm']:cases[n]=g.read(B/'ue'/f'{n}.payload.json')['joint_angles_deg']
for rid in ['upperarm_l/r0','upperarm_l/r1','upperarm_l/r2','upperarm_l/r3','elbow_l.flex/r0','forearm_l.twist/r0','hand_l.flex/r0','hand_l.deviate/r0','chest/r1','head/r2']:
 lo,hi=a.profile['raw_limits_deg'][rid]
 for v in np.linspace(lo,hi,7):cases[rid+'@'+str(v)]=dict(preset,**{rid:float(v)})
focus=set(changed);results=[];increases=[]
def related(aa,bb):
 ma,mb=m[aa],m[bb]
 # Pelvis and chest are separated by the waist body: record separately.
 if {ma['body'],mb['body']}=={'pelvis','chest'}:return False
 ga=ma.get('modules',[ma['module']]);gb=mb.get('modules',[mb['module']]);return ma['body']==mb['body'] or bool(set(ga)&set(gb)) or any(frozenset((x,y)) in adj for x in ga for y in gb)
for name,q in cases.items():
 posed,mat,f=a.pose_parts(p,m,raw,q);oldposed,oldmat,_=a.pose_parts(old,oldmeta,raw,q);keys=list(posed);boxes=np.array([posed[k].bounding_box() for k in keys]);findings=[]
 for i,key in enumerate(keys):
  if key not in focus:continue
  mask=np.all(np.minimum(boxes[i,3:],boxes[:,3:])>np.maximum(boxes[i,:3],boxes[:,:3])+1e-7,axis=1)
  for j in np.flatnonzero(mask):
   other=keys[j]
   if other==key or (other in focus and j<i) or not related(key,other):continue
   # Fixed-owner mating volumes do not obstruct a joint's movement.
   if np.max(abs(mat[key]@np.linalg.inv(np.array(m[key]['transform']))-mat[other]@np.linalg.inv(np.array(m[other]['transform']))))<1e-7:continue
   v=max(0.,float((posed[key]^posed[other]).volume()))
   if v<.01:continue
   oldv=float((oldposed[key]^oldposed[other]).volume()) if key in oldposed and other in oldposed else 0
   row={'pair':[key,other],'new_mm3':v,'inherited_mm3':oldv}
   findings.append(row)
   if v>oldv+.02:increases.append({'pose':name,**row})
 results.append({'pose':name,'adjacent_contacts':findings});print(name,len(findings),'increases',len(increases),flush=True)
b.put(D/'adjacent_regression.json',{'status':'REGRESSION_PASS_WITH_INHERITED_CONTACTS' if not increases else 'NEEDS_CORRECTION','cases':results,'new_or_increased_contacts':increases,'continuous_collision_proof':False,'physical_test':False,'excluded_nonadjacent_body_pair':['pelvis','chest'],'scope':'Added/revised printed parts against moving adjacent mechanisms; 7-point raw-axis sampling; same-motion fixed fits assessed separately.'})
