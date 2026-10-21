"""Generate positively connected printed rigid-body carriers around real modules.
Exact beam/obstacle intersections are retained. No geometry is hidden for routing.
"""
from common import *
from layout_fullbody import *
import heapq
from connected import adjacent_pairs
from route_retry import retry_pair
from route_grid import route_grid

VARIANT="carriers_swept"

ASSEMBLY_POSE={'upperarm_l.abduct':30,'upperarm_r.abduct':30,'thigh_l.abduct':8,'thigh_r.abduct':8}

def anchors(states,meta):
 out={}
 for m in states:
  kind=m['kind'];q=m['angles_deg'];W=np.array(m['world_mount']);O=np.array(m['origin_mm']);n=m['id']
  if kind in ('tut','wide_tut'):
   fs=tut.frames(q);e=7.5 if kind=='wide_tut' else 1.5;choices=[('P_case_minus',[0,-13.4,-30.9-e],[0,-1,0]),('D_case_minus',[0,13.4,37.9],[0,1,0])]
  elif kind=='three_axis':
   fs=three_axis.frames(q);choices=[('P_case_minus',[0,-13.4,-38.4],[0,-1,0]),('C02',[0,5,30],[0,0,1])]
  elif kind in ('core','clavicle_core','ankle_core'):
   a,b=q;fs={'C02':np.eye(3),'ring':rot(1,-b),'C01':rot(1,-b)@rot(0,a)};choices=[('C02',[0,5,30],[0,0,1]),('C01',[0,7.5,-19.5],[0,0,-1])]
  else:
   fs={'parent':np.eye(3),'child':rot(2,q[0])};choices=[('base_sensor_half',[0,-8,-8],[0,-1,0]),('lever_cup',[12.5,0,2.5],[1,0,0])]
  for k,pt,v in choices:
   pid=n+'/'+k;M=W@fs[meta[pid]['owner']];body=meta[pid]['body'];alternatives=[(pt,v)]
   if k in ('P_case_minus','D_case_minus'):
    sg=-1 if k.startswith('P') else 1
    for xx in (-13.7,13.7):alternatives.append(([xx,sg*4.5,pt[2]],[xx/14.42,sg*4.5/14.42,0]))
   if k in ('P_case_minus','D_case_minus'):
    sg=-1 if k.startswith('P') else 1
    for deg in (45,135,25,155,65,115,90):
     a=np.deg2rad(deg);v=[np.cos(a),sg*np.sin(a),0]
     alternatives.append(([13.4*v[0],13.4*v[1],pt[2]],v))
   if k in ('P_case_minus','D_case_minus'):
    sg=-1 if k.startswith('P') else 1
    for dz in (0,-.5,.5,-1,1,-2,2):
     for rr in (13.4,14.0,14.5):
      for deg in (90,70,110,50,130,30,150,10,170):
       a=np.deg2rad(deg);v=np.array([np.cos(a),sg*np.sin(a),0.]);at=[rr*v[0],rr*v[1],pt[2]+dz]
       for tilt in (0,-.75,.75,-1.5,1.5):
        vv=v+np.array([0,0,tilt]);alternatives.append((at,vv/np.linalg.norm(vv)))
   if k=='C02':
    for z in (30,27,33,24):
     for sg in (-1,1):
      for y in (0,-5,5):alternatives.append(([sg*10.3,y,z],[sg,0,0]))
      for x in (0,-5,5):alternatives.append(([x,sg*10.3,z],[0,sg,0]))
    for x in (0,-6,6):
     for y in (0,-6,6):alternatives.append(([x,y,33],[0,0,1]))
   if k=='base_sensor_half':
    for x in (0,-5,5,-9,9):
     alternatives.append(([x,-8,-8],[0,-1,0]));alternatives.append(([x,-5,-9.5],[0,0,-1]))
    for sg in (-1,1):alternatives.append(([sg*12.5,-5,-7.5],[sg,0,0]))
   if k=='base_sensor_half':
    for x in (0,-4,4,-8,8,-11,11):
     for z in (-11.5,-12.5):alternatives.append(([x,-4.5,z],[0,0,-1]))
    for x in (0,-4,4,-8,8):
     for z in (-5,-8):alternatives.append(([x,-10.3,z],[0,-1,0]))
   if k=='lever_cup':
    alternatives += [([10.5,4,2.5],[0,1,0]),([10.5,-4,2.5],[0,-1,0])]
    for z in (3,6,8):
     for deg in (0,45,90,135,180,225,270,315,22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5):
      a=np.deg2rad(deg);v=np.array([np.cos(a),np.sin(a),0.]);at=[12.5*v[0],12.5*v[1],z]
      for tilt in (0,-.75,.75):
       vv=v+np.array([0,0,tilt]);alternatives.append((at,vv/np.linalg.norm(vv)))
    for x in (11,13,15):alternatives.append(([x,0,.5],[0,0,-1]))
   out.setdefault(body,[]).append({'part':pid,'point':M@pt+O,'normal':M@v,'module':n,'alternatives':[(M@np.array(ap)+O,M@np.array(av)) for ap,av in alternatives]})
 return out

