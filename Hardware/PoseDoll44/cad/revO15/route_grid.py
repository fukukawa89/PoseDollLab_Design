"""Shared world-grid visibility cache for repeated attachment searches."""
import numpy as np
import itertools,heapq

def route_grid(router,a,b):
 a=np.array(a);b=np.array(b)
 if router.clear(a,b):return [a,b]
 step=4.;sa=np.rint(a/step).astype(int);goal=np.rint(b/step).astype(int);lo=np.minimum(sa,goal)-12;hi=np.maximum(sa,goal)+12
 if not hasattr(router,'grid_free'):router.grid_free={};router.grid_edges={}
 def point(u):return np.array(u)*step
 def free(u):
  if u not in router.grid_free:router.grid_free[u]=router.clear(point(u),point(u))
  return router.grid_free[u]
 def edge(u,v):
  key=tuple(sorted((u,v)))
  if key not in router.grid_edges:router.grid_edges[key]=router.clear(point(u),point(v))
  return router.grid_edges[key]
 Q=[];cost={};prev={};visited=set();moves=np.r_[np.eye(3,dtype=int),-np.eye(3,dtype=int)]
 seeds=sorted((tuple(sa+np.array(d)) for d in itertools.product((-1,0,1),repeat=3)),key=lambda u:np.linalg.norm(point(u)-a))
 for u in seeds:
  if not free(u) or not router.clear(a,point(u)):continue
  g=float(np.linalg.norm(point(u)-a)/step);cost[u]=g;heapq.heappush(Q,(g+np.linalg.norm(point(u)-b)/step,u))
  if len(cost)>=6:break
 while Q and len(visited)<18000:
  _,u=heapq.heappop(Q)
  if u in visited:continue
  visited.add(u);pos=point(u)
  if np.linalg.norm(pos-b)<=8 and router.clear(pos,b):
   path=[b,pos]
   while u in prev:u=prev[u];path.append(point(u))
   path.append(a);path.reverse();simple=[path[0]];i=0
   while i<len(path)-1:
    j=len(path)-1
    while j>i+1 and not router.clear(path[i],path[j]):j-=1
    if not router.clear(path[i],path[j]):return None
    if np.linalg.norm(path[j]-simple[-1])>1e-6:simple.append(path[j])
    i=j
   return simple
  for mv in moves:
   vv=np.array(u)+mv
   if np.any(vv<lo) or np.any(vv>hi):continue
   v=tuple(vv);g=cost[u]+1
   if g>=cost.get(v,1e30) or not free(v) or not edge(u,v):continue
   cost[v]=g;prev[v]=u;heapq.heappush(Q,(g+np.linalg.norm(point(v)-b)/step,v))
 return None
