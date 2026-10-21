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

solutions={}
for st in x.g['steps'][:-1]:
 if st['kind']!='hinge':continue
 x.begin(st);mod=st['id'];key='frame/'+st['child'];moving=shape(key);fix={k:shape(k) for k in ['frame/'+st['parent'],mod+'/M3_nut',mod+'/M3_reaction_washer',mod+'/inner_M4_wide']};candidates=[[[0,0,0],[0,48,0]],[[0,0,0],[0,-48,0]],[[0,0,0],[48,0,0]],[[0,0,0],[-48,0,0]],[[0,0,0],[0,0,48]],[[0,0,0],[0,0,-48]]]
 for path in candidates:
  passed,peak,n,where,other=check(moving,fix,path,.75);row={'chapter':st['step'],'part':key,'path':path,'passed':passed,'peak':peak,'samples':n,'other':other};rows.append(row);print(json.dumps(row),flush=True)
  if passed:solutions[key]=path;break
 put(WORK/'hinge_paths.json',{'solutions':solutions,'attempts':rows,'scope':'Sampled translations of the full child frame against full parent frame and three installed internal stock items.'})
