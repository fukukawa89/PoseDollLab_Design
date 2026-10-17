import sys,json,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O
from transfer_revo22_f5_family289 import build
from audit_revo22_f5_native271 import run as audit
from route_revo22_f5_native272 import run as route
from trial_revo22_f5_process273 import trial as process
from optimize_revo22_f5_276 import pick
from verify_revo22_f5_geometry292 import run as geo

def run(job):
 pid,ref=job;src=build(pid,ref);q=audit(pid,src)
 for i in range(3):
  if q['native_review_resolved']:break
  label=f'family301_{i}';d=route(pid,src,label,allow_removable_core=True,target_native_height=True);q=audit(pid,label);before=json.loads((O/'candidates'/pid/src/'design'/f'{pid}.json').read_text());src=label
  if d['new_tooth_count']==before['new_tooth_count']:break
 if not q['native_review_resolved']:q=process(pid,src,'family301_micro',{'min_feature_size':'100%'})
 if q['native_review_resolved']:pick(pid);geo(pid)
 print('FAMILY301',pid,q['native_review_resolved'],q['external_island_count'],q['critical_external_count'],flush=True)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  fs={ex.submit(run,j):j for j in[('P116','P034'),('X076','X037'),('X061','X037')]}
  for f in concurrent.futures.as_completed(fs):
   try:f.result()
   except Exception:traceback.print_exc();print('FAMILY301_ERROR',fs[f],flush=True)
