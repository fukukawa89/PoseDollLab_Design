import sys,json,concurrent.futures,traceback
from relief_revo22_f5_bead317 import run as relief
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import candidates,pick
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit

def run(p):
 if pick(p):return(p,True)
 src=candidates(p)[0][2]
 for i in range(5):
  label=f'bead317_{i}'
  if not relief(p,src,label):break
  q=audit(p,label)
  if q['native_review_resolved']:
   pick(p);geo(p);assert fit(p)['fit_and_pose_geometry_passed'];return(p,True)
  src=label
 return(p,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in sys.argv[1:]}
  for f in concurrent.futures.as_completed(fs):
   try:print('BEAD317_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('BEAD317_ERROR',fs[f],flush=True)