class Router:
 def __init__(self,obstacles,radius=5.0):
  self.obs=obstacles;self.keys=list(obstacles);self.bb=np.array([v.bounding_box() for v in obstacles.values()]);self.r=radius;self.root=min(3.6,radius);self.calls=0;self.stock_voids=[]
 def relieve(self,s,guard=False):
  bb=np.array(s.bounding_box())
  for bounds,actual,margin in self.stock_voids:
   if np.all(np.minimum(bb[3:],bounds[3:])>np.maximum(bb[:3],bounds[:3])):s-=margin if guard else actual
  return s
 def clear(self,a,b):
  a=np.asarray(a);b=np.asarray(b);lo=np.minimum(a,b)-self.r-.25;hi=np.maximum(a,b)+self.r+.25;idx=np.flatnonzero(np.all((self.bb[:,:3]<hi)&(self.bb[:,3:]>lo),axis=1))
  if not len(idx):return True
  if np.linalg.norm(b-a)<1e-7:s=md.Manifold.sphere(self.r+.25,16).translate(a)
  else:s=beam(a,b,self.r+.25)+md.Manifold.sphere(self.r+.25,16).translate(a)+md.Manifold.sphere(self.r+.25,16).translate(b)
  self.calls+=1
  s=self.relieve(s,guard=True)
  if solid_count(s)!=1:return False
  return all((s^self.obs[self.keys[i]]).volume()<1e-4 for i in idx)
 def clear_shape(self,s):
  bb=np.array(s.bounding_box());idx=np.flatnonzero(np.all((self.bb[:,:3]<bb[3:])&(self.bb[:,3:]>bb[:3]),axis=1));self.calls+=1
  s=self.relieve(s,guard=True)
  if solid_count(s)!=1:return False
  return all((s^self.obs[self.keys[i]]).volume()<1e-4 for i in idx)
 def escape(self,a,n,anchor=None):
  a=np.array(a);n=np.array(n)
  if not self.clear_shape(md.Manifold.sphere(self.root+.25,24).translate(a)):return None
  directions=[n]
  for d in itertools.product((-.7,0,.7),repeat=3):
   v=n+np.array(d)
   if np.linalg.norm(v)<.1 or np.dot(v,n)<.1:continue
   v=v/np.linalg.norm(v)
   if np.linalg.norm(v-n)>.1:directions.append(v)
  for direction in directions:
   for length in ((5,8,12,16,20) if self.r<=3 else (8,12,16,20,6)):
    b=a+direction*length;s=md.Manifold.batch_hull([md.Manifold.sphere(self.root+.25,24).translate(a),md.Manifold.sphere(self.r+.25,24).translate(b)])
    if self.clear_shape(s):
     actual=self.relieve(md.Manifold.batch_hull([md.Manifold.sphere(self.root,24).translate(a),md.Manifold.sphere(self.r,24).translate(b)]))
     if solid_count(actual)!=1 or anchor is not None and (actual^anchor).volume()<8:continue
     return [a,b]
  return None
 def path(self,a,b):return route_grid(self,a,b)

def motion_bank(char,overrides=None):
 poses={'assembly':ASSEMBLY_POSE,**read(H/'mechanical_manifest/revO_pose_cases.json')['cases']}
 for label,ang in enumerate(read(OUT/'serial_clavicle_bilateral_search.json')['cases']):
  poses['bilateral_clavicle_'+str(label)]=ang
 prof,_=config(char)
 for n in prof['nodes']:
  aid=n.get('axis_id')
  if not aid or aid.startswith('pelvis.'):continue
  axis=prof['axes'][aid] if isinstance(prof['axes'],dict) else next(a for a in prof['axes'] if a['id']==aid)
  for i,v in enumerate(axis['limits_rad']):poses[f'{aid}.{i}']={aid:float(np.rad2deg(v))}
 bank=[];seen=set()
 for name,ang in poses.items():
  key=tuple(sorted(ang.items()))
  if key in seen:continue
  seen.add(key);_,m,st,f,pr=build(char,ang,overrides=overrides,geometry=False)
  if f:raise ValueError((name,f))
  T,_=fk(pr,ang);bank.append((name,m,T))
 # Protect physical transit states as well as endpoint poses. Finer final audits
 # remain separate; a 15-degree construction sample is not continuous proof.
 if overrides is None:
  from raw_paths import paths
  for label,m,T,detail in paths(char,step=15):bank.append(('raw/'+label,m,T))
 return bank

