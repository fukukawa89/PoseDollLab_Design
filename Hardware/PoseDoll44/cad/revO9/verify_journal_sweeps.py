"""Finite frustum supersets of journal mesh surfaces, invariant under rotation.
The target is partitioned exactly into journal triangles and remaining surfaces.
Each journal triangle is enclosed by an axial frustum; no target face is dropped.
The source is separated from these convex supersets by supporting planes. The
remaining open surfaces are checked using unsigned distance plus a mandatory
initial disjointness check of the COMPLETE closed meshes.
"""
import numpy as np,time,json
from common import *
from rigid_collision import Body,Pair
from continuous_clearance import Certificate

def split_journals(t,axis):
 cols=[i for i in range(3) if i!=axis];ax=np.abs(t[:,:,axis]);r=np.linalg.norm(t[:,:,cols],axis=2)
 mask=(ax.min(1)>=4.99998)&(ax.max(1)<=9.25002)&(r.max(1)<=2.2582)&(np.sign(t[:,:,axis]).min(1)==np.sign(t[:,:,axis]).max(1));groups={}
 for tri in t[mask]:
  sign=np.sign(tri[0,axis]);x=tri[:,axis]*sign;rad=np.linalg.norm(tri[:,cols],axis=1);lo=float(x.min());hi=float(x.max());key=(int(sign),round(lo,5),round(hi,5));r0=float(rad[np.abs(x-lo)<1e-5].max());r1=float(rad[np.abs(x-hi)<1e-5].max())
  if hi-lo>1e-8:
   excess=max(0.,float((rad-(r0+(r1-r0)*(x-lo)/(hi-lo))).max()));r0+=excess;r1+=excess
  else:r0=r1=max(r0,r1)
  old=groups.get(key,(0,0));groups[key]=(max(old[0],r0+2e-5),max(old[1],r1+2e-5))
 frusta=[{'sign':s,'lo':lo-1e-5,'hi':hi+1e-5,'r0':v[0]+.001,'r1':v[1]+.001} for (s,lo,hi),v in groups.items()]
 # The rounding and extension of steep, nearly planar frusta can change slopes.
 # Independently verify every selected input vertex against its final superset.
 coverage=True
 for tri in t[mask]:
  sign=int(np.sign(tri[0,axis]));x=tri[:,axis]*sign;rad=np.linalg.norm(tri[:,cols],axis=1);key=(sign,round(float(x.min()),5),round(float(x.max()),5));f=frusta[list(groups).index(key)];R=f['r0']+(f['r1']-f['r0'])*(x-f['lo'])/(f['hi']-f['lo']);coverage=coverage and bool(np.all(rad<=R+1e-7))
 assert coverage
 return t[~mask],frusta,{'total_triangles':len(t),'journal_triangles':int(mask.sum()),'remaining_triangles':int((~mask).sum()),'superset_vertex_coverage':coverage,'frusta':len(frusta)}

def certify_frusta(source,axis,frusta,required=.01):
 cols=[i for i in range(3) if i!=axis];minbound=float('inf');queries=0;unknown=[]
 for fi,f in enumerate(frusta):
  slope=(f['r1']-f['r0'])/(f['hi']-f['lo']);normalizer=np.hypot(1,slope);stack=[(source,0)]
  while stack:
   t,depth=stack.pop();x=t[:,:,axis]*f['sign'];v=t[:,:,cols];p=v.mean(1);norm=np.linalg.norm(p,axis=1);unit=p/np.maximum(norm[:,None],1e-12)
   radial=(np.einsum('tvi,ti->tv',v,unit)-slope*x-f['r0']+slope*f['lo']).min(1)/normalizer
   axial=np.maximum(f['lo']-x.max(1),x.min(1)-f['hi']);bound=np.maximum(radial,axial);ok=bound>=required;queries+=len(t)
   if ok.any():minbound=min(minbound,float(bound[ok].min()))
   bad=t[~ok]
   if not len(bad):continue
   if depth>=8:unknown.append({'frustum':fi,'source_triangles':len(bad)});continue
   a,b,c=bad[:,0],bad[:,1],bad[:,2];ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
   child=np.concatenate([np.stack(z,axis=1) for z in ((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca))]);stack.append((child,depth+1))
 return {'status':'CERTIFIED_JOURNAL_SUPERSET_SEPARATION' if not unknown else 'UNKNOWN_SUPERSET_TOO_LOOSE','required_mm':required,'lower_bound_mm':minbound,'plane_checks':queries,'unknown':unknown}

