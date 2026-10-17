import json,collections
from search_revo22_f5_orientation268 import O
f=O/'candidates/X046/contact423/verification/f5_fit_and_pose.json';q=json.loads(f.read_text());flags=q['sampled_valid_pose_contact_changes'];seen=set()
for r in flags:
 k=(r['part'],round(r['changed_volume_in_contact_zone_mm3'],9))
 if k in seen:continue
 seen.add(k);print(r)
print('COUNTS',len(flags),q['removed_volume_mm3'],q['added_volume_mm3'],q['edited_volume_outside_recorded_ROIs_mm3'])
