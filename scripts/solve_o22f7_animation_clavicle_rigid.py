"""Search a rigid insertion motion for the two integrated clavicle frames."""
from o22f7_animation import Build,WORK,put,arr
from build_revo22_assembly import b
import numpy as np,heapq,time,itertools,json
x=Build();solutions={};meshcache={}
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in meshcache:meshcache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return b.g.move(meshcache[o['mesh']],x.mats[k])
def local_transform(q):
 M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];return x.mount@M@np.linalg.inv(x.mount)
for st in [x.g['steps'][3],x.g['steps'][10]]:
 x.begin(st);key='frame/'+st['child'];moving=shape(key);fix={k:shape(k) for k in ['frame/'+st['parent'],st['id']+'/M3_nut',st['id']+'/M3_reaction_washer',st['id']+'/inner_M4_wide']};bounds={k:np.array(v.bounding_box()) for k,v in fix.items()};freecache={};evals=0;starttime=time.time()
 def free(q):
  global evals
  if q in freecache:return freecache[q]
  ss=b.g.move(moving,local_transform(q));bb=np.array(ss.bounding_box());valid=True
  for k,v in fix.items():
   if np.any(np.minimum(bb[3:],bounds[k][3:])<=np.maximum(bb[:3],bounds[k][:3])+1e-6):continue
   if float((ss^v).volume())>.02:valid=False;break
  freecache[q]=valid;evals+=1;return valid
 start=(0.,)*6;heap=[(0,0,start)];cost={start:0};parent={start:None};found=None;count=0
 while heap and count<5000:
  _,g,p=heapq.heappop(heap)
  if g!=cost[p]:continue
  count+=1
  if np.linalg.norm(p[:3])>=55:found=p;break
  if count%30==0 and np.linalg.norm(p[:3])>3:
   for ax in [2,0,1]:
    if found:break
    for sg in [1,-1]:
     end=list(p);end[ax]+=sg*80;end=tuple(end);points=[tuple(np.array(p)+(np.array(end)-p)*t) for t in np.linspace(0,1,81)]
     if all(free(q) for q in points):
      parent[end]=p;found=end;break
   if found:break
  for axis in [2,0,1,3,4,5]:
   for sign in [1,-1]:
    q=list(p);q[axis]+=sign*(.5 if axis<3 else 2);q=tuple(q);ng=g+1
    if max(abs(v) for v in q[:3])>60 or max(abs(v) for v in q[3:])>180:continue
    if ng>=cost.get(q,1e9) or not free(q):continue
    mid=tuple((np.array(q)+p)/2)
    if not free(mid):continue
    cost[q]=ng;parent[q]=p;priority=ng*.05-np.linalg.norm(q[:3])-.012*np.linalg.norm(q[3:]);heapq.heappush(heap,(priority,ng,q))
  if count%200==0:
   best=max(cost,key=lambda v:np.linalg.norm(v[:3]));bp=[];q=best
   while q is not None:bp.append(list(q));q=parent[q]
   put(WORK/(st['step']+'_rigid_search_progress.json'),{'nodes':count,'best_path':bp[::-1],'evaluations':evals})
   print(st['step'],'nodes',count,'evaluations',evals,'furthest',round(np.linalg.norm(best[:3]),2),'seconds',round(time.time()-starttime),flush=True)
 if found:
  path=[];p=found
  while p is not None:path.append(list(p));p=parent[p]
  path=path[::-1];compressed=[path[0]]+[path[i] for i in range(1,len(path)-1) if not np.array_equal(np.array(path[i])-path[i-1],np.array(path[i+1])-path[i])]+[path[-1]];solutions[key]={'pose_path_local':compressed,'nodes':count,'evaluations':evals,'scope':'Sampled rigid transforms against parent and installed inner hardware; printed tolerances are not simulated.'}
 print('RESULT',st['step'],solutions.get(key),flush=True);put(WORK/'clavicle_rigid_paths.json',{'solutions':solutions,'nodes':count,'evaluations':evals})

