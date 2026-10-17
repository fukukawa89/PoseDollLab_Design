import sys,concurrent.futures,traceback
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(p,l):
 g=geo(p,l)
 if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
 assert pick(p)
 return p,l,'VALIDATED'
if __name__=='__main__':
 pairs=[('P071','gusset338_0'),('W017','gusset338_0'),('P051','extract341_0'),('P073','extract341_0'),('P117','extract341_0')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as ex:
  fs={ex.submit(run,*q):q for q in pairs}
  for f in concurrent.futures.as_completed(fs):
   try:print('VALIDATE342',f.result(),flush=True)
   except Exception:traceback.print_exc();print('VALIDATE342_ERROR',fs[f],flush=True)
