import traceback,concurrent.futures
from route_revo22_f5_ends366 import run as route
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(j):
 p,src=j
 for i in range(3):
  l=f'reroute399_{i}';d=route(p,src,l,allow_removable_core=True);q=audit(p,l)
  if q['native_review_resolved']:
   g=geo(p,l)
   if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
   assert pick(p);return p,True
  src=l
 return p,False
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  fs={ex.submit(run,j):j for j in [('X038','cut388_0'),('P130','shaped394_3')]}
  for f in concurrent.futures.as_completed(fs):
   try:print('REROUTE399_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('REROUTE399_ERROR',fs[f],flush=True)
