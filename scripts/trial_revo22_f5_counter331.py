import sys,json,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O
from optimize_revo22_f5_276 import candidates,pick
from trial_revo22_f5_process273 import trial
from verify_revo22_f5_geometry292 import run as geo

def run(pid):
 if pick(pid):return(pid,True)
 src=next(q[2]for q in candidates(pid)if not q[4].get('part_body_modified_from_F4')and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf')))
 for mode,settings in [('partial',{'counterbore_hole_bridging':'partiallybridge'}),('infill',{'counterbore_hole_bridging':'partiallybridge','is_infill_first':'1'})]:
  label='counter331_'+mode;q=trial(pid,src,label,settings)
  if q['native_review_resolved']:pick(pid);geo(pid);return(pid,True)
 return(pid,False)
if __name__=='__main__':
 ids=sys.argv[1:]or[p.name for p in(O/'candidates').iterdir()if not(O/'selections'/f'{p.name}.json').exists()and candidates(p.name)]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in ids}
  for f in concurrent.futures.as_completed(fs):
   try:print('COUNTER331_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('COUNTER331_ERROR',fs[f],flush=True)
