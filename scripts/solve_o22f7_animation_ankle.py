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
for st in [x.g['steps'][19],x.g['steps'][23]]:
 x.begin(st);mod=st['id'];c01='frame/'+st['child'];c02='frame/'+st['parent']
 for part,fixkeys in [('C14',[c01]),('C15',[c01,c02,mod+'/C14'])]:
  moving=shape(mod+'/'+part);fix={k:shape(k) for k in fixkeys};candidates=[]
  if part=='C14':
   for h in [6,10,16,25]:
    for end in [[60,-8,h],[0,-70,h],[0,70,h],[-60,-8,h]]:candidates.append([[0,0,0],[0,0,-1],[0,-3,-1],[0,-3,h],end])
  else:
   for h in [8,12,20,35,60]:
    for end in [[70,0,h],[0,70,h],[0,-70,h],[-70,0,h]]:candidates.append([[0,0,0],[0,0,h],end])
  for path in candidates:
   passed,peak,n,where,other=check(moving,fix,path);r={'chapter':st['step'],'part':part,'path':path,'passed':passed,'peak':peak,'samples':n,'obstacle':other,'where':where};rows.append(r);print(json.dumps(r),flush=True)
   if passed:solutions[mod+'/'+part]=path;break
 put(WORK/'ankle_path_search.json',{'solutions':solutions,'attempts':rows})
