import json
from search_revo22_f5_orientation268 import O
for pid in ['P071','P093']:
 se=json.loads((O/'selections'/f'{pid}.json').read_text());f=O/'candidates'/pid/se['label']/'verification/f5_fit_and_pose.json';r=json.loads(f.read_text());print(pid,se['label'],r.get('schema'),r.get('sampled_valid_pose_contact_changes'))
