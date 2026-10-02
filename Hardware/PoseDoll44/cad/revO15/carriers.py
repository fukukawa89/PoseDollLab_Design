"""Generate positively connected printed rigid-body carriers around real modules.
Exact beam/obstacle intersections are retained. No geometry is hidden for routing.
"""
from common import *
from layout_fullbody import *
import heapq

ASSEMBLY_POSE={'upperarm_l.abduct':30,'upperarm_r.abduct':30,'thigh_l.abduct':8,'thigh_r.abduct':8}

def anchors(states,meta):
 out={}
 for m in states:
  kind=m['kind'];q=m['angles_deg'];W=np.array(m['world_mount']);O=np.array(m['origin_mm']);n=m['id']
  if kind in ('tut','wide_tut'):
   fs=tut.frames(q);e=7.5 if kind=='wide_tut' else 1.5;choices=[('P_case_minus',[0,-11.4,-21.8-e],[0,-1,0]),('D_case_minus',[0,11.4,28.8],[0,1,0])]
  elif kind=='three_axis':
   fs=three_axis.frames(q);choices=[('P_case_minus',[0,-11.4,-29.3],[0,-1,0]),('C02',[0,5,30],[0,0,1])]
  elif kind in ('core','clavicle_core','ankle_core'):
   a,b=q;fs={'C02':np.eye(3),'ring':rot(1,-b),'C01':rot(1,-b)@rot(0,a)};choices=[('C02',[0,5,30],[0,0,1]),('C01',[0,7.5,-19.5],[0,0,-1])]
  else:
   fs={'parent':np.eye(3),'child':rot(2,q[0])};choices=[('base_sensor_half',[0,-8,-8],[0,-1,0]),('lever_cup',[12.5,0,2.5],[1,0,0])]
  for k,pt,v in choices:
   pid=n+'/'+k;M=W@fs[meta[pid]['owner']];body=meta[pid]['body'];alternatives=[(pt,v)]
   if k in ('P_case_minus','D_case_minus'):
    sg=-1 if k.startswith('P') else 1
    for xx in (-13.7,13.7):alternatives.append(([xx,sg*4.5,pt[2]+sg*1.4],[xx/14.42,sg*4.5/14.42,0]))
   if k=='lever_cup':alternatives += [([10.5,4,2.5],[0,1,0]),([10.5,-4,2.5],[0,-1,0])]
   out.setdefault(body,[]).append({'part':pid,'point':M@pt+O,'normal':M@v,'module':n,'alternatives':[(M@np.array(ap)+O,M@np.array(av)) for ap,av in alternatives]})
 return out

class Router:
 def __init__(self,obstacles,radius=5.0):
  self.obs=obstacles;self.keys=list(obstacles);self.bb=np.array([v.bounding_box() for v in obstacles.values()]);self.r=radius;self.calls=0
 def clear(self,a,b):
  a=np.asarray(a);b=np.asarray(b);lo=np.minimum(a,b)-self.r-.25;hi=np.maximum(a,b)+self.r+.25;idx=np.flatnonzero(np.all((self.bb[:,:3]<hi)&(self.bb[:,3:]>lo),axis=1))
  if not len(idx):return True
  if np.linalg.norm(b-a)<1e-7:s=md.Manifold.sphere(self.r+.25,16).translate(a)
  else:s=beam(a,b,self.r+.25)+md.Manifold.sphere(self.r+.25,16).translate(a)+md.Manifold.sphere(self.r+.25,16).translate(b)
  self.calls+=1
  return all((s^self.obs[self.keys[i]]).volume()<1e-4 for i in idx)
 def clear_shape(self,s):
  bb=np.array(s.bounding_box());idx=np.flatnonzero(np.all((self.bb[:,:3]<bb[3:])&(self.bb[:,3:]>bb[:3]),axis=1));self.calls+=1
  return all((s^self.obs[self.keys[i]]).volume()<1e-4 for i in idx)
 def escape(self,a,n):
  a=np.array(a);n=np.array(n)
  for length in ((5,8,12,16,20) if self.r<=3 else (8,12,16,20)):
   b=a+n*length;s=md.Manifold.batch_hull([md.Manifold.sphere(2.85,24).translate(a),md.Manifold.sphere(self.r+.25,24).translate(b)])
   if self.clear_shape(s):return [a,b]
  return None
 def path(self,a,b):
  a=np.array(a);b=np.array(b)
  if self.clear(a,b):return [a,b]
  step=4.;end=np.rint((b-a)/step).astype(int);lo=np.minimum(0,end)-8;hi=np.maximum(0,end)+8;start=(0,0,0);goal=tuple(end);memo={};cost={start:0.};prev={};Q=[(float(np.linalg.norm(end)),start)];moves=np.r_[np.eye(3,dtype=int),-np.eye(3,dtype=int)]
  while Q and len(cost)<18000:
   _,u=heapq.heappop(Q);pos=a+np.array(u)*step
   if u==goal and self.clear(pos,b):
    path=[b,pos]
    while u in prev:u=prev[u];path.append(a+np.array(u)*step)
    path.reverse();simple=[path[0]];i=0
    while i<len(path)-1:
     j=len(path)-1
     while j>i+1 and not self.clear(path[i],path[j]):j-=1
     if not self.clear(path[i],path[j]):return None
     simple.append(path[j]);i=j
    return simple
   for mv in moves:
    vv=np.array(u)+mv
    if np.any(vv<lo) or np.any(vv>hi):continue
    v=tuple(vv);g=cost[u]+1
    if g>=cost.get(v,1e30):continue
    if v not in memo:memo[v]=self.clear(a+vv*step,a+vv*step)
    if not memo[v]:continue
    if not self.clear(pos,a+vv*step):continue
    cost[v]=g;prev[v]=u;heapq.heappush(Q,(g+float(np.linalg.norm(vv-end)),v))
  return None

