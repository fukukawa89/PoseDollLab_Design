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

import itertools
for st in [x.g['steps'][3],x.g['steps'][10]]:
 x.begin(st);mod=st['id'];key='frame/'+st['child'];moving=shape(key);fix={k:shape(k) for k in ['frame/'+st['parent'],mod+'/M3_nut',mod+'/M3_reaction_washer',mod+'/inner_M4_wide']}
 candidates=[np.array(v,float)*48 for v in itertools.product([0,1,-1],repeat=3) if sum(z!=0 for z in v)>1]
 candidates += [np.array([xx,yy,zz],float)*48 for xx in [1,.5,-.5,-1] for yy in [1,.5,-.5,-1] for zz in [.2,.5,1,2]]
 for end in candidates:
  path=[[0,0,0],end.tolist()];passed,peak,n,where,other=check(moving,fix,path,.5);row={'part':key,'path':path,'passed':passed,'peak':peak,'samples':n};rows.append(row)
  if passed:solutions[key]=path;print(json.dumps(row),flush=True);break
 print(st['step'],'found',key in solutions,flush=True)
 put(WORK/'clavicle_paths.json',{'solutions':solutions,'attempts':rows})
