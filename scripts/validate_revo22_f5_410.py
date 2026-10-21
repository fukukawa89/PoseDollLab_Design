from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick
g=geo('X046','cap396_0');r=fit('X046','cap396_0');assert r['fit_and_pose_geometry_passed'];assert pick('X046');print('X046_FINAL410_PASS',flush=True)
