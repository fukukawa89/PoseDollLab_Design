from pathlib import Path
import sys,json,shutil
import numpy as np
from shapely.geometry import LineString
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f4_low_wide_contacts as side
import check_revo22_f3_layers as layer
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def repair(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 for sub,ext in [('parts','npz'),('design','json')]:
  (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
 (dst/'verification').mkdir(exist_ok=True)
 if not (src/'verification/full_bead_contacts.json').exists():check(pid,label)
 d=json.loads((src/'verification/full_bead_contacts.json').read_text());targets=[]
 for q in d['external_islands']:
  b=q['bounds_mm'];targets.append(dict(q,point_mm=[(b[0]+b[2])/2,(b[1]+b[3])/2]))
 for q in d['external_free_runs']:
  if q['length_mm']<.5:continue
  g=LineString(q['xy_mm'])
  for dist in np.linspace(0,g.length,max(2,int(np.ceil(g.length/.65))+1)):
   p=g.interpolate(dist);targets.append({'z_mm':q['z_mm'],'bounds_mm':[p.x-.4,p.y-.4,p.x+.4,p.y+.4],'point_mm':[p.x,p.y]})
 (dst/'verification'/f'QC_{pid}_ORCA_extrusion_contacts.json').write_text(json.dumps({'floating_printed_components':targets}));shutil.copy2(src/'verification/plate_manifest.json',dst/'verification'/f'QC_{pid}_ORCA_manifest.json');side.O=dst;layer.O=dst;side.check=lambda _:None;layer.check(pid);side.repair_side(pid);run(pid,newlabel);return check(pid,newlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:repair(*spec.split(':'))
