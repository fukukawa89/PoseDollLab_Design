"""One-dimensional continuous checks of the remaining rotating core pairs."""
import itertools,time,numpy as np
from common import *
from continuous_clearance import Certificate

def domain(cert,aa,bb,required):
 # Check disjointness at a known member of this connected interval.
 initial=cert.pair.check(B=pose_matrices(sum(aa)/2,sum(bb)/2)['C02'])
 if not initial['status'].startswith('CLEAR'):return {'status':'INITIAL_CONTACT_OR_OVERLAP','initial':initial}
 stack=[(aa,bb,0)];passed=[];failed=[];unknown=[];n=0
 while stack:
  a,b,depth=stack.pop();r=cert.cell(a,b,required,max_tri_depth=10,max_queries=15000);n+=1
  if n%20==0:print('intervals',n,'certified',len(passed),'failed',len(failed),'unknown',len(unknown),flush=True)
  if r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE':passed.append({'alpha_interval_deg':a,'beta_interval_deg':b,**r})
  elif r['status']=='INSUFFICIENT_AT_CELL_CENTER':failed.append({'alpha_interval_deg':a,'beta_interval_deg':b,**r})
  elif depth>=14:unknown.append({'alpha_interval_deg':a,'beta_interval_deg':b,**r})
  elif a[1]>a[0]:
   mid=sum(a)/2;stack.extend([((a[0],mid),b,depth+1),((mid,a[1]),b,depth+1)])
  else:
   mid=sum(b)/2;stack.extend([(a,(b[0],mid),depth+1),(a,(mid,b[1]),depth+1)])
 return {'status':'CERTIFIED_CONTINUOUS_SCOPED_PAIR' if not failed and not unknown else 'FAIL_OR_UNKNOWN','required_nominal_mm':required,'initial':initial,'cells':passed,'failed_cells':failed,'unknown_cells':unknown,'processed':n}

def main():
 path=OUT/'cup_relief_L3_R0p35/core_meshes.npz';m=dict(np.load(path));m['fasteners']=np.concatenate(list(dict(np.load(G8/'fastened_core/fasteners.npz')).values()));rows=[]
 for part in ('C14','C15','fasteners'):
  for yoke in ('C01','C02'):
   if yoke=='C01':source,target=m[part],m[yoke];aa,bb=(-30.,30.),(0.,0.);frame='intermediate frame, input rotates by minus alpha; symmetric interval unchanged'
   else:source,target=m[part],m[yoke];aa,bb=(0.,0.),(-100.,100.);frame='intermediate ring frame'
   t0=time.perf_counter();r=domain(Certificate(source,target),aa,bb,.01);rows.append({'pair':[yoke,part],'frame':frame,'seconds':time.perf_counter()-t0,**r});print(yoke,part,r['status'],r.get('processed'),len(r.get('failed_cells',[])),len(r.get('unknown_cells',[])),round(time.perf_counter()-t0,1),flush=True)
   save('continuous_other_core_pairs.json',{'status':'RUNNING' if len(rows)<6 else 'COMPLETE','pairs':rows,'scope':'0.01 mm positive nominal surface separation screen for actual moving core pairs, including small intended bearing clearances. It is NOT a manufacturing tolerance requirement or an achieved clearance allowance. Fixed seated ring/fastener fits are inherited separately.','input_sha256':sha(path),'physical_tested':False,'manufacturing_released':False})
if __name__=='__main__':main()
