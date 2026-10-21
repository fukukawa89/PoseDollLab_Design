from pathlib import Path
import sys,json,shutil,time
import numpy as np
from shapely.geometry import LineString
from o22_cross_section_geometry import polygon
from build_revo22_fins import solid,union
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f4_steep_contacts as side
import check_revo22_f3_layers as layer
from slice_revo22_f4_candidate import run
from o22_native_region_context import context
from o22_recover_native_flag_paths import recover
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def repair(pid,label,newlabel):
 src=O/'candidates'/pid/label;dst=O/'candidates'/pid/newlabel
 if (dst/'verification/local_extrusion.json').exists():return
 for sub,ext in [('parts','npz'),('design','json')]:
  (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
 (dst/'verification').mkdir(exist_ok=True);rep=json.loads((src/'verification/local_extrusion.json').read_text());d=recover(pid,label);ctx=context(pid,label);contexts=[q['context'] for q in ctx['regions'] if q['kind']=='span'];targets=rep['detached_bead_regions'].copy();seen=set();nn=np.load(src/'parts'/f'{pid}.npz');it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];whole=union([solid(nn[v],nn[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(nn[f])]).transform(np.c_[np.array(it['rotation_matrix']),np.array(it['translation_mm'])]);pcache={}
 for r,ct in zip(d['records'],contexts):
  if ct=='inside_prior_solid_infill_region':continue
  # Prior-layer-only centerline flags can still have partial bead overlap. Target fully air regions first.
  if r['max_centerline_distance_from_backing_mm']<=max(.12,r['mean_width_mm']/2-.025):continue
  ln=LineString(r['xy_mm']);zk=round(r['z_mm'],4)
  if zk not in pcache:pcache[zk]=polygon(whole.slice(max(.01,zk-.3))).buffer(.015)
  if pcache[zk].covers(ln):continue
  for dl in np.linspace(0,ln.length,max(2,int(np.ceil(ln.length/1.2))+1)):
   p=ln.interpolate(dl);key=tuple(round(x/.35) for x in [p.x,p.y,r['z_mm']])
   if key in seen:continue
   seen.add(key);targets.append({'z_mm':r['z_mm'],'bounds_mm':[p.x-.4,p.y-.4,p.x+.4,p.y+.4],'point_mm':[p.x,p.y]})
 (dst/'verification'/f'QC_{pid}_ORCA_extrusion_contacts.json').write_text(json.dumps({'floating_printed_components':targets}));shutil.copy2(src/'verification/plate_manifest.json',dst/'verification'/f'QC_{pid}_ORCA_manifest.json');side.O=dst;layer.O=dst;side.check=lambda _:None;layer.check(pid);side.repair_side(pid);run(pid,newlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:repair(*spec.split(':'))
