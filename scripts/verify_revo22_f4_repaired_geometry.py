from pathlib import Path
import sys,json,hashlib,traceback,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins_v4 import solid,protected,md
from o22_material_components import material_components
from o22_mesh_identity import body_sha
from verify_revo22_f4_portal_layers import check as portal_layers
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';F3=B/'O22F3_Release'
def check(pid,label):
 d=O/'candidates'/pid/label;n=np.load(d/'parts'/f'{pid}.npz');r=json.loads((d/'design'/f'{pid}.json').read_text(encoding='utf8'));old=np.load(F3/'reference/parts'/f'{pid}.npz');M=np.array(r['orientation']['matrix']);off=np.array(r['orientation']['source_translation_mm'])
 s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else md.Manifold();t=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else md.Manifold()
 body_same=np.array_equal(old['source_v'],n['source_v']) and np.array_equal(old['f'],n['f']) and np.max(abs(n['v']-(old['source_v']@M.T+off)))<1e-7 and abs(np.linalg.det(M)-1)<1e-7 and np.max(abs(M@M.T-np.eye(3)))<1e-7
 vols=next((x['volumes'] for x in GUARDS if x['part']==r['part']),[]);guard=protected(vols).transform(np.c_[M,off]);body_overlap=float((fin^s).volume());guard_overlap=float(((fin+t)^guard).volume())
 roots=[{'minimum_z_mm':float(q.bounding_box()[2]),'first_layer_area_mm2':float(q.slice(.1).area()),'teeth_connection_volume_mm3':float((q^t).volume())} for q in material_components(fin)]
 connections=[{'body_overlap_mm3':float((q^s).volume()),'fin_overlap_mm3':float((q^fin).volume())} for q in material_components(t)]
 unbraced=[q['number'] for q in r['segments'] if q['height_mm']>35 and q['brace_count']==0 and q['blade_thickness_mm']<q['height_mm']/12-.001]
 failures=[]
 change_report=d/'verification/body_change_fit_and_pose.json';change=json.loads(change_report.read_text()) if change_report.exists() else {};source_reference_same=np.array_equal(old['source_v'],n['source_v']) and np.array_equal(old['f'],n.get('source_f',n['f']));authorized_change=source_reference_same and bool(change.get('fit_and_pose_geometry_passed',False)) and change.get('body_mesh_sha256')==body_sha(n)
 if not body_same and not authorized_change:failures.append('body_neither_preserved_nor_validated_change')
 if any(str(q.status())!='Error.NoError' for q in [s,fin,t]):failures.append('mesh_boolean_status_error')
 if body_overlap>1e-6:failures.append('fin_body_penetration')
 # Temporary fins may occupy an empty mating clearance, provided they can be removed vertically.
 tri=n['fin_v'][n['fin_f']];cr=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cr,axis=1)/2
 suspended_mask=(cr[:,2] < -1e-5)&(tri[:,:,2].min(axis=1)>1e-4)&(area>1e-6)
 suspended_down_area=float(area[suspended_mask].sum())
 portal_report=None
 if any(q.get('bed_connected_portal') for q in r['segments']):
  portal_report=portal_layers(fin,r);(d/'verification/portal_layer_growth.json').write_text(json.dumps(portal_report,indent=2))
  if not portal_report['passed']:failures.append('portal_fin_growth_or_bed_connection_failed')
 elif suspended_down_area>.001:failures.append('fin_has_downward_facing_surface_above_bed')
 if not all(q['minimum_z_mm']<1e-5 and q['first_layer_area_mm2']>.01 and q['teeth_connection_volume_mm3']>.005 for q in roots):failures.append('bed_root_or_fin_tooth_connection_missing')
 if not all(q['body_overlap_mm3']>.005 and q['fin_overlap_mm3']>.005 for q in connections):failures.append('tooth_not_connecting_both_sides')
 if unbraced:failures.append('tall_thin_panel_without_buttress')
 result={'id':pid,'label':label,'source_mesh_preserved':bool(body_same),'assembly_and_pose_geometry_unchanged':bool(body_same),'validated_permanent_body_change':authorized_change if not body_same else False,'body_change_validation':'body_change_fit_and_pose.json' if not body_same else None,'physical_strength_or_heat_simulation_performed':False,'fin_body_overlap_mm3':body_overlap,'temporary_support_occupying_assembly_clearances_mm3':guard_overlap,'fin_suspended_downface_area_mm2':suspended_down_area,'removal_policy':'Fins have no downward-facing area above the build plate, hence every fin column continues to the bed. After severing the short teeth they can withdraw toward the bed without crossing the unchanged part. Empty functional clearances must be completely cleaned before assembly.','fin_roots':roots,'tooth_components':connections,'unbraced_tall_thin_segments':unbraced,'failures':failures,'geometric_constraints_passed':not failures,'npz_sha256':hashlib.sha256((d/'parts'/f'{pid}.npz').read_bytes()).hexdigest()}
 if portal_report is not None:
  result['portal_layer_growth']=portal_report;result['removal_policy']='All fin components start at the bed. Wide portal panels route around intervening body material using independently checked 45-degree layer growth; they never rely on the body for their roots. Sever yellow teeth, cut the orange portal crown into separate sections, then remove the legs, buttresses and base joins. This is a cut-apart support frame, not a guaranteed single-direction extraction. Empty assembly clearances must be fully cleaned before assembly.'
 (d/'verification/geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('CANDIDATE_GEOMETRY',pid,label,failures,flush=True);return result
GUARDS=json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text(encoding='utf8'))['objects']
if __name__=='__main__':
 for spec in sys.argv[1:]:check(*spec.split(':'))
