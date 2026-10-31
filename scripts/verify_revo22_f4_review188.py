from pathlib import Path
import sys,concurrent.futures,traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
def one(spec):
 try:
  pid,label=spec.split(':');f=fit(pid,label);g=geom(pid,label)
  if f['fit_and_pose_geometry_passed']and g['geometric_constraints_passed']:run(pid,label);check(pid,label);return refine(pid,label)['native_review_resolved']
 except Exception:traceback.print_exc()
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):print('REVIEW188_RESULT',f.result(),flush=True)
