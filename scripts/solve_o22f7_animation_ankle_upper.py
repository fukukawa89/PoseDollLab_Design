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
 x.begin(st);mod=st['id'];moving=shape(mod+'/C15');fix={k:shape(k) for k in ['frame/'+st['parent'],'frame/'+st['child'],mod+'/C14']};found=False
 for h in [8,10,12,6]:
  if found:break
  for xx in [-15,-18,-12,-20,3]:
   if found:break
   for yy in [-70,70]:
    path=[[0,0,0],[0,0,h],[xx,0,h],[xx,yy,h]];passed,peak,n,where,other=check(moving,fix,path);row={'part':mod+'/C15','path':path,'passed':passed,'peak':peak,'samples':n,'obstacle':other,'where':where};rows.append(row);print(json.dumps(row),flush=True)
    if passed:solutions[mod+'/C15']=path;found=True;break
 put(WORK/'ankle_upper_path_search.json',{'solutions':solutions,'attempts':rows})
