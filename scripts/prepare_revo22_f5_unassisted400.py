import sys,json,shutil,numpy as np
sys.path.insert(0,'PoseDoll_HW44_Plan/design/scripts')
from search_revo22_f5_orientation268 import O,OLD,put
from verify_revo22_f5_geometry292 import run as geo
old=json.loads((OLD/'manifest.json').read_text());profiles={i['id']:i.get('source_profile',p['profile'])for p in old['plates']for i in p['items']}
for row in json.loads((O/'inventory.json').read_text())['rows']:
 if row['has_fins']:continue
 p=row['id'];q=O/'candidates'/p/'unassisted_f4';sf=O/'selections'/f'{p}.json'
 if not sf.exists():
  for sub in ['parts','design','verification']:(q/sub).mkdir(parents=True,exist_ok=True)
  shutil.copy2(OLD/'parts'/f'{p}.npz',q/'parts'/f'{p}.npz');d=json.loads((OLD/'design'/f'{p}.json').read_text());pr=profiles[p];d.update(trial='unassisted_f4',f4_to_current_matrix=np.eye(3).tolist(),f4_to_current_translation_mm=[0,0,0],part_body_modified_from_F4=False,new_tooth_count=0,support_count=0,required_layer_height_mm=pr['layer'],required_initial_layer_height_mm=pr['initial'],required_wall_generator=pr['wall'],required_process_overrides=pr.get('overrides',{}),required_layer_ranges=pr.get('height_overrides',[]));put(q/'design'/f'{p}.json',d);put(sf,dict(id=p,label='unassisted_f4',native_pass=None,body_modified=False,support_volume_mm3=0,teeth=0,fins=0,whole_plate_native_audit_required=True))
 geo(p)
print('UNASSISTED400_DONE',flush=True)
