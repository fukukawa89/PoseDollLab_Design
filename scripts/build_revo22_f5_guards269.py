"""Functional guards in each frozen F4 print coordinate frame."""
from pathlib import Path
import sys,json,numpy as np,time
from build_revo22_fins import solid,vf,union,box,protected,md
from search_revo22_f5_orientation268 import R,B,O,OLD,put
import repair_revo22_f4_guarded_chamfer as ctx
(O/'guards').mkdir(exist_ok=True)
def run(ids):
 lookup=json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects'];offset=np.array([[x,y,z]for x in[-.25,.25]for y in[-.25,.25]for z in[-.25,.25]])
 for pid in ids:
  if(O/'guards'/f'{pid}.npz').exists():continue
  n=np.load(OLD/'parts'/f'{pid}.npz');d=json.loads((OLD/'design'/f'{pid}.json').read_text());body=solid(n['v'],n['f']);bb=np.array(body.bounding_box());M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);vols=[v for q in lookup if q['id']==pid for v in q['volumes']];ss=[protected(vols).transform(np.c_[M,t])]if vols else[];rows=[]
  try:
   parts,key,T=ctx.context(d,pid)
   for k,p in parts.items():
    sku=ctx.CACHE[1][k].get('sku')or''
    if not any(x in sku for x in ['NUT_','SCREW_','SHOULDER_']):continue
    oldbb=np.array(p.bounding_box());corners=np.array([[x,y,z,1]for x in oldbb[[0,3]]for y in oldbb[[1,4]]for z in oldbb[[2,5]]])@T.T;lo=corners[:,:3].min(0);hi=corners[:,:3].max(0);sep=np.maximum(np.maximum(lo-bb[3:],bb[:3]-hi),0)
    if np.linalg.norm(sep)>.6:continue
    sp=p.transform(T[:3,:])
    if sp.min_gap(body,.6)>=.5:continue
    v,f=vf(sp);expanded=md.Manifold.hull_points((v[:,None,:]+offset).reshape(-1,3));ss.append(expanded);row=dict(part=k,sku=sku,margin_mm=.25,radial_entry_guard=False)
    if 'magnet' in k and 'nut' in k:
     A=T@np.array(ctx.CACHE[1][k]['transform']);local=np.c_[v,np.ones(len(v))]@np.linalg.inv(A).T;center=(local[:,:3].min(0)+local[:,:3].max(0))/2;delta=A[:3,0]*np.sign(center[0])*15.;vv=vf(expanded)[0];ss.append(md.Manifold.hull_points(np.r_[vv,vv+delta]));row.update(radial_entry_guard=True,radial_travel_mm=15,axis=delta.tolist())
    rows.append(row)
  except Exception as e:raise RuntimeError((pid,'hardware guard context failed',repr(e)))
  guard=union(ss);v,f=vf(guard);np.savez_compressed(O/'guards'/f'{pid}.npz',v=v,f=f);put(O/'guards'/f'{pid}.json',dict(id=pid,source_protected_volumes=len(vols),hardware=rows,scope='Expanded hardware fit envelopes and supplied source functional clearances. Magnet cap nuts also reserve the outward radial entry sweep. Guards may overlap permanent body; they forbid supports only, and do not certify an entire assembly motion.'));print('GUARDS',pid,len(vols),len(rows),sum(r['radial_entry_guard']for r in rows),flush=True)
if __name__=='__main__':
 inv=json.loads((O/'inventory.json').read_text());ids=sys.argv[1:]or[g[0]for g in inv['groups']if next(x for x in inv['rows']if x['id']==g[0])['has_fins']and g[0]!='X062'];run(ids)
