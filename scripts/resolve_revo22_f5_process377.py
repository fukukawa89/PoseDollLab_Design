import sys,traceback,concurrent.futures
from trial_revo22_f5_process273 import trial
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(job):
 p,src,name,settings=job;l='process377_'+name;q=trial(p,src,l,settings)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p)
 return p,l,q['native_review_resolved']
if __name__=='__main__':
 settings=[('classic',{'wall_generator':'classic','detect_thin_wall':'0'}),('width50',{'outer_wall_line_width':'0.5','inner_wall_line_width':'0.5','is_infill_first':'1'}),('width60',{'outer_wall_line_width':'0.6','inner_wall_line_width':'0.6','is_infill_first':'1'}),('micro',{'min_feature_size':'100%'})];jobs=[(p,s,n,v)for p,s in [('P130','ends366_0'),('X038','cut374_0'),('X046','cut374_0'),('X054','ends366_0')]for n,v in settings]
 with concurrent.futures.ProcessPoolExecutor(max_workers=4)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('PROCESS377_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('PROCESS377_ERROR',fs[f],flush=True)
