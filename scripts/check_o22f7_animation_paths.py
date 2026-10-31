"""Targeted sampled checks of the two non-straight core assembly moves."""
import json,numpy as np
from o22f7_animation import Build,OUT,WORK,put,arr
from build_revo22_assembly import b
x=Build();seq=json.loads((OUT/'sequence.json').read_text('utf8'));report=[];cache={}
def solid(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return b.g.move(cache[o['mesh']],x.mats[k])
for st in x.g['steps'][:-1]:
 if st['kind']=='hinge':continue
 x.begin(st);mod=st['id'];ankle=st['kind']=='ankle_core';c01='frame/'+st['child'] if ankle else mod+'/C01';c02='frame/'+st['parent'] if ankle else 'frame/'+st['child'] if st['kind']=='three_axis' else mod+'/C02'
 for part,fixed in [('C14',[c01]),('C15',[c01,c02,mod+'/C14'])]:
  key=mod+'/'+part;a=next(a for a in seq['actions'] if x.idx[key] in a['new']);offset=np.array(a['path'][-1]);path=np.array(a['path'])-offset;moving=solid(key);fix={k:solid(k) for k in fixed};boxes={k:np.array(v.bounding_box()) for k,v in fix.items()};maximum=0;hits=[];samples=0
  for aa,bb in zip(path,path[1:]):
   for t in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(bb-aa)/1.0))+1)):
    p=aa+(bb-aa)*t;ss=moving.translate(p);box=np.array(ss.bounding_box());samples+=1
    for k,v in fix.items():
     if np.any(np.minimum(box[3:],boxes[k][3:])<=np.maximum(box[:3],boxes[k][:3])+1e-5):continue
     vol=float((ss^v).volume());maximum=max(maximum,vol)
     if vol>.02 and len(hits)<3:hits.append({'other':k,'translation':arr(p),'volume':vol})
  row={'chapter':st['step'],'part':key,'samples':samples,'peak_mm3':maximum,'findings':hits};report.append(row);print(json.dumps(row),flush=True);put(WORK/'core_paths.json',{'scope':'1 mm sampled nominal paths against the explicitly listed fork/core parts, not whole assembly or print tolerances.','rows':report})
