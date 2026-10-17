import sys,json
sys.path.insert(0,'PoseDoll_HW44_Plan/design/scripts')
from search_revo22_f5_orientation268 import O
p=O/'candidates/X054/bounded379_0/verification/f5_fit_and_pose.json'
print('exists',p.exists())
if p.exists():
 q=json.loads(p.read_text());print({k:v for k,v in q.items() if k in ['fit_and_pose_geometry_passed','added_volume_mm3','removed_volume_mm3','base_actual_contact_zones_preserved']})
from verify_revo22_f5_contacts298 import run
r=run('X054','bounded379_0')
assert r['fit_and_pose_geometry_passed']
from optimize_revo22_f5_276 import pick
print('PICK',bool(pick('X054')))
