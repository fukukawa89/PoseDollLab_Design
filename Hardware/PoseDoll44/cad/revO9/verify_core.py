"""Check remaining moving pairs, core assembly and restricted tool access."""
import itertools,time,numpy as np
from common import *
from rigid_collision import Body,Pair,regression

def main():
 path=OUT/'cup_relief_L3_R0p35/core_meshes.npz';m=dict(np.load(path));fast=dict(np.load(G8/'fastened_core/fasteners.npz'));m['fasteners']=np.concatenate(list(fast.values()));bodies={k:Body(v) for k,v in m.items()};pairs={p:Pair(bodies[p[0]],bodies[p[1]]) for p in itertools.combinations(bodies,2)}
 rows=[]
 for a,b in list(itertools.product((-30,-25,-15,0,15,25,30),(-100,-75,-50,-25,0,25,50,75,100)))+[(75,75)]:
  mats=pose_matrices(a,b);find=[]
  for (x,y),pair in pairs.items():
   if {x,y}<={'C14','C15','fasteners'}:continue # invariant seated fits, inherited with hashes below
   r=pair.check(mats[x],mats[y])
   if not r['status'].startswith('CLEAR'):find.append({'pair':[x,y],**r})
  rows.append({'alpha_deg':a,'beta_deg':b,'status':'FAIL' if any(r['status']=='PENETRATION' for r in find) else 'REVIEW' if find else 'CLEAR_DISCRETE_CORE','findings':find})
 save('core_motion_grid.json',{'cases':rows,'status':'SCOPED_DISCRETE_CHECK','input_sha256':sha(path),'unchanged_seated_fit_report_sha256':sha(G8/'fastened_core/report.json'),'scope':'Includes every moving core pair. Ring-half and screw/nut seated fits stay rigidly together and are inherited unchanged; no outer twist housing or wires included.','physical_tested':False,'manufacturing_released':False});print('MOTION',[(r['alpha_deg'],r['beta_deg'],r['status']) for r in rows if not r['status'].startswith('CLEAR')],flush=True)
 # The same five assembly stages as O8, now tested against the changed geometry.
 stages=[('interleave_yokes','C02',['C01'],[(0,0,z) for z in np.linspace(30,0,31)]),('lower_side_entry','C14',['C01','C02'],[(0,y,-7) for y in np.linspace(-30,0,31)]),('lower_seat','C14',['C01','C02'],[(0,0,z) for z in np.linspace(-7,0,15)]),('upper_side_entry','C15',['C01','C02','C14'],[(x,0,7) for x in np.linspace(30,0,31)]),('upper_seat','C15',['C01','C02','C14'],[(0,0,z) for z in np.linspace(7,0,15)])];out=[]
 for name,part,others,offsets in stages:
  ps={n:Pair(bodies[part],bodies[n]) for n in others};cases=[]
  for offset in offsets:
   findings=[]
   for other,pair in ps.items():
    r=pair.check(ta=np.array(offset));intended=part=='C15' and other=='C14' and np.linalg.norm(offset)<1e-8 and r['status']=='CONTACT_REQUIRES_REVIEW'
    if not r['status'].startswith('CLEAR'):findings.append({'other':other,'intended_final_plane_contact':bool(intended),**r})
   cases.append({'offset_mm':list(offset),'status':'FAIL' if any(r['status']=='PENETRATION' for r in findings) else 'REVIEW' if any(not r['intended_final_plane_contact'] for r in findings) else 'CLEAR_DISCRETE_ASSEMBLY','findings':findings})
  out.append({'stage':name,'moving_part':part,'cases':cases});print('ASSEMBLY',name,[c for c in cases if not c['status'].startswith('CLEAR')],flush=True)
 save('assembly_path.json',{'stages':out,'scope':'123 discrete positions; final half-ring contact is deliberate. No continuous assembly, screw sequence, operator hand access or tolerance claim.','input_sha256':sha(path),'physical_tested':False,'manufacturing_released':False})
 # A 35 mm cylinder equals the union of the old 20 mm exposed straight shaft
 # translated 0..15 mm outwards. This certifies that selected straight approach
 # volume at a fixed pose, not an unmodelled handle or a bent key.
 tools=dict(np.load(G8/'fastened_core/tools.npz'));access=[]
 for key,t in tools.items():
  sign=1 if t[:,:,2].mean()>0 else -1;tool=t.copy();tip=(tool[:,:,2]*sign)>20;tool[:,:,2][tip]+=sign*15
  check={n:Pair(Body(tool),bodies[n]) for n in ('C01','C02')};attempts=[];found=None
  for a,b in sorted(itertools.product((-30,-25,-15,0,15,25,30),(-100,-90,-75,-60,-30,0,30,60,75,90,100)),key=lambda q:abs(q[0])+abs(q[1])):
   mats=pose_matrices(a,b);find=[]
   for n,pair in check.items():
    r=pair.check(mats['C14'],mats[n])
    if not r['status'].startswith('CLEAR'):find.append({'obstacle':n,**r})
   attempts.append({'alpha_deg':a,'beta_deg':b,'findings':find})
   if not find:found={'alpha_deg':a,'beta_deg':b};break
  access.append({'tool':key,'clear_pose_in_working_rectangle':found,'attempts':attempts});print('TOOL',key,found,flush=True)
 save('restricted_tool_access.json',{'tools':access,'scope':'Nominal straight 1.5 AF key swept approach envelope against two yokes. Handle, operator and actual torque not qualified. Work rectangle alpha +/-30, beta +/-100.','input_sha256':sha(path),'physical_tested':False,'manufacturing_released':False})
 # Independent rebuilt-mesh comparisons include the updated translation support.
 from mesh_collision import compare
 receipts=regression(m)
 for offset in ([0,0,30],[0,0,4],[1,2,3]):
  a=m['C02'];b=m['C01'];r=Pair(bodies['C02'],bodies['C01']).check(ta=np.array(offset));old=compare(a+offset,b)
  assert (r['status']=='PENETRATION')==(old['status']=='PENETRATION')
  assert ('REVIEW' in r['status'])==('REVIEW' in old['status'])
  receipts.append({'offset_mm':offset,'compiled':r,'rebuilt':old})
 save('rigid_collision_regression_final.json',{'status':'PASS','cases':receipts})
if __name__=='__main__':main()
