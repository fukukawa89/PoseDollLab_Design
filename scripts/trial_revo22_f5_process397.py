import traceback,concurrent.futures
from trial_revo22_f5_process273 import trial
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(j):
 p,src,k,settings=j;l='process397_'+k;q=trial(p,src,l,settings)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p)
 return p,l,q['native_review_resolved']
if __name__=='__main__':
 variants=[('width45',dict(outer_wall_line_width='0.45',inner_wall_line_width='0.45')),('width48',dict(outer_wall_line_width='0.48',inner_wall_line_width='0.48')),('bead60',dict(min_bead_width='60%'))]
 jobs=[(p,'ends366_0',k,ss)for p in ['P130','X038']for k,ss in variants]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('PROCESS397_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('PROCESS397_ERROR',fs[f],flush=True)
