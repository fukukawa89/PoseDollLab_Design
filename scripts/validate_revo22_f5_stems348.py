import sys,concurrent.futures,traceback
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def run(p):
 g=geo(p,'clearstem345_0')
 if g['body_change_fit_and_pose_required']:assert fit(p,'clearstem345_0')['fit_and_pose_geometry_passed']
 assert pick(p);print('CLEARSTEM348_PASS',p,flush=True)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  fs={ex.submit(run,p):p for p in ['P051','P117']}
  for f in concurrent.futures.as_completed(fs):
   try:f.result()
   except Exception:traceback.print_exc()
