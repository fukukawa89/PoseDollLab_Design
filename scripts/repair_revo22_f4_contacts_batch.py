from pathlib import Path
import sys,json,shutil,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f4_side_contacts as side
import check_revo22_f3_layers as layer
from slice_revo22_f4_candidate import run
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
def repair(pid,label,dlabel):
 src=O/'candidates'/pid/label;dest=O/'candidates'/pid/dlabel
 if (dest/'verification/local_extrusion.json').exists():return
 for sub in ['parts','design','verification']:(dest/sub).mkdir(parents=True,exist_ok=True)
 for sub,ext in [('parts','npz'),('design','json')]:shutil.copy2(src/sub/f'{pid}.{ext}',dest/sub/f'{pid}.{ext}')
 d=json.loads((src/'verification/local_extrusion.json').read_text());p=json.loads((src/'verification/plate_manifest.json').read_text());targets=d['detached_bead_regions'].copy();seen=set()
 for r in sorted(d['unresolved_spans'],key=lambda x:-x['max_centerline_distance_from_backing_mm']):
  if r['max_centerline_distance_from_backing_mm']<.12:continue
  bb=r['bounds_mm'];key=tuple(round(x/.7) for x in [r['z_mm'],*bb])
  if key in seen:continue
  seen.add(key);targets.append({'z_mm':r['z_mm'],'area_mm2':r['length_mm']*r['mean_width_mm'],'bounds_mm':[bb[0]-.04,bb[1]-.04,bb[2]+.04,bb[3]+.04]})
 (dest/'verification'/f'QC_{pid}_ORCA_extrusion_contacts.json').write_text(json.dumps({'floating_printed_components':targets,'note':'Targets for support repair; includes local overhang spans. Not an accepted print report.'}))
 (dest/'verification'/f'QC_{pid}_ORCA_manifest.json').write_text(json.dumps(p,ensure_ascii=False),encoding='utf8')
 side.O=dest;layer.O=dest;side.check=lambda _:None;layer.check(pid);side.repair_side(pid)
 return run(pid,dlabel)
if __name__=='__main__':
 for spec in sys.argv[1:]:
  pid,label,dlabel=spec.split(':');print('REPAIR_START',pid,label,dlabel,flush=True);repair(pid,label,dlabel)
