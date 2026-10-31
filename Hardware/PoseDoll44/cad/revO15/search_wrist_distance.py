from common import *
from search_wrist import pair
from layout_fullbody import config
from model import fk
out=[]
for side in ('l','r'):
 prof,modules=config('quinn');T,A=fk(prof,{});ids=[f'hand_{side}.flex',f'hand_{side}.deviate'];mm=[next(m for m in modules if m['id']==i) for i in ids];FF=[np.array(m['F']) for m in mm];v=unit if False else None
 for distance in (28,31,34,37,40):
  d=(A[ids[1]]['origin']-A[ids[0]]['origin']);d=d/np.linalg.norm(d)*distance;opts=[]
  for p1,p2 in itertools.product(range(0,360,45),repeat=2):
   h,_,_,_=pair(0,0,*FF,d,p1,p2)
   if not h:opts.append([p1,p2])
  rows=[]
  for ph in opts:
   results=[]
   for q1,q2 in itertools.product((-65,0,65),(-25,0,35)):
    h,hh,_,_=pair(q1,q2,*FF,d,*ph);results.append({'q':[q1,q2],'hard':h,'integration':len(hh)-len(h)})
   rows.append({'phases':ph,'fail_samples':sum(bool(r['hard']) for r in results),'samples':results})
  rows.sort(key=lambda x:x['fail_samples']);out.append({'side':side,'distance_mm':distance,'neutral_clear':len(opts),'candidates':rows});save('wrist_distance_search.json',{'results':out,'continuous_motion_proved':False});print(side,distance,'neutral',len(opts),'best',[(r['phases'],r['fail_samples']) for r in rows[:6]],flush=True)
  if rows and rows[0]['fail_samples']==0:break
