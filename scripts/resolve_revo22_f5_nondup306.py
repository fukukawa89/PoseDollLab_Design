"""Narrow tapered contacts on small lands, preserving functional-hole clearance."""
import sys,json,shutil,traceback,concurrent.futures,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf
from build_revo22_f5_precise_guards283 import run as guards
from audit_revo22_f5_native271 import run as audit
from route_revo22_f5_side304 import run as route
from trial_revo22_f5_process273 import trial as process
from optimize_revo22_f5_276 import pick,candidates
from verify_revo22_f5_geometry292 import run as geo

def run(pid):
 if pick(pid):return(pid,True)
 choices=[q for q in candidates(pid)if not q[4].get('part_body_modified_from_F4',False)and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))];src=choices[0][2];a=O/'candidates'/pid/src;b=O/'candidates'/pid/'nondup306_base';guards(pid)
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 if not(b/'parts'/f'{pid}.npz').exists():
  for sub,fn in[('parts',f'{pid}.npz'),('design',f'{pid}.json'),('verification','native_final.json'),('verification','plate_manifest.json')]:shutil.copy2(a/sub/fn,b/sub/fn)
  for f in(a/'projects').glob('*.3mf'):shutil.copy2(f,b/'projects'/f.name)
  d=json.loads((b/'design'/f'{pid}.json').read_text());gn=np.load(O/'guards_precise'/f'{pid}.npz');g=solid(gn['v'],gn['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);v,f=vf(g);np.savez_compressed(b/'verification/guards.npz',v=v,f=f);d.update(trial='nondup306_base',guard_policy='actual_hex_precise_283');put(b/'design'/f'{pid}.json',d)
 current='nondup306_base'
 for step in range(3):
  label=f'nondup306_{step}';d=route(pid,current,label,allow_removable_core=True,target_native_height=True,tip_width=.6);q=audit(pid,label)
  if pick(pid):geo(pid);return(pid,True)
  before=json.loads((O/'candidates'/pid/current/'design'/f'{pid}.json').read_text());current=label
  if d['new_tooth_count']==before['new_tooth_count']:break
 process(pid,current,'nondup306_micro',{'min_feature_size':'100%'})
 if pick(pid):geo(pid);return(pid,True)
 return(pid,False)
if __name__=='__main__':
 ids=sys.argv[1:]or[p.name for p in(O/'candidates').iterdir()if not(O/'selections'/f'{p.name}.json').exists()and candidates(p.name)]
 with concurrent.futures.ProcessPoolExecutor(max_workers=4)as ex:
  fs={ex.submit(run,p):p for p in ids}
  for f in concurrent.futures.as_completed(fs):
   try:print('NONDUP306_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('NONDUP306_ERROR',fs[f],flush=True)
