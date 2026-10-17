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

seq=json.loads((x.scene and __import__('o22f7_animation').OUT/'sequence.json').read_text('utf8'));solutions={}
for st in x.g['steps'][:-1]:
 x.begin(st)
 for r in [r for r in x.g['routes'] if r['step']==st['step']]:
  key=r['sensor_part_O20'].replace('sensor_PCB','magnet');a=next(a for a in seq['actions'] if x.idx[key] in a['new']);cap=r['magnet_mount'];moving=shape(key);fixed=shape(cap);world=(np.array(a['path'][0])-a['path'][-1]);local=np.linalg.solve(x.mount[:3,:3],world)
  for sign in [1,-1]:
   path=[[0,0,0],arr(local*sign)];passed,peak,n,where,other=check(moving,{cap:fixed},path,.5);row={'route':r['connector'],'part':key,'direction_sign':sign,'passed':passed,'peak':peak,'samples':n};rows.append(row)
   if passed:solutions[key]=sign;break
  if not passed or sign==-1:print(json.dumps(row),flush=True)
 put(WORK/'magnet_paths.json',{'solutions':solutions,'attempts':rows,'scope':'Magnet translation against its loose printed holder only, before adhesive or retaining screws.'})
print('magnet paths solved',len(solutions),flush=True)
