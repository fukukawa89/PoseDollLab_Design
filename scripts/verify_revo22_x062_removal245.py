"""Verify a concrete cut plan and continuous removal sweep for the remaining supports."""
from pathlib import Path
import sys,json,numpy as np,math
from build_revo22_x062_open242 import S,OLD,put,sha
from build_revo22_fins import solid,vf,union,md,box
from o22_material_components import material_components
from route_revo22_x062244 import tooth,sweep_convex

def exact_clear(s,body,delta):
 if s.is_empty() or body.is_empty():return True,0
 # Swept boundary prisms plus the two endpoints equal sweep by a line segment.
 if (s^body).volume()>1e-6 or (s.translate(delta)^body).volume()>1e-6:return False,0
 hull=sweep_convex(s,delta)
 if (hull^body).volume()<1e-6:return True,0
 v,f=vf(s);tris=v[f];bb=np.array(body.bounding_box());checked=0
 for tri in tris:
  pts=np.vstack([tri,tri+delta]);lo=pts.min(0);hi=pts.max(0)
  if np.any(hi<bb[:3])or np.any(lo>bb[3:]):continue
  norm=np.cross(tri[1]-tri[0],tri[2]-tri[0])
  if abs(np.dot(norm,delta))<1e-8:continue
  # Explicit triangular prism avoids convex-hull failures on thin boundary slivers.
  if np.dot(norm,delta)<0:tri=tri[[0,2,1]]
  points=np.vstack([tri,tri+delta]);faces=np.array([[2,1,0],[3,4,5],[0,1,4],[0,4,3],[1,2,5],[1,5,4],[2,0,3],[2,3,5]],dtype=np.uint64);p=solid(points,faces);checked+=1
  assert str(p.status()).endswith('NoError'),p.status()
  if (p^body).volume()>1e-6:return False,checked
 return True,checked

def run(label):
 folder=S/'candidates/X062'/label;n=np.load(folder/'parts/X062.npz');d=json.loads((folder/'design/X062.json').read_text());body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);stubs=[];rebuilt=[];cuts=[]
 for q in d['teeth']:
  a=np.array([q['x'],q['root_y'],max(.4,q['roof']-q['free_vertical_mm']-.3)]);b=np.array([q['x'],q['y'],q['roof']+.18]);cut=a+(b-a)*((q['cut_height_mm']-a[2])/(b[2]-a[2]));stubs.append(tooth(a,cut));rebuilt.append(tooth(a,b));cuts.append(dict(point=cut.tolist(),neck_xy_mm=[.8,.8],slim_free_vertical_mm=q['free_vertical_mm']))
 for q in d.get('local_route_repairs',[]):
  a=np.array(q['root']);b=np.array(q['target'])+[0,0,.24];cut=a+(b-a)*((q['cut_z_mm']-a[2])/(b[2]-a[2]));stubs.append(tooth(a,cut));rebuilt.append(tooth(a,b));cuts.append(dict(point=cut.tolist(),neck_xy_mm=[.8,.8],slim_free_vertical_mm=q['free_vertical_mm']))
 rebuilt=union(rebuilt);error=float((teeth-rebuilt).volume()+(rebuilt-teeth).volume());assert error<1e-4,error
 remaining=fin+union(stubs);assert (remaining^body).volume()<1e-6;groups=material_components(remaining);rows=[];out={}
 for i,g in enumerate(groups,1):
  related=[]
  for q in d.get('local_route_repairs',[]):
   a=np.array(q['root'])
   if(g^box(a-[.3,.3,.15],a+[.3,.3,.15])).volume()>.005:related.append(q['removal_vector'])
  dirs=[[0.,0.,-1.]]+related+[[math.cos(a)*.8,math.sin(a)*.8,-1.]for a in np.arange(0,2*np.pi,np.pi/6)]
  good=None;attempts=[]
  for dr in dirs:
   dr=np.array(dr);dr/=np.linalg.norm(dr)
   if any(np.allclose(dr,x)for x in attempts):continue
   attempts.append(dr);ok,checks=exact_clear(g,body,dr*210)
   if ok:good=dr;break
  print('REMOVAL_GROUP',i,'of',len(groups),'volume',round(g.volume(),2),'clear',good is not None,'directions',len(attempts),flush=True)
  rows.append(dict(id=f'S{i:02}',bounds_mm=list(g.bounding_box()),volume_mm3=float(g.volume()),removal_vector=good.tolist()if good is not None else None,swept_distance_mm=210,continuous_sweep_passed=good is not None,method='Conservative convex sweep or exact boundary-prism sweep plus endpoints.'))
  out[f'g{i}_v'],out[f'g{i}_f']=vf(g)
 np.savez_compressed(folder/'verification/removal_groups.npz',**out)
 old=np.load(OLD/'parts/X062.npz');M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);exactsource=np.array_equal(n['source_v'],old['source_v'])and np.array_equal(n['f'],old['f']);err=float(np.max(np.abs(n['source_v']@M.T+t-n['v'])));assert exactsource and err<1e-7
 report=dict(id='X062',label=label,parts_npz_sha256=sha(folder/'parts/X062.npz'),original_mesh_exactly_preserved=exactsource,source_transform_error_mm=err,teeth_reconstruction_difference_mm3=error,cut_count=len(cuts),cuts=cuts,remaining_support_groups=len(groups),groups=rows,all_groups_have_continuous_body_clearance=all(r['continuous_sweep_passed']for r in rows),fin_body_intersection_mm3=float((fin^body).volume()),post_cut_support_body_intersection_mm3=float((remaining^body).volume()),scope='Checks rigid removal relative to permanent body after the specified yellow cuts. Support-to-support sequencing is handled separately; this is not a scissors-force or material test.',physical_print_tested=False)
 put(folder/'verification/removal.json',report);assert report['all_groups_have_continuous_body_clearance'];print('REMOVAL245_PASS',label,len(groups),len(cuts),flush=True)
if __name__=='__main__':run(sys.argv[1])