def far_domain(source,target,axis,interval):
 cert=Certificate(source,target,unsigned=True);stack=[(interval,0)];rows=[];failed=[];unknown=[]
 while stack:
  ab,depth=stack.pop();aa,bb=(ab,(0.,0.)) if axis==0 else ((0.,0.),ab);r=cert.cell(aa,bb,.01,max_tri_depth=9,max_queries=60000)
  row={'angle_interval_deg':ab,**r}
  if r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE':rows.append(row)
  elif r['status']=='INSUFFICIENT_AT_CELL_CENTER':failed.append(row)
  elif depth>=10:unknown.append(row)
  else:mid=sum(ab)/2;stack.extend([((ab[0],mid),depth+1),((mid,ab[1]),depth+1)])
 return {'status':'CERTIFIED_CONTINUOUS_REMAINING_SURFACES' if not failed and not unknown else 'FAIL_OR_UNKNOWN','cells':rows,'failed':failed,'unknown':unknown,'unsigned_distance':True}

def main():
 meshfile=OUT/'cup_relief_L3_R0p35/core_meshes.npz';m=dict(np.load(meshfile));m['fasteners']=np.concatenate(list(dict(np.load(G8/'fastened_core/fasteners.npz')).values()));rows=[]
 inputs=[meshfile,Path(__file__),Path(__file__).with_name('continuous_clearance.py'),Path(__file__).with_name('common.py'),Path(__file__).with_name('rigid_collision.py'),H/'cad/revO8/mesh_collision.py',H/'cad/revO8/reference_assembly.py',G8/'fastened_core/fasteners.npz'];before={str(p.relative_to(H)):sha(p) for p in inputs}
 for yoke,axis,interval in [('C01',0,(-30.,30.)),('C02',1,(-100.,100.))]:
  far,frusta,partition=split_journals(m[yoke],axis)
  for part in ('C14','C15','fasteners'):
   t0=time.perf_counter();initial=Pair(Body(m[part]),Body(m[yoke])).check();assert initial['status'].startswith('CLEAR')
   j=certify_frusta(m[part],axis,frusta);print(yoke,part,'journal',j['status'],j['plane_checks'],flush=True)
   r=far_domain(m[part],far,axis,interval) if j['status']=='CERTIFIED_JOURNAL_SUPERSET_SEPARATION' else {'status':'NOT_RUN_JOURNAL_ENVELOPE_UNKNOWN'}
   row={'pair':[yoke,part],'interval_deg':interval,'axis':axis,'partition':partition,'journal':j,'remaining_surfaces':r,'initial_full_closed_meshes':initial,'seconds':time.perf_counter()-t0,'status':'CERTIFIED_CONTINUOUS_SCOPED_PAIR' if j['status']=='CERTIFIED_JOURNAL_SUPERSET_SEPARATION' and r['status']=='CERTIFIED_CONTINUOUS_REMAINING_SURFACES' else 'FAIL_OR_UNKNOWN'};rows.append(row);print(yoke,part,row['status'],round(row['seconds'],1),flush=True)
   assert before=={str(p.relative_to(H)):sha(p) for p in inputs}
   save('continuous_other_core_pairs.json',{'status':'COMPLETE' if len(rows)==6 else 'RUNNING','pairs':rows,'input_receipt_sha256':before,'scope':'Positive 0.01 mm nominal separation of rotating meshes; journal surfaces covered by invariant conical supersets and all other faces by continuous interval bounds. Not a manufacturing tolerance, fit, load or wear certificate. Fixed seated fits are inherited unchanged.','physical_tested':False,'manufacturing_released':False})
if __name__=='__main__':main()
