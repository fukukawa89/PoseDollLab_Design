"""Conservative interval certification of added elbows vs same-module parts.
Bounding motion displacement proves the entire raw-angle cell, not just its centre.
"""
import sys,json,math,time,hashlib,itertools
import numpy as np
import trimesh
import o22f7 as r
h=r.h

def main():
 r.configure();import build_revo22_assembly as a
 a.D=r.WORK/'assembly';a.b.D=a.D;parts,meta,base,*_=a.model();f0,o0=a.owners(base);exports={x['id']:x for x in r.read(h.B/'print_batch/manifest.json')['rows']};reports=[]
 for pid,key in [(pid,ins['part'])for pid in r.read(r.WORK/'whole_batch_audit.json')['affected_ids']for ins in exports[pid]['instances']]:
  n=np.load(r.OUT/f'parts/{pid}.npz');prefix='r1'if pid=='P095'else'f7';added=h.solid(n[prefix+'_added_body_v'],n[prefix+'_added_body_f']);d=r.read(r.OUT/f'design/{pid}.json');module=key.split('/')[0];j=next(x for x in a.profile['joints']if x['id']==module);kind=j['kind'];rawids=j['raw_ids'];A=np.array(meta[key]['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else-1;bed=exports[pid]['bed'];T=h.H(d['orientation']['matrix'],d['orientation']['source_translation_mm'])@h.H(bed['rotation'],bed['translation_mm'])@np.linalg.inv(A);C=T@o0[module,'ring'];abb=np.array(added.bounding_box());limits=np.array([a.profile['raw_limits_deg'][x]for x in rawids],float);neutral=np.array([a.profile['neutral_raw_deg'][x]for x in rawids]);groups={}
  for k,s in parts.items():
   if k==key or meta[k].get('module')!=module or meta[k]['owner']=='rigid_frame':continue
   owner=meta[k]['owner'];groups.setdefault(owner,[]).append(s.transform(np.linalg.inv(o0[module,owner])[:3]))
  def frames(q):
   if kind in ['tut','wide_tut']:f=a.b.b.L.tut.frames(q)
   elif kind=='three_axis':f=a.b.b.L.three_axis.frames(q)
   else:f={'C02':np.eye(3),'ring':a.b.b.rot(1,-q[1]),'C01':a.b.b.rot(1,-q[1])@a.b.b.rot(0,q[0])}
   return f
  ar=next(x for x in r.read(r.WORK/'whole_batch_audit.json')['rows']if x['id']==pid);arms=[x for x in ar['candidate_bends']if x['active_flat_capped_elbow']];centres=np.array([x['print_centre']for x in arms]);radii=np.array([x['radius_mm']for x in arms]);ci=np.linalg.inv(C);ringcentres=centres@ci[:3,:3].T+ci[:3,3];motion_radius=float(np.linalg.norm(ringcentres,axis=1).max())
  av,af=h.vf(added);dv=np.linalg.norm(av[:,None,:]-centres[None,:,:],axis=2)-radii;assert np.max(np.min(dv[af].max(1),axis=1))<1e-6,(pid,'spherical envelope')
  result=[]
  for owner,ss in groups.items():
   source=h.union(ss);sv,sf=h.vf(source);mesh=trimesh.Trimesh(sv,sf,process=False);vs=sv;radius=motion_radius;bb=np.array(source.bounding_box());corners=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))));F=frames(neutral);nom=F['ring'].T@F[owner];active=[]
   for i in range(len(rawids)):
    q=neutral.copy();q[i]+=.731;f=frames(q)
    if np.max(abs(f['ring'].T@f[owner]-nom))>1e-7:active.append(i)
   cells=[limits[active].copy()]if active else[np.zeros((0,2))];tested=0;leaf=0;minlower=1e9;fail=[];start=time.time();maxdepth=0
   while cells:
    cell=cells.pop();q=neutral.copy()
    if active:q[active]=cell.mean(1)
    f=frames(q);rotation=f['ring'].T@f[owner];query=ringcentres@rotation;half=(cell[:,1]-cell[:,0])/2 if active else np.array([])
    displacement=min(2*radius,2*radius*np.deg2rad(half).sum());tested+=1
    distances=-trimesh.proximity.signed_distance(mesh,query);assert np.all(np.isfinite(distances)),(pid,owner,q);gap=float(np.min(distances-radii))
    if tested%10000==0:print('INTERVAL_PROGRESS',pid,owner,tested,len(cells),flush=True)
    if gap>displacement+.05:
     leaf+=1;minlower=min(minlower,gap-displacement);continue
    if not active or max(half)<.015 or tested>200000:
     fail.append(dict(q=q.tolist(),cell=cell.tolist(),gap=gap,bound=displacement));break
    i=int(np.argmax(half));mid=cell[i].mean();left=cell.copy();right=cell.copy();left[i,1]=mid;right[i,0]=mid;cells.extend([left,right])
   rep=dict(owner=owner,parts=len(ss),sensitive_raw_axes=[rawids[i]for i in active],limits_deg=limits[active].tolist(),query_centre_radius_bound_mm=radius,spherical_envelopes_radii_mm=radii.tolist(),cells_tested=tested,certified_cells=leaf,minimum_certified_gap_lower_bound_mm=minlower if leaf else None,passed=not fail,unresolved=fail,elapsed_s=time.time()-start);result.append(rep);print('CONTINUOUS',pid,owner,'PASS'if not fail else'FAIL',tested,'s',round(rep['elapsed_s'],1),flush=True)
  rr=dict(id=pid,part=key,body_sha256=hashlib.sha256(n['v'].tobytes()+n['f'].tobytes()).hexdigest(),passed=all(x['passed']for x in result),groups=result,scope='Spheres containing the complete candidate elbow additions are checked by signed centre-to-surface distance. Conservative rigid-rotation interval bound over all combinations of the same joint raw-axis limits, against every modeled same-module owner part. No baseline-collision exclusions. Other body modules are covered by separate sampled whole-device checks, not this local continuous proof.',clearance_gate_mm=.05)
  h.put(r.WORK/f'continuous/{pid}_{module}.json',rr);reports.append(rr)
 h.put(r.WORK/'continuous_summary.json',dict(passed=all(x['passed']for x in reports),rows=reports))
if __name__=='__main__':main()
