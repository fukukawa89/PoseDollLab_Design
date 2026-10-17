"""Resolve pending parts using precise guards and native-height contacts."""
import sys,json,shutil,concurrent.futures,traceback,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf
from build_revo22_f5_precise_guards283 import run as guards
from route_revo22_f5_native272 import run as route
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick,candidates
from trial_revo22_f5_process273 import trial as process
from relief_revo22_f5_native275 import run as relief
from trial_revo22_f5_phase280 import run as phase

def run(pid):
 if pick(pid):return(pid,True)
 choices=[q for q in candidates(pid)if list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))and not q[4].get('part_body_modified_from_F4',False)]
 if not choices:return(pid,'no_eligible_base')
 src=choices[0][2];a=O/'candidates'/pid/src;b=O/'candidates'/pid/'pass2_base';guards(pid)
 for sub in['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 for sub,fn in[('parts',f'{pid}.npz'),('design',f'{pid}.json'),('verification','native_final.json'),('verification','plate_manifest.json')]:shutil.copy2(a/sub/fn,b/sub/fn)
 for f in(a/'projects').glob('*.3mf'):shutil.copy2(f,b/'projects'/f.name)
 d=json.loads((b/'design'/f'{pid}.json').read_text());gn=np.load(O/'guards_precise'/f'{pid}.npz');g=solid(gn['v'],gn['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);v,f=vf(g);np.savez_compressed(b/'verification/guards.npz',v=v,f=f);d['guard_policy']='actual_hex_precise_283';d['trial']='pass2_base';d['guard_base_from']=src;put(b/'design'/f'{pid}.json',d);current='pass2_base'
 for step in range(3):
  label=f'pass2_tip{step}';dd=route(pid,current,label,allow_removable_core=True,target_native_height=True);q=audit(pid,label)
  if pick(pid):return(pid,True)
  before=json.loads((O/'candidates'/pid/current/'design'/f'{pid}.json').read_text());current=label
  if dd['new_tooth_count']==before['new_tooth_count']:break
 for suffix,settings in[('micro',{'min_feature_size':'100%'}),('width',{'outer_wall_line_width':'0.6','inner_wall_line_width':'0.6','is_infill_first':'1'})]:
  process(pid,current,'pass2_'+suffix,settings)
  if pick(pid):return(pid,True)
 best=[q for q in candidates(pid)if list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))][0];current=best[2]
 for step in range(3):
  label=f'pass2_relief{step}';d=relief(pid,current,label)
  if d is None:break
  audit(pid,label)
  if pick(pid):return(pid,True)
  current=label
 best=[q for q in candidates(pid)if not q[4].get('part_body_modified_from_F4',False)and q[4].get('lift_mm',0)>1 and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))]
 if best and best[0][0]<16:
  for delta in[.05,.1,.15]:
   phase(pid,best[0][2],delta)
   if pick(pid):return(pid,True)
 q=candidates(pid)[0];put(O/'pending_pass2'/f'{pid}.json',dict(id=pid,best_label=q[2],islands=q[3]['external_island_count'],critical=q[3]['critical_external_count'],score=q[0]));return(pid,False)
if __name__=='__main__':
 ids=sys.argv[1:]or[p.stem for p in(O/'pending').glob('*.json')];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as pool:
  fs={pool.submit(run,pid):pid for pid in ids}
  for f in concurrent.futures.as_completed(fs):
   try:out.append(f.result());put(O/'pass2_progress.json',out);print('PASS2_RESULT',out[-1],flush=True)
   except Exception:traceback.print_exc();print('PASS2_ERROR',fs[f],flush=True)