def swept_obstacles(body,ids,related,pp,meta,T,bank,routes,endpoint_associations):
 # Static non-neighbours remain obstacles in the build pose. Adjacent modules
 # and their current carriers are swept through every recorded sample in this
 # body's coordinate frame. No contact finding is waived in the final audit.
 # A retained endpoint moves with its complete future rigid frame. Include
 # every original endpoint of an associated frame, even when that endpoint
 # originated in a different neighboring module.
 sweep={k:bool(endpoint_associations.get(k,{meta[k]['module']})&related) for k in pp}
 obs={k:v for k,v in pp.items() if k not in ids and not sweep[k]}
 mats={};samples={};base={};kinds={m['id']:m['kind'] for m in config(CHAR)[1]}
 for k in pp:
  if k in ids or not sweep[k]:continue
  group,local=k.split('/',1);shape=libraries()[kinds[group]][0][local]
  if kinds[group]=='hinge' and local=='lever_cup':shape=shape^box([-50,-50,-50],[14,50,50])
  base[k]=shape;samples[k]=set()
 for name,m,t in bank:
  B=T[body]@np.linalg.inv(t[body])
  for k,shape in base.items():
   M=B@m[k]['transform'];key=tuple(np.round(M,7).ravel())
   if key in samples[k]:continue
   samples[k].add(key);obs[k+'@'+name]=pose(shape,M[:3,:3],M[:3,3])
  for other,(shape,mods) in routes.items():
   k='connections/'+other
   if not any(x in related for x in mods):
    if name=='assembly':obs[k]=shape
    continue
   M=B@t[other]@np.linalg.inv(T[other]);key=tuple(np.round(M,7).ravel())
   if key in mats.setdefault(k,set()):continue
   mats[k].add(key);obs[k+'@'+name]=pose(shape,M[:3,:3],M[:3,3])
 return obs

