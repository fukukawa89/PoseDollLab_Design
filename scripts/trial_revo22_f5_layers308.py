"""Evaluate thinner layers without changing body, fin or tooth geometry."""
import sys,json,shutil,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick,candidates
from verify_revo22_f5_geometry292 import run as geometry

def trial(pid,src,height):
 label=f'layer308_{round(height*1000)}';a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if not(b/'parts'/f'{pid}.npz').exists():
  for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
  shutil.copy2(a/'parts'/f'{pid}.npz',b/'parts'/f'{pid}.npz');shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz');d=json.loads((a/'design'/f'{pid}.json').read_text());d.update(trial=label,required_layer_height_mm=height,required_initial_layer_height_mm=.2,thinner_layer_trial_from=src,geometry_unchanged_for_layer_trial=True);d['required_process_overrides'].pop('layer_height',None);put(b/'design'/f'{pid}.json',d)
 return audit(pid,label)
def run(pid):
 if pick(pid):return(pid,True)
 qs=[q for q in candidates(pid)if not q[4].get('part_body_modified_from_F4',False)and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))]
 if not qs:return(pid,'no base')
 src=qs[0][2]
 for height in [.16,.12,.10]:
  q=trial(pid,src,height)
  if pick(pid):geometry(pid);return(pid,True)
 return(pid,False)
if __name__=='__main__':
 ids=sys.argv[1:]or[p.name for p in(O/'candidates').iterdir()if not(O/'selections'/f'{p.name}.json').exists()and candidates(p.name)]
 print('LAYER308_PLAN',ids,flush=True)
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in ids}
  for f in concurrent.futures.as_completed(fs):
   try:print('LAYER308_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('LAYER308_ERROR',fs[f],flush=True)
