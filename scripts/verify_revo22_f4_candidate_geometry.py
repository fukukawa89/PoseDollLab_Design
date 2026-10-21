from pathlib import Path
import sys,json,hashlib,traceback,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins_v4 import solid,protected,md
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';F3=B/'O22F3_Release'
def check(pid,label):
 d=O/'candidates'/pid/label;n=np.load(d/'parts'/f'{pid}.npz');r=json.loads((d/'design'/f'{pid}.json').read_text(encoding='utf8'));old=np.load(F3/'reference/parts'/f'{pid}.npz');M=np.array(r['orientation']['matrix']);off=np.array(r['orientation']['source_translation_mm'])
 s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else md.Manifold();t=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else md.Manifold()
 body_same=np.array_equal(old['source_v'],n['source_v']) and np.array_equal(old['f'],n['f']) and np.max(abs(n['v']-(old['source_v']@M.T+off)))<1e-7 and abs(np.linalg.det(M)-1)<1e-7 and np.max(abs(M@M.T-np.eye(3)))<1e-7
 vols=next((x['volumes'] for x in GUARDS if x['part']==r['part']),[]);guard=protected(vols).transform(np.c_[M,off]);body_overlap=float((fin^s).volume());guard_overlap=float(((fin+t)^guard).volume())
 roots=[{'minimum_z_mm':float(q.bounding_box()[2]),'first_layer_area_mm2':float(q.slice(.1).area()),'teeth_connection_volume_mm3':float((q^t).volume())} for q in fin.decompose()]
 connections=[{'body_overlap_mm3':float((q^s).volume()),'fin_overlap_mm3':float((q^fin).volume())} for q in t.decompose()]
 unbraced=[q['number'] for q in r['segments'] if q['height_mm']>35 and q['brace_count']==0 and q['blade_thickness_mm']<q['height_mm']/12-.001]
 failures=[]
 if not body_same:failures.append('body_not_verified_as_original_rigid_transform')
 if any(str(q.status())!='Error.NoError' for q in [s,fin,t]):failures.append('mesh_boolean_status_error')
 if body_overlap>1e-6:failures.append('fin_body_penetration')
 if guard_overlap>1e-5:failures.append('functional_guard_penetration')
 if not all(q['minimum_z_mm']<1e-5 and q['first_layer_area_mm2']>.01 and q['teeth_connection_volume_mm3']>.005 for q in roots):failures.append('bed_root_or_fin_tooth_connection_missing')
 if not all(q['body_overlap_mm3']>.005 and q['fin_overlap_mm3']>.005 for q in connections):failures.append('tooth_not_connecting_both_sides')
 if unbraced:failures.append('tall_thin_panel_without_buttress')
 result={'id':pid,'label':label,'source_mesh_preserved':bool(body_same),'assembly_and_pose_geometry_unchanged':bool(body_same),'physical_strength_or_heat_simulation_performed':False,'fin_body_overlap_mm3':body_overlap,'functional_guard_overlap_mm3':guard_overlap,'fin_roots':roots,'tooth_components':connections,'unbraced_tall_thin_segments':unbraced,'failures':failures,'geometric_constraints_passed':not failures,'npz_sha256':hashlib.sha256((d/'parts'/f'{pid}.npz').read_bytes()).hexdigest()}
 (d/'verification/geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('CANDIDATE_GEOMETRY',pid,label,failures,flush=True);return result
GUARDS=json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text(encoding='utf8'))['objects']
if __name__=='__main__':
 choices=json.loads((O/'native_review_choices.json').read_text(encoding='utf8'));rows=[]
 for q in choices:
  try:rows.append(check(q['id'],q['label']))
  except Exception:rows.append({'id':q['id'],'label':q['label'],'error':traceback.format_exc()})
 (O/'candidate_geometry.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
 print('CANDIDATE_GEOMETRY_COMPLETE',len(rows),flush=True)
