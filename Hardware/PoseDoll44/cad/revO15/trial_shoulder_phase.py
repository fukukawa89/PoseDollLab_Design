from associated_fit import *
import layout_fullbody as layout
from raw_paths import paths
from carriers_swept import motion_bank


def evaluate(char):
 subset=['waist','chest','head','clavicle_l.protract','clavicle_l.elevate','upperarm_l','elbow_l.flex','forearm_l.twist','hand_l.flex','hand_l.deviate']
 p0,mm,f=associated_parts(char,ASSEMBLY_POSE,only=subset);_,m0,_,_,pr=layout.build(char,ASSEMBLY_POSE,geometry=False);T0,_=fk(pr,ASSEMBLY_POSE);adj=adjacent_pairs(char);keys=list(p0)
 def matrix(k,m,T):return T[k.split('/',1)[1]] if k.startswith('frame/') else m[k]['transform']
 I0={k:np.linalg.inv(matrix(k,m0,T0)) for k in keys};cache={};potential={}
 for i,a in enumerate(keys[:-1]):
  ma=mm[a];ga=ma.get('modules',[ma['module']]);others=[]
  for j in range(i+1,len(keys)):
   b=keys[j];mb=mm[b];gb=mb.get('modules',[mb['module']])
   if ma['body']==mb['body']:continue
   if set(ga)&set(gb) or any(frozenset((x,y)) in adj for x in ga for y in gb):others.append(j)
  potential[i]=np.array(others,int)
 def check(label,m,T):
  matrices={k:matrix(k,m,T) for k in keys};parts={k:pose(s,(matrices[k]@I0[k])[:3,:3],(matrices[k]@I0[k])[:3,3]) for k,s in p0.items()};bounds=np.array([s.bounding_box() for s in parts.values()])
  for i,a in enumerate(keys[:-1]):
   ix=potential[i]
   if not len(ix):continue
   ix=ix[np.all(np.minimum(bounds[i,3:],bounds[ix,3:])>np.maximum(bounds[i,:3],bounds[ix,:3])+1e-8,axis=1)];IA=np.linalg.inv(matrices[a])
   for j in ix:
    b=keys[j];stamp=(a,b,tuple(np.round(IA@matrices[b],9).ravel()))
    if stamp not in cache:cache[stamp]=float((parts[a]^parts[b]).volume())
    if cache[stamp]>1e-4:return {'sample':label,'pair':[a,b],'volume_mm3':cache[stamp]}
 for label,m,T in motion_bank(char):
  bad=check(label,m,T)
  if bad:return {'stage':'endpoints','failure':bad}
 print('PHASE ENDPOINT CLEAR',char,flush=True)
 for label,m,T,detail in paths(char,['arms_forward','arms_overhead','arms_side','forehead','touch_back_head']):
  bad=check(label,m,T)
  if bad:return {'stage':'raw_path','failure':bad}
 return None

old=layout.config;rows=[]
for ph in (180,150,-150,120,-120,90,-90,60,-60,30,-30):
 def shifted(char):
  pr,mm=old(char)
  for m in mm:
   if m['id'].startswith('upperarm_'):m['F']=(np.array(m['F'])@rot(2,ph)).tolist()
  return pr,mm
 layout.config=shifted
 try:bad=evaluate('quinn')
 finally:layout.config=old
 rows.append({'phase_deg':ph,'failure':bad});save('shoulder_phase_path_trials.json',{'trials':rows,'winner':ph if bad is None else None});print('SHOULDER PHASE',ph,bad,flush=True)
 if bad is None:break
