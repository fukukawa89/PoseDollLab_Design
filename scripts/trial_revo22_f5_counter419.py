import traceback,concurrent.futures
from trial_revo22_f5_process273 import trial
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(j):
 k,ss=j;p='P130';l='counter419_'+k;q=trial(p,'reroute417_r4_2',l,ss)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p)
 return p,l,q['native_review_resolved']
if __name__=='__main__':
 jobs=[('partial',{'counterbore_hole_bridging':'partiallybridge'}),('infill',{'counterbore_hole_bridging':'partiallybridge','is_infill_first':'1'}),('micro',{'counterbore_hole_bridging':'partiallybridge','is_infill_first':'1','min_feature_size':'100%'})]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('COUNTER419_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('COUNTER419_ERROR',fs[f],flush=True)
