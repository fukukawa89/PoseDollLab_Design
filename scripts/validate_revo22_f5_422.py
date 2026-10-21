from verify_revo22_f5_contacts298 import run as fit
from verify_revo22_f5_geometry292 import run as geo
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick
p='X046';l='contact420';r=fit(p,l);assert r['fit_and_pose_geometry_passed'];q=audit(p,l)
if q['native_review_resolved']:geo(p,l);assert pick(p);print('FIT422_ALL_PASS',flush=True)
