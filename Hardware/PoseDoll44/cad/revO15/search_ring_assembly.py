"""Search rigid translation paths. Nominal sampled motion only, not compliance."""
from common import *
import core,heapq

def route(shape,obstacles,goal,limit=12000,step=1.):
 keys=list(obstacles);bb=np.array([s.bounding_box() for s in obstacles.values()]);sb=np.array(shape.bounding_box());cache={};calls=0
 def clear(pos):
  nonlocal calls
  key=tuple(np.round(pos,5))
  if key in cache:return cache[key]
  b=sb+np.tile(pos,2);ix=np.flatnonzero(np.all(np.minimum(b[3:],bb[:,3:])>np.maximum(b[:3],bb[:,:3])+1e-6,axis=1));q=shape.translate(pos);calls+=1
  ok=all((q^obstacles[keys[j]]).volume()<1e-4 for j in ix);cache[key]=ok;return ok
 start=(0,0,0);goal=np.array(goal);Q=[(np.linalg.norm(goal),start)];cost={start:0};prev={};moves=np.r_[np.eye(3),-np.eye(3)].astype(int);seen=set()
 if not clear(np.zeros(3)):return {'cause':'START_COLLISION'}
 while Q and len(seen)<limit:
  _,u=heapq.heappop(Q)
  if u in seen:continue
  seen.add(u);a=np.array(u)*step
  if np.linalg.norm(a-goal)<step+.01:
   path=[a.tolist()]
   while u in prev:u=prev[u];path.append((np.array(u)*step).tolist())
   return {'path':path[::-1],'expanded':len(seen),'collision_queries':calls}
  for mv in moves:
   vv=np.array(u)+mv;v=tuple(vv);g=cost[u]+1
   if any(abs(vv)>90) or g>=cost.get(v,1e30):continue
   b=vv*step
   if not clear(b) or not clear((a+b)/2):continue
   prev[v]=u;cost[v]=g;heapq.heappush(Q,(g+1.2*np.linalg.norm(b-goal)/step,v))
  if len(seen)%1000==0:print('expanded',len(seen),'frontier',len(Q),flush=True)
 return {'cause':'SEARCH_LIMIT_OR_NO_TRANSLATION_PATH','expanded':len(seen),'collision_queries':calls}

def main():
 p,o,s=core.make();old={k:from_tri(t) for k,t in np.load(core.G13/'printed_core/parts.npz').items()};results=[]
 for a in (0,25,-25):
  # C02 is installed after the lower fork and lower bearing half.
  obs={'C01':pose(p['C01'],rot(0,a))}
  for lab,shape in [('with_support',p['C14']),('original_ring',old['C14'])]:
   for goal in ([0,-60,-5],[0,60,-5]):
    print('TRY',a,lab,goal,flush=True);r=route(shape,obs,goal);results.append({'alpha':a,'shape':lab,'goal':goal,**r});save('ring_assembly_search.json',{'rows':results});print('RESULT',r if 'path' not in r else {k:v for k,v in r.items() if k!='path'},flush=True)
    if 'path' in r:break
   if 'path' in r and lab=='with_support':return
if __name__=='__main__':main()
