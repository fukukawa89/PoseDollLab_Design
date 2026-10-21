from pathlib import Path
import sys,json,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import repair_revo22_f3_side_contacts as side
import check_revo22_f3_layers as layer
from slice_revo22_f4_candidate import run
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
def repair(pid,label):
 src=O/'candidates'/pid/label;dest=O/'candidates'/pid/(label+'_repair')
 assert not dest.exists(),dest
 for sub in ['parts','design','verification']:(dest/sub).mkdir(parents=True,exist_ok=True)
 for sub,ext in [('parts','npz'),('design','json')]:shutil.copy2(src/sub/f'{pid}.{ext}',dest/sub/f'{pid}.{ext}')
 d=json.loads((src/'verification/local_extrusion.json').read_text(encoding='utf8'));p=json.loads((src/'verification/plate_manifest.json').read_text(encoding='utf8'));targets=d['detached_bead_regions'].copy()
 for r in d['unresolved_spans']:
  bb=r['bounds_mm'];targets.append({'z_mm':r['z_mm'],'area_mm2':r['length_mm']*r['mean_width_mm'],'bounds_mm':[bb[0]-.04,bb[1]-.04,bb[2]+.04,bb[3]+.04]})
 (dest/'verification'/f'QC_{pid}_ORCA_extrusion_contacts.json').write_text(json.dumps({'floating_printed_components':targets,'note':'Targets for experimental support repair; includes local overhang spans as well as wholly detached regions. Not a passed extrusion report.'}),encoding='utf8')
 (dest/'verification'/f'QC_{pid}_ORCA_manifest.json').write_text(json.dumps(p,ensure_ascii=False),encoding='utf8')
 side.O=dest;layer.O=dest;layer.check(pid);side.repair_side(pid)
 return run(pid,label+'_repair')
if __name__=='__main__':repair(sys.argv[1],sys.argv[2])
