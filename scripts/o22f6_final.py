"""O22F6 PLA release: retain cleared supports and restore only unresolved F5 types.

User authorized original removable supports in holes on 2026-10-15 if clearance
could not be made printable. All original permanent bodies and plate placements
are retained. Release requires full final-native path screening on all 14 plates.
"""
from pathlib import Path
import sys,json,shutil,copy,argparse,concurrent.futures,time
import numpy as np
import o22f6_holeclear as h

CAND=h.B/'O22F6_HoleClear';HISTORY=h.B/'diagnostics/O22F6_holeclear_20261015'
OUT=h.B/'O22F6_PLA_Final';WORK=h.B/'diagnostics/O22F6_final_20261015'
RESTORE=frozenset('P095 X058 P073 X038 X046 W007 X066 X062 P117 W016 P035 P071 P051 P093 P130 W017'.split())

def configure():
 h.OUT=OUT;h.WORK=WORK;h.PROJECT_SUFFIX='PLA_final';h.PRINT_SETTINGS_ID='O22-F6 Final / A1 mini PLA 0.4';h.ORIGINAL_PROFILE_IDS=RESTORE;h.SCREEN_LABEL='finalpla';h.TARGET_PART_IDS=None

def manifest():return json.loads((h.SRC/'manifest.json').read_text(encoding='utf-8'))

def stage():
 configure();assert not (OUT/'manifest.json').exists(),'Final package already exists; do not overwrite released files'
 for sub in ['parts','design','projects','verification']:(OUT/sub).mkdir(parents=True,exist_ok=True)
 for sub in ['guards','initial']:shutil.copytree(HISTORY/sub,WORK/sub,dirs_exist_ok=True)
 for name in ['initial_summary.json','inventory.json','rejected_experiment_summary.json']:
  if (HISTORY/name).exists():shutil.copy2(HISTORY/name,WORK/name)
 old_summary=json.loads((CAND/'verification/summary.json').read_text());affected={i for p in old_summary['plate_results']for i in p['affected_parts']};assert affected==RESTORE,(affected,RESTORE)
 old_overrides=json.loads((HISTORY/'profile_overrides.json').read_text());h.put(WORK/'profile_overrides.json',{k:v for k,v in old_overrides.items()if k not in RESTORE})
 rows=[]
 for r in manifest()['rows']:
  pid=r['id'];source=h.SRC if pid in RESTORE else CAND
  shutil.copy2(source/f'parts/{pid}.npz',OUT/f'parts/{pid}.npz');d=json.loads((source/f'design/{pid}.json').read_text())
  d.update(f6_status='staging_not_released',physical_print_tested=False,f6_support_policy='original_F5_restored_for_printability'if pid in RESTORE else 'fastener_clearance_retained',native_pending=True)
  if pid in RESTORE:d.update(connector_void_policy='removable_support_may_occupy_fastener_clearance_user_authorized',removable_core_may_transit_empty_hardware_space=True,f5_tooth_records_are_historical=False)
  h.put(OUT/f'design/{pid}.json',d)
  rows.append(dict(id=pid,support_source=source.name,npz_sha256=h.sha(OUT/f'parts/{pid}.npz'),restored=pid in RESTORE))
 h.put(WORK/'staging.json',dict(status='NOT_RELEASED',user_authorized_fallback=True,restore_ids=sorted(RESTORE),candidate_manifest_sha256=h.sha(CAND/'manifest.json'),source_manifest_sha256=h.sha(h.SRC/'manifest.json'),rows=rows))
 print('STAGED',len(rows),'types;',len(RESTORE),'restored',flush=True)

def build_one(p):configure();return h.build_plate(p)
def screen_one(p):configure();return h.screen_plate(p)
def holes_one(p):
 configure();import o22f6_deposited_holes as dh
 dh.OUT=OUT;dh.WORK=WORK;dh.PROJECT_SUFFIX=h.PROJECT_SUFFIX
 return dh.check(p)

def clearholes_one(p):
 configure();import o22f6_deposited_holes as dh
 dh.OUT=OUT;dh.WORK=WORK;dh.PROJECT_SUFFIX=h.PROJECT_SUFFIX;dh.GUARD_PART_IDS={r['id']for r in manifest()['rows']}-RESTORE;dh.REPORT_NAME='deposited_retained_clearance.json'
 return dh.check(p)

def geometry_one(r):
 configure();pid=r['id'];path=OUT/f'parts/{pid}.npz';oldpath=h.SRC/f'parts/{pid}.npz';a=np.load(path);b=np.load(oldpath);assert h.sha(oldpath)==r['npz_sha256']
 assert np.array_equal(a['v'],b['v'])and np.array_equal(a['f'],b['f']),(pid,'body_changed')
 body=h.solid(a['v'],a['f']);fin=h.solid(a['fin_v'],a['fin_f']);teeth=h.solid(a['teeth_v'],a['teeth_f']);g=np.load(WORK/f'guards/{pid}.npz');guard=h.solid(g['v'],g['f']);support=fin+teeth;overlap=max(0.,float((support^guard).volume()));initial=json.loads((WORK/f'initial/{pid}.json').read_text());fins=h.material_components(fin);cc=h.material_components(body+support)
 assert len(cc)==len(h.material_components(body)),(pid,'disconnected_geometry')
 assert all(c.bounding_box()[2]<1e-5 and c.slice(.05).area()>.005 for c in fins),(pid,'unrooted_fin')
 assert (fin^body).volume()<1e-6,(pid,'fin_body_overlap')
 if pid in RESTORE:
  assert h.sha(path)==h.sha(oldpath),(pid,'restore_not_exact')
  assert abs(overlap-initial['support_in_fastener_clearance_mm3'])<1e-5
 else:assert overlap<1e-6,(pid,'unexpected_hole_occupation',overlap)
 result=dict(id=pid,npz_sha256=h.sha(path),source_npz_sha256=h.sha(oldpath),body_vertices_and_faces_identical_to_F5=True,original_F5_support_restored=pid in RESTORE,guard_count=initial['guard_count'],before_support_in_guard_mm3=initial['support_in_fastener_clearance_mm3'],after_support_in_guard_mm3=overlap,all_fins_bed_rooted=True,fin_count=len(fins),connected_material_components=len(cc),support_volume_mm3=float(support.volume()),support_geometry_changed=h.sha(path)!=h.sha(oldpath),physical_print_tested=False)
 h.put(WORK/f'geometry/{pid}.json',result);print('GEOMETRY',pid,'restored'if pid in RESTORE else'clear',round(overlap,6),flush=True);return result

def run(action,ids=None):
 configure();m=manifest();rows=m['rows']if action=='geometry'else m['plates'];rows=[r for r in rows if not ids or r['id']in ids];fn=dict(build=build_one,screen=screen_one,holes=holes_one,clearholes=clearholes_one,geometry=geometry_one)[action];results=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for result in pool.map(fn,rows):results.append(result)
 if action=='geometry':h.put(WORK/'geometry_verification.json',dict(all_bodies_identical_to_F5=True,rows=results))
 print('COMPLETE',action,len(rows),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['stage','build','screen','holes','clearholes','geometry']);ap.add_argument('--ids',nargs='*');a=ap.parse_args()
 if a.action=='stage':stage()
 else:run(a.action,a.ids)