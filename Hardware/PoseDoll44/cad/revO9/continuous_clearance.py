"""Conservative continuous yoke clearance over closed angle rectangles.
Geometry is the complete closed triangle mesh, not vertices alone. Distance to
an oriented closed surface is 1-Lipschitz. Each BVH node / triangle is enclosed
in a ball. Rotation displacement is bounded by the exact chord bound per axis.
Finite numerical tolerances remain; this is not manufacturing qualification.
"""
import numpy as np,time,json
from common import *
from rigid_collision import Body,Pair

class Node:
 def __init__(self,t):
  low=t.min((0,1));high=t.max((0,1));self.p=(low+high)/2;self.radius=float(np.linalg.norm(t-self.p,axis=2).max());self.children=None;self.faces=None;self.max_radius=float(np.linalg.norm(t,axis=2).max())
  if len(t)<=8:self.faces=t;return
  centers=t.mean(1);axis=np.argmax(np.ptp(centers,axis=0));idx=np.argsort(centers[:,axis]);h=len(idx)//2;self.children=(Node(t[idx[:h]]),Node(t[idx[h:]]))

class Certificate:
 def __init__(self,a,b,unsigned=False):
  self.unsigned=unsigned;self.a=a;self.target=Body(b);self.root=Node(a);self.pair=Pair(Body(a),self.target);self.radial_exclusion=(abs if unsigned else lambda x:max(0.,x))(float(self.target.distance.EvaluateFunction([0.,0.,0.])))
 def cell(self,abox,bbox,required=.6,max_tri_depth=7,max_queries=25000):
  a0=(abox[0]+abox[1])/2;b0=(bbox[0]+bbox[1])/2;ha=np.deg2rad((abox[1]-abox[0])/2);hb=np.deg2rad((bbox[1]-bbox[0])/2)
  A=rot([1,0,0],a0);B=rot([0,1,0],b0);ca=2*np.sin(ha/2);cb=2*np.sin(hb/2);queries=0;lower=float('inf')
  def evaluate(p,r):
   nonlocal queries
   pA=p@A;wa=ca*np.hypot(p[1],p[2]);wb=cb*np.hypot(pA[0],pA[2]);w=wa+wb;d=float(self.target.distance.EvaluateFunction(pA@B));d=abs(d) if self.unsigned else d;queries+=1
   return d-r-w,d,w
  stack=[self.root]
  while stack:
   if queries>=max_queries:return {'status':'SUBDIVIDE_ANGLES','reason':'QUERY_BUDGET_NO_PASS','queries':queries}
   n=stack.pop()
   radial_bound=self.radial_exclusion-n.max_radius
   if radial_bound>=required:lower=min(lower,radial_bound);continue
   lb,d,w=evaluate(n.p,n.radius)
   if lb>=required:lower=min(lower,lb);continue
   if n.children:stack.extend(n.children);continue
   triangles=[(t,0) for t in n.faces]
   while triangles:
    if queries>=max_queries:return {'status':'SUBDIVIDE_ANGLES','reason':'QUERY_BUDGET_NO_PASS','queries':queries}
    t,depth=triangles.pop()
    radial_bound=self.radial_exclusion-float(np.linalg.norm(t,axis=1).max())
    if radial_bound>=required:lower=min(lower,radial_bound);continue
    p=t.mean(0);r=float(np.linalg.norm(t-p,axis=1).max());lb,d,w=evaluate(p,r)
    if lb>=required:lower=min(lower,lb);continue
    if d<required-1e-7:return {'status':'INSUFFICIENT_AT_CELL_CENTER','alpha_deg':a0,'beta_deg':b0,'witness_source_mm':p.tolist(),'signed_distance_mm':d,'queries':queries}
    if (d-w<required and depth>=1) or depth>=max_tri_depth:return {'status':'SUBDIVIDE_ANGLES','queries':queries}
    x,y,z=t;xy=(x+y)/2;yz=(y+z)/2;zx=(z+x)/2
    triangles.extend((q,depth+1) for q in (np.array([x,xy,zx]),np.array([xy,y,yz]),np.array([zx,yz,z]),np.array([xy,yz,zx])))
  return {'status':'CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE','lower_bound_mm':lower,'queries':queries}

