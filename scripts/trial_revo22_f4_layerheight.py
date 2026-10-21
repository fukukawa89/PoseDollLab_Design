from pathlib import Path
import sys,json,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import package_revo22_fins_v4 as pack
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
for spec in sys.argv[1:]:
 pid,source,height=spec.split(':');label='layer_'+height.replace('.','p')+'_06';src=O/'candidates'/pid/source;dest=O/'candidates'/pid/label
 for sub,ext in [('parts','npz'),('design','json')]:
  (dest/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dest/sub/f'{pid}.{ext}')
 (dest/'verification').mkdir(exist_ok=True)
 for name in ['body_change_fit_and_pose.json','washer_contact_surfaces.json']:
  if (src/'verification'/name).exists():shutil.copy2(src/'verification'/name,dest/'verification'/name)
 p=dest/'design'/f'{pid}.json';d=json.loads(p.read_text());d['required_layer_height_mm']=float(height);d['slicing_trial_parent']=source;p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');pack.PROCESS_LAYER_HEIGHT=float(height);run(pid,label);check(pid,label)
