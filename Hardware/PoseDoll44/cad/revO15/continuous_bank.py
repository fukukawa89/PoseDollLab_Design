"""Sample paths with finite-twist branch continuity; no continuous certificate.
Never interpolate two unrelated inverse-kinematic branch solutions blindly.
"""
from common import *
import layout_fullbody as layout
from layout_fullbody import fk
from carriers_swept import ASSEMBLY_POSE
from load_budget import declared_cases


def state(char,angles,hints):
 names=[m['id'] for m in layout.config(char)[1] if m['kind'] in ('tut','wide_tut')];counter=[0];original=layout.candidates
 def select(M,max_b=95):
  name=names[counter[0]];counter[0]+=1;q=original(M,max_b);hint=hints.get(name)
  if hint is None or not len(q):return q
  # Preserve the previous free twist exactly at the zero-bend singularity.
  if np.max(np.abs(M[:,2]-[0,0,1]))<1e-8:
   theta=np.rad2deg(np.arctan2(M[1,0],M[0,0]));psi=(theta-hint[0]+180)%360-180
   if abs(psi)<=170:q=np.r_[q,[[hint[0],0,0,psi]]]
  return q[[np.argmin(np.sum((q-np.array(hint))**2,axis=1))]]
 layout.candidates=select
 try:return layout.build(char,angles,geometry=False)
 finally:layout.candidates=original


def paths(char,max_semantic_step=5,max_raw_step=15):
 source=declared_cases(char);out=[];report=[]
 for name,target in source.items():
  if name=='assembly':continue
  axes=set(ASSEMBLY_POSE)|set(target);start={a:ASSEMBLY_POSE.get(a,0.) for a in axes};end={a:target.get(a,0.) for a in axes};steps=max(1,int(np.ceil(max(abs(end[a]-start[a]) for a in axes)/max_semantic_step)));hints={};previous=None;largest=0;bad=[]
  for i in range(steps+1):
   u=i/steps;angles={a:start[a]+u*(end[a]-start[a]) for a in axes};_,meta,states,f,pr=state(char,angles,hints);now={m['id']:m['angles_deg'] for m in states}
   if previous:
    jump=max(max(abs(np.array(now[k])-previous[k])) for k in now);largest=max(largest,float(jump))
    if jump>max_raw_step:bad.append({'sample':i,'raw_step_deg':float(jump)})
   if f:bad.append({'sample':i,'mapping_failures':f})
   hints=now;previous=now;T,_=fk(pr,angles);out.append((name+f'/{i:03}',meta,T))
  report.append({'target':name,'samples':steps+1,'maximum_raw_step_deg':largest,'issues':bad})
 return out,report

if __name__=='__main__':
 for char in ('quinn','manny'):
  bank,rows=paths(char);save('paths/'+char+'_kinematics.json',{'rows':rows,'samples':len(bank),'max_semantic_step_deg':5,'max_accepted_raw_step_deg':15,'continuous_motion_proof':False,'physical_tested':False,'source_sha256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py')]}});print('PATHS',char,len(bank),'discontinuous',[(r['target'],r['maximum_raw_step_deg']) for r in rows if r['issues']],flush=True)
