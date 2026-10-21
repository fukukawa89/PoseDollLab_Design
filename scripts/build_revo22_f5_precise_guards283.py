"""Accurate functional envelopes: actual hex fasteners, source clearance cores + 0.05 mm."""
import sys,json,numpy as np,math
from search_revo22_f5_orientation268 import O,B,OLD,put
from build_revo22_fins import solid,vf,box,union,md
import repair_revo22_f4_guarded_chamfer as ctx

def run(pid):
 dst=O/'guards_precise';dst.mkdir(exist_ok=True)
 if(dst/f'{pid}.npz').exists():return
 n=np.load(OLD/'parts'/f'{pid}.npz');d=json.loads((OLD/'design'/f'{pid}.json').read_text());body=solid(n['v'],n['f']);bb=np.array(body.bounding_box());M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);parts,key,T=ctx.context(d,pid);ss=[];rows=[]
 for k,p in parts.items():
  sku=ctx.CACHE[1][k].get('sku')or''
  if not any(x in sku for x in['NUT_','SCREW_','SHOULDER_']):continue
  oldbb=np.array(p.bounding_box());corn=np.array([[x,y,z,1]for x in oldbb[[0,3]]for y in oldbb[[1,4]]for z in oldbb[[2,5]]])@T.T;lo=corn[:,:3].min(0);hi=corn[:,:3].max(0);sep=np.maximum(np.maximum(lo-bb[3:],bb[:3]-hi),0)
  if np.linalg.norm(sep)>.6:continue
  sp=p.transform(T[:3,:])
  if sp.min_gap(body,.6)>=.5:continue
  v,_=vf(sp);margin=.25 if 'magnet'in k and'nut'in k else .05;offset=np.array([[x,y,z]for x in[-margin,margin]for y in[-margin,margin]for z in[-margin,margin]]);expanded=md.Manifold.hull_points((v[:,None,:]+offset).reshape(-1,3));ss.append(expanded);row=dict(part=k,sku=sku,margin_mm=margin,actual_hex_shape='NUT_'in sku)
  if 'magnet'in k and'nut'in k:
   A=T@np.array(ctx.CACHE[1][k]['transform']);local=np.c_[v,np.ones(len(v))]@np.linalg.inv(A).T;center=(local[:,:3].min(0)+local[:,:3].max(0))/2;delta=A[:3,0]*np.sign(center[0])*15.;vv=vf(expanded)[0];ss.append(md.Manifold.hull_points(np.r_[vv,vv+delta]));row.update(radial_entry_guard=True)
  rows.append(row)
 actual_nuts=sum('NUT_'in x['sku']for x in rows);vols=[v for q in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects']if q['id']==pid for v in q['volumes']];source_rows=[]
 for v in vols:
  if 'nut'in v['feature'].lower()and actual_nuts:source_rows.append(dict(feature=v['feature'],policy='Actual nearby nut hex geometry replaces the circumcircle approximation'));continue
  m=.05
  if v['shape']=='box':s=box(np.array(v['min_mm'])-m,np.array(v['max_mm'])+m)
  else:
   rad=v['radius_mm']*(1/math.cos(math.pi/6)if'nut'in v['feature'].lower()else 1)+m;z0,z1=v['z_mm'];s=md.Manifold.cylinder(z1-z0+2*m,rad,rad,96).translate([0,0,z0-m])
  s=s.transform(np.array(v['local_to_source_print_matrix'])[:3,:]).transform(np.c_[M,t]);ss.append(s);source_rows.append(dict(feature=v['feature'],margin_mm=m))
 g=union(ss);v,f=vf(g);np.savez_compressed(dst/f'{pid}.npz',v=v,f=f);put(dst/f'{pid}.json',dict(id=pid,hardware=rows,source_features=source_rows,scope='Actual fastener convex geometry plus 0.05 mm coordinate margin; magnet cap nut entry sweeps retain 0.25 mm. Source clearance cores use 0.05 mm margin. The earlier circular nut approximation is replaced only where actual nut geometry is available. Final support removal and body identity still require independent verification.'));print('PRECISE_GUARD',pid,len(rows),actual_nuts,flush=True)
if __name__=='__main__':
 for pid in sys.argv[1:]:run(pid)

