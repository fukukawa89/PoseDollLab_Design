import json,shutil,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,union
from o22_material_components import material_components
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick
p='X046';l='trim406';a=O/'candidates'/p/'cap396_0';b=O/'candidates'/p/l
if not(b/'parts'/f'{p}.npz').exists():
 n=dict(np.load(a/'parts'/f'{p}.npz'));old=np.load(O/'candidates'/p/'stem356_1'/'parts'/f'{p}.npz');d=json.loads((a/'design'/f'{p}.json').read_text());body=solid(n['v'],n['f']);ref=solid(old['v'],old['f']);teeth=solid(n['teeth_v'],n['teeth_f']);fin=solid(n['fin_v'],n['fin_f']);exposed=ref-body;trimmed=teeth-exposed;trimmed=union([s for s in material_components(trimmed)if(s^body).volume()>.005 and(s^fin).volume()>.005]);print('TRIM406_REMOVED_TOOTH_MM3',(teeth-trimmed).volume(),flush=True)
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n['teeth_v'],n['teeth_f']=vf(trimmed);np.savez_compressed(b/'parts'/f'{p}.npz',**n);d.update(trial=l,teeth_clipped_by_body_relief=True,support_volume_mm3=float((fin+trimmed).volume()));put(b/'design'/f'{p}.json',d)
 for fn in ['guards.npz','strict_magnet_guards.npz']:shutil.copy2(a/'verification'/fn,b/'verification'/fn)
g=geo(p,l);q=audit(p,l)
if q['native_review_resolved']:
 assert fit(p,l)['fit_and_pose_geometry_passed'];assert pick(p);print('TRIM406_PASS',flush=True)
