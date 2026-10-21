import json,shutil,hashlib
from pathlib import Path
from search_revo22_f5_orientation268 import O,put
from stage_revo22_f5_compact296 import S
sel=json.loads((O/'plate_repair_P130_447.json').read_text());put(O/'selections/P130.json',sel);q=O/'candidates/P130'/sel['label']
for sub,ext in [('parts','npz'),('design','json')]:shutil.copy2(q/sub/f'P130.{ext}',S/sub/f'P130.{ext}')
for fn in ['f5_geometry.json','native_final.json','construction.json','f5_fin_groups.npz','guards.npz','strict_magnet_guards.npz']:shutil.copy2(q/'verification'/fn,S/'verification/types/P130'/fn)
frozen=json.loads((S/'frozen_selection.json').read_text());frozen['P130']=dict(sel,npz_sha256=hashlib.sha256((S/'parts/P130.npz').read_bytes()).hexdigest(),geometric_proof=json.loads((q/'verification/f5_geometry.json').read_text()));put(S/'frozen_selection.json',frozen)
p=Path(__file__).parent/'stage_revo22_f5_compact296.py';s=p.read_text(encoding='utf-8-sig');s=s.replace("'P071','P130']else[0,1]","'P071','P130','X050']else[0,1]");p.write_text(s,encoding='utf-8')
p=Path(__file__).parent/'propose_revo22_f5_layer446.py';s=p.read_text(encoding='utf-8-sig');s=s.replace("i=copy.deepcopy(old);d=", "i=copy.deepcopy(old);nn=np.load(S/'parts'/f\"{i['id']}.npz\");vv=np.r_[nn['v'],nn['fin_v'],nn['teeth_v']];i.update(size=np.ptp(vv,axis=0).tolist(),local_bounds_mm=np.r_[vv.min(0),vv.max(0)].tolist());d=");p.write_text(s,encoding='utf-8')
