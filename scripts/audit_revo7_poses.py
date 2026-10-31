"""Keep O6 stress cases while separating out-of-range and impossible symmetric targets."""
from pathlib import Path
import json,sys,hashlib,itertools,math
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';V=H/'verification/revO7/runs/o7_20260924_r1'
sys.path.insert(0,str(R/'scripts'));from study_revo import anatomy
from model import fk,keyposes

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def segment_dist(a,b,c,d):
 u=b-a;v=d-c;w=a-c;A=float(u@u);B=float(u@v);C=float(v@v);D=float(u@w);E=float(v@w)
 cand=[]
 if A>0:
  for t in (0.,1.):s=np.clip((B*t-D)/A,0,1);cand.append(np.linalg.norm(w+s*u-t*v))
 if C>0:
  for s in (0.,1.):t=np.clip((B*s+E)/C,0,1);cand.append(np.linalg.norm(w+s*u-t*v))
 den=A*C-B*B
 if den>1e-12:
  s=(B*E-C*D)/den;t=(A*E-B*D)/den
  if 0<=s<=1 and 0<=t<=1:cand.append(np.linalg.norm(w+s*u-t*v))
 return float(min(cand or [np.linalg.norm(w)]))
def main():
 lpath=H/'generated/revO6/runs/o6_20260924_r1/bilateral_search/layout_search.json';layout=json.loads(lpath.read_text());rows=[];targets=[];sources=[Path(__file__),lpath,R/'scripts/study_revo.py',R/'scripts/revo_common.py',H/'cad/model.py']
 for char in ('manny','quinn'):
  p=anatomy(char,480);sources.append(H/f'mechanical_manifest/physical_{char}_44_revG_humanform_trial.json');limits={a['id']:np.degrees(a['limits_rad']) for a in p['axes']}
  c=next(x for x in layout['characters'] if x['character']==char and x['side']=='l')
  for pose in c['poses']:
   bad=[{'axis':n,'deg':v,'limits_deg':limits[n].tolist()} for n,v in pose['angles_deg'].items() if not limits[n][0]-1e-8<=v<=limits[n][1]+1e-8]
   if bad:rows.append({'character':char,'pose':pose['pose'],'violations':bad,'O6_case_retained_as':'OUT_OF_RANGE_STRESS_NOT_REQUIRED_PROFILE_RANGE'})
  T,_=fk(p,keyposes()['arms_crossed']);old=segment_dist(T['elbow_l'][:3,3],T['hand_l'][:3,3],T['elbow_r'][:3,3],T['hand_r'][:3,3])
  # Task-space sample: preserve crossed forearms but place left above right.
  # Search within original profile limits; objective targets crossed wrists at
  # chest height and separated forearm centerlines, not preset mirrored angles.
  ids=[f'{n}_{s}.{a}' for s in ('l','r') for n,a in [('upperarm','flex'),('upperarm','abduct'),('upperarm','twist'),('elbow','flex')]]
  lower=np.array([limits[x][0] for x in ids]);upper=np.array([limits[x][1] for x in ids]);start=np.array([65,-20,60,115,65,-20,60,115],float);rng=np.random.default_rng(74480)
  def evaluate(v,detail=False):
   q=dict(zip(ids,v));T,_=fk(p,q);ch=T['chest'][:3,3];L=T['hand_l'][:3,3]-ch;RR=T['hand_r'][:3,3]-ch
   # Cross body; higher left wrist, lower right wrist. Deliberate task-space
   # design choices; no claim these bounds describe every valid crossed pose.
   tarL=np.array([35,-30,35]);tarR=np.array([45,30,8]);cost=float(((L-tarL)**2).sum()+((RR-tarR)**2).sum())
   sep=segment_dist(T['elbow_l'][:3,3],T['hand_l'][:3,3],T['elbow_r'][:3,3],T['hand_r'][:3,3]);cost+=100*max(18.5-sep,0)**2
   cost+=.05*float(((v-start)**2).sum())
   if detail:return {'angles_deg':{n:float(x) for n,x in q.items()},'left_wrist_relative_chest_mm':L.tolist(),'right_wrist_relative_chest_mm':RR.tolist(),'forearm_centerline_separation_mm':sep,'forearm_capsule_radius_assumption_mm':9,'in_original_joint_limits':bool(np.all(v>=lower-1e-9) and np.all(v<=upper+1e-9)),'score':cost}
   return cost
  best=(float('inf'),None)
  for k in range(40):
   v=np.clip(start+(0 if k==0 else rng.normal(0,30,8)),lower,upper)
   for step in (15,8,4,2,1,.5):
    for _ in range(10):
     changed=False
     for i in rng.permutation(8):
      vs=[v.copy() for j in range(3)];vs[1][i]=min(upper[i],v[i]+step);vs[2][i]=max(lower[i],v[i]-step);scores=[evaluate(x) for x in vs];j=int(np.argmin(scores));changed|=j!=0;v=vs[j]
     if not changed:break
   score=evaluate(v)
   if score<best[0]:best=(score,v.copy())
  targets.append({'character':char,'old_symmetric_forearm_centerline_separation_mm':old,'old_symmetric_target_has_capsule_overlap':old<18,'asymmetric_crossed_example':evaluate(best[1],True),'status':'ANATOMICAL_CANDIDATE_ONLY_REAL_MECHANISM_AND_CONTINUOUS_PATH_NOT_QUALIFIED'})
  print(char,targets[-1],flush=True)
 result={'schema':'o7-pose-evidence-audit-v1','O6_reports_modified':False,'out_of_range_states':rows,'crossed_arms_targets':targets,'actions_removed':False,'policy':'Out-of-range cases remain stress evidence; original acceptance ranges preserved. Add a physically distinct crossed-arm candidate, never relabel old module collisions as clearance.','input_sha256':{p.relative_to(R).as_posix():sha(p) for p in sources},'physical_tested':False,'manufacturing_released':False}
 V.mkdir(parents=True,exist_ok=True);(V/'pose_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
