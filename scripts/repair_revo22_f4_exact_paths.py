from pathlib import Path
import sys,json,shutil
import numpy as np
from shapely.geometry import LineString
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f4_path_contacts as side
import check_revo22_f3_layers as layer
from slice_revo22_f4_candidate import run
from verify_revo22_f4_ordered_contacts import check as ordered
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def repair(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 for sub,ext in [('parts','npz'),('design','json')]:
  (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
 (dst/'verification').mkdir(exist_ok=True)
 if not (src/'verification/ordered_contacts.json').exists():ordered(pid,label)
 d=json.loads((src/'verification/ordered_contacts.json').read_text());targets=d['detached_bead_regions'].copy();seen=set()
 for r in d['unresolved']:
  if r['inside_previous_solid']:continue
  ln=LineString(r['xy_mm'])
  for dl in np.linspace(0,ln.length,max(2,int(np.ceil(ln.length/.9))+1)):
   p=ln.interpolate(dl);key=tuple(round(x/.25) for x in [p.x,p.y,r['z_mm']])
   if key in seen:continue
   seen.add(key);targets.append({'z_mm':r['z_mm'],'bounds_mm':[p.x-.4,p.y-.4,p.x+.4,p.y+.4],'point_mm':[p.x,p.y]})
 (dst/'verification'/f'QC_{pid}_ORCA_extrusion_contacts.json').write_text(json.dumps({'floating_printed_components':targets}))
 shutil.copy2(src/'verification/plate_manifest.json',dst/'verification'/f'QC_{pid}_ORCA_manifest.json');side.O=dst;layer.O=dst;side.check=lambda _:None;layer.check(pid);side.repair_side(pid);run(pid,newlabel);ordered(pid,newlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:repair(*spec.split(':'))
