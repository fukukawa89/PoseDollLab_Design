"""Compare required micro-feature filtering with the exact same mesh."""
import json,sys,shutil,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from audit_revo22_f5_native271 import run

def trial(pid,src,label,settings):
 a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 if not(b/'design'/f'{pid}.json').exists():
  for sub,fn in [('parts',f'{pid}.npz'),('verification','guards.npz')]:shutil.copy2(a/sub/fn,b/sub/fn)
  
  if(a/'verification/strict_magnet_guards.npz').exists():shutil.copy2(a/'verification/strict_magnet_guards.npz',b/'verification/strict_magnet_guards.npz')
  d=json.loads((a/'design'/f'{pid}.json').read_text());d['required_process_overrides']=dict(d.get('required_process_overrides',{}),**settings);d['required_wall_generator']=settings.get('wall_generator',d.get('required_wall_generator','arachne'));d['trial']=label;put(b/'design'/f'{pid}.json',d)
 return run(pid,label)
if __name__=='__main__':
 jobs=[('X001','oldpose_b','oldpose_m100',{'min_feature_size':'100%'}),('X037','oldpose_guard_c','oldpose_m100',{'min_feature_size':'100%'}),('P003','open_a','open_m100',{'min_feature_size':'100%'})]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  for r in ex.map(lambda x:x,[]):pass
  ff=[ex.submit(trial,*q)for q in jobs]
  for f in concurrent.futures.as_completed(ff):f.result()
