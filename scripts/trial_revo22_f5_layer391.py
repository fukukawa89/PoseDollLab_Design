import sys,json,shutil,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(job):
 p,src,h=job;l='layer391_'+src+'_'+str(round(h*1000));a=O/'candidates'/p/src;b=O/'candidates'/p/l
 if not(b/'parts'/f'{p}.npz').exists():
  for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
  shutil.copy2(a/'parts'/f'{p}.npz',b/'parts'/f'{p}.npz')
  for fn in ['guards.npz','strict_magnet_guards.npz']:
   if(a/'verification'/fn).exists():shutil.copy2(a/'verification'/fn,b/'verification'/fn)
  d=json.loads((a/'design'/f'{p}.json').read_text());d.update(trial=l,required_layer_height_mm=h,required_initial_layer_height_mm=.2);d['required_process_overrides'].pop('layer_height',None);put(b/'design'/f'{p}.json',d)
 q=audit(p,l)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p);return p,l,True
 return p,l,False
if __name__=='__main__':
 jobs=[('P130','ends366_0',.16),('P130','ends366_0',.12),('X038','ends366_0',.16),('X038','cut388_0',.16)]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('LAYER391_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('LAYER391_ERROR',fs[f],flush=True)