def main():
 path=OUT/'cup_relief_L3_R0p35/core_meshes.npz';input_paths=[path,Path(__file__),Path(__file__).with_name('common.py'),Path(__file__).with_name('rigid_collision.py'),H/'cad/revO8/reference_assembly.py',H/'cad/revO8/mesh_collision.py'];input_before={str(p.relative_to(H)):sha(p) for p in input_paths};m=dict(np.load(path));cert=Certificate(m['C01'],m['C02']);initial=cert.pair.check();assert initial['status'].startswith('CLEAR'),initial
 # The connected rectangle contains the checked disjoint neutral assembly.
 # Certified positive surface clearance throughout prevents any transition into
 # overlap or containment. Do not infer this from unsigned distances alone.
 stack=[((-30.,30.),(-100.,100.),0)];rows=[];failed=[];unknown=[];queries=0;t0=time.perf_counter();count=0
 while stack:
  aa,bb,depth=stack.pop();r=cert.cell(aa,bb);queries+=r['queries'];count+=1
  if r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE':rows.append({'alpha_interval_deg':aa,'beta_interval_deg':bb,**r})
  elif r['status']=='INSUFFICIENT_AT_CELL_CENTER':failed.append({'alpha_interval_deg':aa,'beta_interval_deg':bb,**r})
  elif depth>=24 or max(aa[1]-aa[0],bb[1]-bb[0])<.125:unknown.append({'alpha_interval_deg':aa,'beta_interval_deg':bb,**r})
  elif aa[1]-aa[0]>=bb[1]-bb[0]:
   mid=sum(aa)/2;stack.extend([((aa[0],mid),bb,depth+1),((mid,aa[1]),bb,depth+1)])
  else:
   mid=sum(bb)/2;stack.extend([(aa,(bb[0],mid),depth+1),(aa,(mid,bb[1]),depth+1)])
  if count%100==0:print(count,'certified',len(rows),'failed',len(failed),'unknown',len(unknown),'pending',len(stack),'covered_area_deg2',round(sum((r['alpha_interval_deg'][1]-r['alpha_interval_deg'][0])*(r['beta_interval_deg'][1]-r['beta_interval_deg'][0]) for r in rows),1),'seconds',round(time.perf_counter()-t0,1),flush=True)
 result={'status':'CERTIFIED_SCOPED_NOMINAL_YOKE_WORKSPACE' if not failed and not unknown else 'INCOMPLETE_OR_FAIL','alpha_interval_deg':[-30,30],'beta_interval_deg':[-100,100],'required_mm':.6,'certified_cells':rows,'failed_cells':failed,'unknown_cells':unknown,'processed_cells':count,'distance_queries':queries,'seconds':time.perf_counter()-t0,'initial_disjoint_collision_check':initial,'input_sha256':sha(path),'scope':'Continuous C01/C02 surfaces over the entire stated angle rectangle. Ring, fasteners, external housings, stops and wires require separate checks. 0.6 mm nominal allowance is not an assembled-tolerance or load certificate.','physical_tested':False,'manufacturing_released':False}
 input_after={str(p.relative_to(H)):sha(p) for p in input_paths};assert input_before==input_after,'Input changed during run';result['input_receipt_sha256']=input_before;result['interval_area_deg2']=sum((r['alpha_interval_deg'][1]-r['alpha_interval_deg'][0])*(r['beta_interval_deg'][1]-r['beta_interval_deg'][0]) for r in rows+failed+unknown);assert abs(result['interval_area_deg2']-12000)<1e-6;save('continuous_yoke_workspace.json',result);print(result['status'],len(rows),len(failed),len(unknown),queries,round(result['seconds'],1),flush=True)
if __name__=='__main__':main()
