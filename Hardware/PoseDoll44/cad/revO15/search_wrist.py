"""Search physical clocking of a pair without changing either rotation axis.
A same-body print/print overlap is only an integration candidate, never a pass.
"""
from common import *
from layout_fullbody import libraries,config,frame
from model import fk

def pair(theta1,theta2,F1,F2,d,phase1,phase2):
 hp,ho,hs=libraries()['hinge'];p={};body={};sk={};axis=F1[:,2];Q=rot(axis,theta1)
 for j,F,pos,q in [(0,F1@rot(2,phase1),np.zeros(3),theta1),(1,Q@F2@rot(2,phase2),Q@d,theta2)]:
  for k,v in hp.items():
   if k=='lever_cup':v=v^box([-50,-50,-50],[14,50,50])
   owner=ho[k];p[str(j)+'/'+k]=pose(v,F@(rot(2,q) if owner=='child' else np.eye(3)),pos);body[str(j)+'/'+k]=j+(owner=='child');sk[str(j)+'/'+k]=hs[k]
 hh=[h for h in hits(p) if h['pair'][0][0]!=h['pair'][1][0]]
 hard=[h for h in hh if body[h['pair'][0]]!=body[h['pair'][1]] or all(sk[k] is not None for k in h['pair'])]
 return hard,hh,p,body

def main():
 out=[]
 for side in ('l','r'):
  prof,modules=config('quinn');T,A=fk(prof,{});ids=[f'hand_{side}.flex',f'hand_{side}.deviate'];mm=[next(m for m in modules if m['id']==i) for i in ids];FF=[np.array(m['F']) for m in mm];d=A[ids[1]]['origin']-A[ids[0]]['origin']
  options=[]
  for p1,p2 in itertools.product(range(0,360,45),repeat=2):
   hard,hh,_,_=pair(0,0,*FF,d,p1,p2);options.append({'phase_deg':[p1,p2],'neutral_hard_count':len(hard),'neutral_hard_volume':sum(h['overlap_mm3'] for h in hard),'neutral_integration_count':len(hh)-len(hard)})
  options.sort(key=lambda x:x['neutral_hard_volume']);best=[]
  for opt in options[:12]:
   mm=[]
   for q1,q2 in itertools.product((-65,0,65),(-25,0,35)):
    hard,hh,_,_=pair(q1,q2,*FF,d,*opt['phase_deg']);mm.append({'angles_deg':[q1,q2],'hard_findings':hard,'same_body_integration_count':len(hh)-len(hard)})
   opt['samples']=mm;opt['fail_samples']=sum(bool(r['hard_findings']) for r in mm);opt['worst_volume']=max(sum(h['overlap_mm3'] for h in r['hard_findings']) for r in mm);best.append(opt)
  best.sort(key=lambda x:(x['fail_samples'],x['worst_volume']));out.append({'side':side,'center_offset_mm':d.tolist(),'candidates':best,'all_neutral_options':options});save('wrist_clocking_search.json',{'results':out,'continuous_clearance_proved':False});print(side,[(b['phase_deg'],b['fail_samples'],round(b['worst_volume'],3)) for b in best],flush=True)
if __name__=='__main__':main()
