import sys,traceback,concurrent.futures
from trial_revo22_f5_process273 import trial
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(job):
 p,src,name,settings=job;l='seam386_'+name;q=trial(p,src,l,settings)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p)
 return p,l,q['native_review_resolved']
if __name__=='__main__':
 settings=[('back',{'seam_position':'back'}),('nearest',{'seam_position':'nearest'}),('random',{'seam_position':'random'})];jobs=[(p,s,n,v)for p,s in [('P130','ends366_0'),('X038','ends366_0')]for n,v in settings]
 with concurrent.futures.ProcessPoolExecutor(max_workers=4)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('SEAM386_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('SEAM386_ERROR',fs[f],flush=True)
