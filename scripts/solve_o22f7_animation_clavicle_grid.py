import json,numpy as np
from o22f7_animation import Build,WORK,put,arr
from build_revo22_assembly import b
x=Build();cache={};rows=[];solutions={}
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return b.g.move(cache[o['mesh']],x.mats[k])
def check(moving,fix,path,step=1):
 bounds={k:np.array(v.bounding_box()) for k,v in fix.items()};maximum=0;samples=0
 for a,c in zip(path,path[1:]):
  for t in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(np.array(c)-a)/step))+1)):
   p=x.direction(np.array(a)+(np.array(c)-a)*t);s=moving.translate(p);bb=np.array(s.bounding_box());samples+=1
   for k,v in fix.items():
    if np.any(np.minimum(bb[3:],bounds[k][3:])<=np.maximum(bb[:3],bounds[k][:3])+1e-6):continue
    vol=float((s^v).volume());maximum=max(maximum,vol)
    if vol>.02:return False,maximum,samples,arr(p),k
 return True,maximum,samples,None,None

import heapq,time
for st in [x.g['steps'][3],x.g['steps'][10]]:
 x.begin(st);mod=st['id'];key='frame/'+st['child'];moving=shape(key);fix={k:shape(k) for k in ['frame/'+st['parent'],mod+'/M3_nut',mod+'/M3_reaction_washer',mod+'/inner_M4_wide']};cache_free={};evaluations=0
 def free(p):
  global evaluations
  if p not in cache_free:
   ok,peak,n,where,other=check(moving,fix,[list(p),list(p)],1);cache_free[p]=ok;evaluations+=1
  return cache_free[p]
 start=(0.,0.,0.);heap=[(0,0,start)];cost={start:0};parent={start:None};found=None;count=0;started=time.time()
 while heap and count<6000:
  _,g,p=heapq.heappop(heap)
  if g!=cost[p]:continue
  count+=1
  if np.linalg.norm(p)>=70:found=p;break
  for axis in [2,0,1]:
   for sign in [1,-1]:
    q=list(p);q[axis]+=sign;q=tuple(q)
    if max(abs(v) for v in q)>75 or q[2]<-10:continue
    ng=g+1
    if ng>=cost.get(q,1e9) or not free(q):continue
    mid=tuple((np.array(q)+p)/2)
    if not free(mid):continue
    cost[q]=ng;parent[q]=p;heapq.heappush(heap,(ng*.12-np.linalg.norm(q),ng,q))
  if count%300==0:print(st['step'],count,evaluations,'radius',max(np.linalg.norm(v) for v in cost),'sec',round(time.time()-started),flush=True)
 if found:
  path=[];p=found
  while p is not None:path.append(list(p));p=parent[p]
  path=path[::-1];compressed=[path[0]]+[path[i] for i in range(1,len(path)-1) if not np.array_equal(np.array(path[i])-path[i-1],np.array(path[i+1])-path[i])]+[path[-1]];passed,peak,n,_,_=check(moving,fix,compressed,.25);solutions[key]={'path':compressed,'passed':passed,'peak':peak,'samples':n}
 print(st['step'],'finished',count,evaluations,solutions.get(key),flush=True);put(WORK/'clavicle_grid_paths.json',{'solutions':solutions,'search_nodes':count,'evaluations':evaluations})
