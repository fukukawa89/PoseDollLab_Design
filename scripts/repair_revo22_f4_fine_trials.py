import json,sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import package_revo22_fins_v4 as pack
from slice_revo22_f4_candidate import run
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
for pid in sys.argv[1:]:
 src=O/'candidates'/pid/'contact_repair_01';label='contact_fine_01';dest=O/'candidates'/pid/label
 for sub,ext in [('parts','npz'),('design','json')]:
  (dest/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dest/sub/f'{pid}.{ext}')
 (dest/'verification').mkdir(exist_ok=True);pack.PROCESS_LAYER_HEIGHT=.12;run(pid,label)
