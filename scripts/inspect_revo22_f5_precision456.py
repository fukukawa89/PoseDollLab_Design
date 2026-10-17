import json,manifold3d as md
from search_revo22_f5_orientation268 import O
print(md.Manifold.set_tolerance.__doc__)
for pid in ['X058']:
 sel=json.loads((O/'selections'/f'{pid}.json').read_text());r=json.loads((O/'candidates'/pid/sel['label']/'verification/f5_fit_and_pose.json').read_text());print(pid,r.get('sampled_valid_pose_contact_changes'))
