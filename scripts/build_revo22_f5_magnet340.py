"""Reserve magnetic-cap fasteners and their complete radial insertion corridors."""
import json,numpy as np
from search_revo22_f5_orientation268 import O,OLD,put
from build_revo22_fins import solid,vf,union,md
import repair_revo22_f4_guarded_chamfer as ctx

def run(pid):
 dst=O/'guards_magnet';dst.mkdir(exist_ok=True);p=dst/f'{pid}.npz'
 if p.exists():return
 n=np.load(OLD/'parts'/f'{pid}.npz');d=json.loads((OLD/'design'/f'{pid}.json').read_text());body=solid(n['v'],n['f']);parts,key,T=ctx.context(d,pid);out=[];rows=[]
 for k,part in parts.items():
  sku=ctx.CACHE[1][k].get('sku')or''
  if 'magnet'not in k or not any(s in sku for s in ['NUT_','SCREW_']):continue
  q=part.transform(T[:3,:])
  if q.min_gap(body,.6)>=.5:continue
  v,_=vf(q);margin=.25 if 'NUT_'in sku else .05;offset=np.array([[x,y,z]for x in[-margin,margin]for y in[-margin,margin]for z in[-margin,margin]]);g=md.Manifold.hull_points((v[:,None]+offset).reshape(-1,3));out.append(g)
  if 'NUT_'in sku:
   A=T@np.array(ctx.CACHE[1][k]['transform']);local=np.c_[v,np.ones(len(v))]@np.linalg.inv(A).T;center=(local[:,:3].min(0)+local[:,:3].max(0))/2;delta=A[:3,0]*np.sign(center[0])*15.;vv=vf(g)[0];out.append(md.Manifold.hull_points(np.r_[vv,vv+delta]))
  rows.append(k)
 g=union(out);v,f=vf(g);np.savez_compressed(p,v=v,f=f);put(dst/f'{pid}.json',{'id':pid,'protected':rows})
