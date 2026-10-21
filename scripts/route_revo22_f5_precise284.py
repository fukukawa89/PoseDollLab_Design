import sys,json,shutil,numpy as np,concurrent.futures,traceback
from search_revo22_f5_orientation268 import O,put
from route_revo22_f5_native272 import run as route
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick
from build_revo22_fins import solid,vf

def run(pid,src):
 if not(O/'guards_precise'/f'{pid}.npz').exists():return(pid,'no_guard')
 a=O/'candidates'/pid/src;b=O/'candidates'/pid/'precise_base'
 for sub in['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 for sub,fn in[('parts',f'{pid}.npz'),('design',f'{pid}.json'),('verification','native_final.json'),('verification','plate_manifest.json')]:shutil.copy2(a/sub/fn,b/sub/fn)
 d=json.loads((b/'design'/f'{pid}.json').read_text());g=np.load(O/'guards_precise'/f'{pid}.npz');s=solid(g['v'],g['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);v,f=vf(s);np.savez_compressed(b/'verification/guards.npz',v=v,f=f);d['guard_policy']='actual_hex_precise_283';put(b/'design'/f'{pid}.json',d);current='precise_base'
 for step in range(3):
  label=f'precise_route{step}';dd=route(pid,current,label);q=audit(pid,label)
  if pick(pid):return(pid,True)
  prev=json.loads((O/'candidates'/pid/current/'design'/f'{pid}.json').read_text());current=label
  if dd['new_tooth_count']==prev['new_tooth_count']:break
 return(pid,False)
if __name__=='__main__':
 jobs=[('P003','oldpose_c'),('X037','oldpose_m100'),('X001','onset_low_a'),('H008','opt0_route0'),('H010','opt0_micro'),('H012','opt0_micro')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as p:
  fs=[p.submit(run,*q)for q in jobs]
  for f in concurrent.futures.as_completed(fs):
   try:print('PRECISE284',f.result(),flush=True)
   except Exception:traceback.print_exc()
