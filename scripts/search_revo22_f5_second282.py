"""Second orientation pass on difficult small families, native-verified."""
import sys,json,math,concurrent.futures,traceback,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_f5_open270 import run as build
from audit_revo22_f5_native271 import run as audit
from route_revo22_f5_native272 import run as route
from optimize_revo22_f5_276 import pick,candidates

def one(pid):
 op=O/'orientation'/f'{pid}.json';ori=json.loads(op.read_text());base_count=len(ori['ranked'])
 if not ori.get('small_tilt_variants'):
  for axis in[0,1]:
   for deg in[-7,7,-15,15]:
    a=math.radians(deg);c=math.cos(a);s=math.sin(a);Q=np.eye(3);i,j=([1,2]if axis==0 else[0,2]);Q[i,i]=c;Q[j,j]=c;Q[i,j]=-s;Q[j,i]=s;ori['ranked'].append(dict(matrix_from_F4=Q.tolist(),bed_face_mm2=0.,xy_hull_area_mm2=1.,experimental_old_pose_tilt_deg=deg,axis=axis))
  ori['small_tilt_variants']=True;put(op,ori)
 ranks=([7,6,10,11,3,4,5,8,9]if pid=='X001'else[12,13,16,17,14,15,18,19,3,4,5,6,7,8,9,10,11])
 for rank in ranks:
  if any(q[3]['native_review_resolved']for q in candidates(pid)):pick(pid);return(pid,True)
  label=f'angle{rank}_a';build(pid,label,rank=rank,lift_override=6.);q=audit(pid,label)
  if pick(pid):return(pid,True)
  if 5*q['external_island_count']+q['critical_external_count']<45:
   nxt=f'angle{rank}_b';route(pid,label,nxt);q=audit(pid,nxt)
   if pick(pid):return(pid,True)
 print('ORIENTATION_PASS_PENDING',pid,flush=True);return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as pool:
  fs=[pool.submit(one,pid)for pid in['X001','P003','X037']]
  for f in concurrent.futures.as_completed(fs):
   try:print('SECOND_ORIENTATION',f.result(),flush=True)
   except Exception:traceback.print_exc()
