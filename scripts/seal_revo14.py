"""O14 final consistency snapshot; never a full-body or print-process release."""
from pathlib import Path
import json,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO14/runs/o14_20260929_r1';B=H/'bench/revO14';DEST=G/'evidence_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 u=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/seal_revo13.py'),'--verify'],capture_output=True,text=True,encoding='utf-8',cwd=R);assert u.returncode==0,u.stdout+u.stderr;old=json.loads(u.stdout)
 if '--verify' in sys.argv:
  d=read(DEST);bad=[n for n,h in d['repository_files_sha256'].items() if not (R/n).is_file() or sha(R/n)!=h]
  optional_bad=[n for n,h in d['local_diagnostic_files_sha256'].items() if (R/n).is_file() and sha(R/n)!=h]
  print(json.dumps({'verified':not bad and not optional_bad,'files':len(d['repository_files_sha256']),'errors':bad,'local_errors':optional_bad,'upstream_O13_verified':old['verified'],'full_body_manufacturing_released':False}));raise SystemExit(bool(bad or optional_bad))
 assert not DEST.exists(),'Use a new run after sealing.'
 c=read(G/'collision_classification.json');assert len(c['cases'])==102 and c['structural_failure_endpoints']==0 and c['pose_contact_endpoints']==12 and not c['complete_body_structural_gate_passed']
 t=read(G/'shoulder_width_trials.json');assert t['complete'] and t['shoulder_shift_per_side_mm']==0 and set(t['candidates'][t['selected']]['single_integrated_components'].values())=={1}
 refs=read(G/'reference_deviations.json');assert all(abs(p['shoulder_width_reference_mm']-p['shoulder_width_current_mm'])<1e-8 and len(p['axis_origins'])==44 and all(abs(a['delta_mm'])<1e-8 for a in p['main_arm_segment_lengths']) for p in refs['profiles'])
 for r in (c,refs,read(G/'reference_deviations_o13.json')):
  for n,h in r['inputs_sha256'].items():assert sha(H/n)==h,n
 bed=read(G/'bed_geometry.json');assert not bed['mechanical_geometry_changed'] and bed['source_core_sha256']==sha(H/'generated/revO13/runs/o13_20260929_r1/printed_core/parts.npz')
 for p in bed['parts']:
  assert p['new']['flat_contact_area_mm2']>90
  if p['part'] in ('C01','C02'):assert p['old']['flat_contact_area_mm2']==0 and not p['new']['COM_over_unsupported_part_contact_hull']
 s=read(G/'slicing/report.json');assert s['actual_slicing'] and not s['actual_printer_profile'] and not s['physically_printed'] and len(s['rows'])==4
 assert sha(B/'generic_diagnostic_NOT_MACHINE_PROFILE.ini')==s['config_sha256']
 for row in s['rows']:
  assert row['exit_code']==0 and row['support_extrusion_segments']>0 and row['final_model_COM_in_model_plus_support_first_layer_hull'] and row['extrusion_progress_centroids_in_hull']
  assert sha(B/'print_beds'/f"{row['part']}_flat_face.stl")==row['stl_sha256']
 q=read(G/'page_checks.json');assert q['status']=='PASS' and not q['errors'] and not q['badResponses'] and not q['viewer']['sceneAudit']['missing'] and q['viewer']['sceneAudit']['glError']==0
 assert q['guide']['mobile']['images']==[True]*4 and not q['guide']['mobile']['replacementCharacters'] and all(x['status']==200 for x in q['guide']['links'])
 assert all(x['mobile']['scrollWidth']<=x['mobile']['width'] for x in (q['guide'],q['viewer']))
 files={Path(__file__),R/'scripts/serve_posedoll_tutorials.py',H/'docs/O14_REFERENCE_COLLISION_PRINT.zh-CN.md',H/'mechanical_manifest/requirements_revO14.json',H/'generated/revO13/runs/o13_20260929_r1/evidence_manifest.json'}
 for root in (H/'cad/revO14',B,H/'tutorials/full-doll-o14',H/'tutorials/core-print'):
  files.update(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 files.update(p for p in G.rglob('*') if p.is_file() and p!=DEST and p.suffix in ('.json','.npz'))
 for r in (c,refs):files.update(H/n for n in r['inputs_sha256'])
 local={p.relative_to(R).as_posix():sha(p) for p in (G/'slicing').glob('*') if p.suffix in ('.gcode','.ini','.log')}
 d={'schema':'o14-final-consistency-snapshot-v1','repository_files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'local_diagnostic_files_sha256':local,'local_artifacts_note':'Diagnostic G-code/config/logs may be excluded from Git; recreate with slice_core.py and the official PrusaSlicer portable tool. Never print this generic G-code.','upstream_O13_verified':old['verified'],'status':'SHOULDER_WIDTH_RESTORED_ADJACENCY_CLASSIFIED_SUPPORTED_SLICING_AND_UI_CHECKED','scope':'Final consistency and stated report dependencies. Not a per-read exploration log, a continuous motion proof, an actual-machine print test or a full-body release.','anatomical_mismatch_limit_approved_mm':None,'structural_endpoint_failures':0,'nonadjacent_contact_endpoints':12,'full_body_manufacturing_released':False}
 DEST.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(files),'upstream_O13_verified':old['verified'],'status':d['status']}))
if __name__=='__main__':main()
