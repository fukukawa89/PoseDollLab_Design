from common import *
from layout_fullbody import config,fk,candidates,frame

def spheres(n):
 i=np.arange(n);z=1-2*(i+.5)/n;a=i*np.pi*(3-np.sqrt(5));r=np.sqrt(1-z*z);return np.c_[r*np.cos(a),r*np.sin(a),z]
def main():
 out=[]
 for side in ('l','r'):
  name='upperarm_'+side;pr,mm=config('quinn');m=next(m for m in mm if m['id']==name)
  cases=[{}]+[{name+'.'+a:v} for a,vs in [('flex',(-50,160)),('abduct',(-30,150)),('twist',(-90,90))] for v in vs]
  cases+=[{name+'.flex':f,name+'.abduct':a,name+'.twist':t} for f,a,t in itertools.product((-50,55,160),(-30,60,150),(-90,0,90))]
  mats=[]
  for a in cases:
   T,_=fk(pr,a);mats.append(T[m['parent']][:3,:3].T@T[m['child']][:3,:3])
  mats=np.array(mats);s=spheres(800);best=[]
  for fi in s:
   score=np.min(np.einsum('i,pij,vj->pv',fi,mats,s),axis=0);v=int(score.argmax());best.append((float(score[v]),fi,s[v]))
  best.sort(key=lambda x:x[0],reverse=True);print('MOUNT',side,'maxmin',best[0][0],flush=True)
  rows=[]
  for score,fi,vi in best[:5]:
   f0=frame(fi);v0=frame(vi)
   for a,b in itertools.product(range(0,360,45),repeat=2):
    F=f0@rot(2,a);V=v0@rot(2,b);qq=[candidates(F.T@M@V,120) for M in mats];fails=sum(not len(q) for q in qq)
    rows.append({'score':score,'F':F.tolist(),'V':V.tolist(),'failures':fails,'q':[q[np.argmin(np.sum(q*q*np.array([1,.1,.1,1]),axis=1))].tolist() if len(q) else None for q in qq]})
  rows.sort(key=lambda r:(r['failures'],-r['score']));out.append({'side':side,'cases':cases,'ranked':rows[:20]});save('shoulder_mount_search.json',{'results':out});print(side,[(r['failures'],r['score']) for r in rows[:4]],flush=True)
if __name__=='__main__':main()