CHAR='quinn'
def make(char):
 global CHAR
 CHAR=char;inputs={str(p):sha(p) for p in [*[Path(__file__).with_name(x) for x in ('carriers_swept.py','raw_paths.py','layout_fullbody.py','common.py','connected.py','carriers.py','route_retry.py','route_grid.py','tut.py','three_axis.py')],H/'mechanical_manifest/revO_pose_cases.json',G3/f'layouts/{char}/anatomy_profile.json',OUT/'serial_clavicle_bilateral_search.json',*OUT.glob('*_parts.npz'),*OUT.glob('*_build.json')]}
 pp,meta,states,fail,prof=build(char,ASSEMBLY_POSE);T,_=fk(prof,ASSEMBLY_POSE);aa=anchors(states,meta);frames={};records=[];added_routes={};bank=motion_bank(char);adj=adjacent_pairs(char)
 endpoint_associations={e['part']:{meta[v['part']]['module'] for v in ends} for ends in aa.values() for e in ends}
 print('MOTION BANK',len(bank),flush=True)
 for body,ends in reversed(list(aa.items())):
  ids=[e['part'] for e in ends];pockets=[];ownmods={meta[k]['module'] for k in ids};related=set(ownmods)
  for pair in adj:
   if pair&ownmods:related.update(pair)
  for k in ids:
   for sk,v in pp.items():
    if meta[sk]['sku'] in (None,'PCBA_INCLUDED') or meta[sk]['body']!=body or meta[sk]['module']==meta[k]['module']:continue
    overlap=float((pp[k]^v).volume())
    if overlap<=1e-4:continue
    cut=v
    for axis in range(3):
     for sg in (-1,1):cut+=v.translate(np.eye(3)[axis]*sg*.2)
    old=float(pp[k].volume());pp[k]-=cut;pockets.append({'part':k,'stock':sk,'overlap_before_mm3':overlap,'removed_mm3':old-float(pp[k].volume())})
  obs=swept_obstacles(body,ids,related,pp,meta,T,bank,added_routes,endpoint_associations);router=Router(obs,radius=2.6 if body.endswith('.flex_frame') else 4.0 if body.endswith('.protract_frame') or body.startswith('elbow_') else 5.0);esc=[];issues=[]
  # A mounting neck can have a real clearance pocket around a fixed screw.
  # Remove material from the new print only. Moving hardware stays an obstacle.
  for sk,v in pp.items():
   if meta[sk]['body']!=body or not (meta[sk]['sku'] or '').startswith(('SCREW_','NUT_')):continue
   actual=md.Manifold.batch_hull([v.translate(np.array(d)*.5) for d in itertools.product((-1,1),repeat=3)])
   margin=md.Manifold.batch_hull([v.translate(np.array(d)*.25) for d in itertools.product((-1,1),repeat=3)])
   router.stock_voids.append((np.array(actual.bounding_box()),actual,margin))
  print('ROUTING',body,'obstacles',len(obs),flush=True)
  for e in ends:
   path=None;overlap=0.
   for point,normal in e['alternatives']:
    overlap=float((pp[e['part']]^md.Manifold.sphere(router.root,16).translate(point)).volume());path=router.escape(point,normal,pp[e['part']]) if overlap>1 else None
    if path is not None:e['point']=point;e['normal']=normal;break
   if path is None:issues.append({'cause':'PORT_BLOCKED_OR_NOT_ANCHORED','part':e['part'],'anchor_overlap_mm3':overlap})
   esc.append(path)
  spans=[]
  if not issues and len(ends)>1:
   connected={0}
   while len(connected)<len(ends):
    dist,i,j=min((np.linalg.norm(esc[i][-1]-esc[j][-1]),i,j) for i in connected for j in range(len(ends)) if j not in connected)
    route=router.path(esc[i][-1],esc[j][-1])
    if route is None:route=retry_pair(router,ends,esc,pp,i,j,len(connected)==1)
    if route is None:issues.append({'cause':'NO_CLEAR_ROUTE','parts':[ids[i],ids[j]]});break
    spans.append(route);connected.add(j)
  s=md.Manifold()
  for k in ids:s+=pp[k]
  route_solid=md.Manifold()
  if not issues:
   for a,b in esc:route_solid+=md.Manifold.batch_hull([md.Manifold.sphere(router.root,24).translate(a),md.Manifold.sphere(router.r,24).translate(b)])
   for points in spans:
    for a,b in zip(points,points[1:]):route_solid+=beam(a,b,router.r)+md.Manifold.sphere(router.r,24).translate(a)+md.Manifold.sphere(router.r,24).translate(b)
   uncut_volume=float(route_solid.volume());route_solid=router.relieve(route_solid);s+=route_solid;added_routes[body]=(route_solid,ownmods)
  M=T[body];local=pose(s,M[:3,:3].T,-M[:3,:3].T@M[:3,3]);frames[body]=local
  rec={'body':body,'replaces':ids,'mesh':mesh_record(s),'issues':issues,'ports':[{'part':e['part'],'point_mm':e['point'].tolist(),'normal':e['normal'].tolist()} for e in ends],'paths_world_mm':[[v.tolist() for v in path] for path in esc+spans if path is not None],'collision_queries':router.calls,'stock_pockets':pockets,'main_rod_diameter_mm':router.r*2,'root_radius_mm':router.root,'service_pocket_removed_mm3':uncut_volume-float(route_solid.volume()) if not issues else None,'swept_obstacles':len(obs)}
  if rec['mesh']['components']!=1 and not issues:issues.append({'cause':'RIGID_FRAME_DISCONNECTED','positive_components':rec['mesh']['components']})
  records.append(rec)
  save(f'{VARIANT}/{char}_routing.json',{'status':'ROUTING_INCOMPLETE','assembly_pose':ASSEMBLY_POSE,'mapping_failures':fail,'frames':records});print('CARRIER',char,body,len(ends),'components',rec['mesh']['components'],'issues',issues,'queries',router.calls,flush=True)
 if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('source/input changed while routing')
 tmp=OUT/f'{VARIANT}/{char}_parts.next.npz';np.savez_compressed(tmp,**{k:tri(v) for k,v in frames.items()});tmp.replace(OUT/f'{VARIANT}/{char}_parts.npz')
 save(f'{VARIANT}/{char}_routing.json',{'status':'ROUTING_GENERATED' if not any(r['issues'] for r in records) else 'ROUTING_BLOCKED','assembly_pose':ASSEMBLY_POSE,'mapping_failures':fail,'frames':records,'input_sha256':inputs,'mesh_sha256':sha(OUT/f'{VARIANT}/{char}_parts.npz'),'motion_samples':[n for n,_,_ in bank],'scope':'Sampled sweeps only; not continuous proof.'})
 return frames,records

if __name__=='__main__':make(sys.argv[1] if len(sys.argv)>1 else 'quinn')