def make(char):
 pp,meta,states,fail,prof=build(char,ASSEMBLY_POSE);T,_=fk(prof,ASSEMBLY_POSE);aa=anchors(states,meta);frames={};records=[];added_routes={}
 for body,ends in reversed(list(aa.items())):
  ids=[e['part'] for e in ends];pockets=[]
  for k in ids:
   for sk,v in pp.items():
    if meta[sk]['sku'] in (None,'PCBA_INCLUDED') or meta[sk]['body']!=body or meta[sk]['module']==meta[k]['module']:continue
    overlap=float((pp[k]^v).volume())
    if overlap<=1e-4:continue
    cut=v
    for axis in range(3):
     for sg in (-1,1):cut+=v.translate(np.eye(3)[axis]*sg*.2)
    old=float(pp[k].volume());pp[k]-=cut;pockets.append({'part':k,'stock':sk,'overlap_before_mm3':overlap,'removed_mm3':old-float(pp[k].volume())})
  obs={k:v for k,v in pp.items() if k not in ids};obs.update(added_routes);router=Router(obs,radius=2.6 if body.endswith('.flex_frame') else 5.0);esc=[];issues=[]
  for e in ends:
   path=None;overlap=0.
   for point,normal in e['alternatives']:
    overlap=float((pp[e['part']]^md.Manifold.sphere(2.6,16).translate(point)).volume());path=router.escape(point,normal) if overlap>1 else None
    if path is not None:e['point']=point;e['normal']=normal;break
   if path is None:issues.append({'cause':'PORT_BLOCKED_OR_NOT_ANCHORED','part':e['part'],'anchor_overlap_mm3':overlap})
   esc.append(path)
  spans=[]
  if not issues and len(ends)>1:
   connected={0}
   while len(connected)<len(ends):
    dist,i,j=min((np.linalg.norm(esc[i][-1]-esc[j][-1]),i,j) for i in connected for j in range(len(ends)) if j not in connected)
    route=router.path(esc[i][-1],esc[j][-1])
    if route is None:issues.append({'cause':'NO_CLEAR_ROUTE','parts':[ids[i],ids[j]]});break
    spans.append(route);connected.add(j)
  s=md.Manifold()
  for k in ids:s+=pp[k]
  route_solid=md.Manifold()
  if not issues:
   for a,b in esc:route_solid+=md.Manifold.batch_hull([md.Manifold.sphere(2.6,24).translate(a),md.Manifold.sphere(router.r,24).translate(b)])
   for points in spans:
    for a,b in zip(points,points[1:]):route_solid+=beam(a,b,router.r)+md.Manifold.sphere(router.r,24).translate(a)+md.Manifold.sphere(router.r,24).translate(b)
   s+=route_solid;added_routes['connections/'+body]=route_solid
  M=T[body];local=pose(s,M[:3,:3].T,-M[:3,:3].T@M[:3,3]);frames[body]=local
  rec={'body':body,'replaces':ids,'mesh':mesh_record(s),'issues':issues,'ports':[{'part':e['part'],'point_mm':e['point'].tolist(),'normal':e['normal'].tolist()} for e in ends],'paths_world_mm':[[v.tolist() for v in path] for path in esc+spans if path is not None],'collision_queries':router.calls,'stock_pockets':pockets,'main_rod_diameter_mm':router.r*2,'root_radius_mm':2.6};records.append(rec)
  save(f'carriers/{char}_routing.json',{'status':'ROUTING_EXPERIMENT','assembly_pose':ASSEMBLY_POSE,'mapping_failures':fail,'frames':records});print('CARRIER',char,body,len(ends),'components',rec['mesh']['components'],'issues',issues,'queries',router.calls,flush=True)
 tmp=OUT/f'carriers/{char}_parts.next.npz';np.savez_compressed(tmp,**{k:tri(v) for k,v in frames.items()});tmp.replace(OUT/f'carriers/{char}_parts.npz')
 save(f'carriers/{char}_routing.json',{'status':'ROUTING_GENERATED','assembly_pose':ASSEMBLY_POSE,'mapping_failures':fail,'frames':records,'source_sha256':{name:sha(Path(__file__).with_name(name)) for name in ('carriers.py','layout_fullbody.py')},'mesh_sha256':sha(OUT/f'carriers/{char}_parts.npz')})
 return frames,records

if __name__=='__main__':make(sys.argv[1] if len(sys.argv)>1 else 'quinn')
