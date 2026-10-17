import sys,json,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O
from optimize_revo22_f5_276 import candidates,pick
from route_revo22_f5_long322 import run as route
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geometry
from verify_revo22_f5_contacts298 import run as fit
from relief_revo22_f5_chips328 import run as relief

def run(pid):
 if pick(pid):return(pid,True)
 choices=[q for q in candidates(pid)if q[4].get('required_process_overrides',{}).get('counterbore_hole_bridging')=='partiallybridge'];src=choices[0][2]
 for i in range(3):
  label=f'counter332_route{i}';dd=route(pid,src,label,allow_removable_core=True,target_native_height=True,tip_width=.6);q=audit(pid,label)
  if q['native_review_resolved']:pick(pid);geometry(pid);return(pid,True)
  before=json.loads((O/'candidates'/pid/src/'design'/f'{pid}.json').read_text());src=label
  if dd['new_tooth_count']==before['new_tooth_count']:break
 for i in range(4):
  label=f'counter332_relief{i}'
  if not relief(pid,src,label):break
  q=audit(pid,label)
  if q['native_review_resolved']:pick(pid);geometry(pid);assert fit(pid)['fit_and_pose_geometry_passed'];return(pid,True)
  src=label
 return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in sys.argv[1:]}
  for f in concurrent.futures.as_completed(fs):
   try:print('COUNTER332_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('COUNTER332_ERROR',fs[f],flush=True)
