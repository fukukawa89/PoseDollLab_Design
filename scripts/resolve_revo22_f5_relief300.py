"""After attempted fin routes, make bounded reliefs outside exact assembly envelopes."""
import sys,json,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from relief_revo22_f5_native275 import run as relief
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_contacts298 import run as fit
from verify_revo22_f5_geometry292 import run as geo
from optimize_revo22_f5_276 import pick,candidates

def run(pid):
 if pick(pid):
  se=json.loads((O/'selections'/f'{pid}.json').read_text())
  if not se.get('body_modified',False):return(pid,True)
  if fit(pid)['fit_and_pose_geometry_passed']:return(pid,True)
 choices=[q for q in candidates(pid)if not q[4].get('part_body_modified_from_F4',False)and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))]
 if not choices:return(pid,'no qualified base')
 current=choices[0][2]
 for step in range(6):
  label=f'contact300_relief{step}';d=relief(pid,current,label)
  if d is None:break
  q=audit(pid,label)
  if q['native_review_resolved']:
   pick(pid)
   if fit(pid)['fit_and_pose_geometry_passed']:geo(pid);return(pid,True)
  current=label
 return(pid,False)
if __name__=='__main__':
 ids=sys.argv[1:]or['P001','P033','P049','P051','P073','P071','P130','W002','W005','W006','W007','W016','W017','X061']
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in ids}
  for f in concurrent.futures.as_completed(fs):
   try:print('RELIEF300_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('RELIEF300_ERROR',fs[f],flush=True)
