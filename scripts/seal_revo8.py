"""Seal O8 research artifacts without upgrading their engineering acceptance state."""
import argparse,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO8/runs/o8_20260925_r1';DEST=G/'evidence_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');a=ap.parse_args()
 if a.verify:
  data=read(DEST);errors=[]
  for rel,d in data['repository_files_sha256'].items():
   p=R/rel
   if not p.is_file() or sha(p)!=d:errors.append(rel)
  print(json.dumps({'repository_artifacts_verified':not errors,'checked_hashes':len(data['repository_files_sha256']),'errors':errors,'physical_tested':False,'manufacturing_released':False}));sys.exit(bool(errors))
 ref=read(G/'reference/core_motion.json');search=read(G/'fork_search.json');clearance=read(G/'fork_clearance.json');fast=read(G/'fastened_core/report.json');assembly=read(G/'assembly_path.json');sensor=read(G/'sensor_observability.json');mapping=read(G/'shoulder_mapping.json');reg=read(G/'collision_regression.json');web=read(H/'tutorials/tut-prototype/verification/checks.json');gauges=read(H/'bench/revO8/fit_gauges/manifest.json')
 assert (ref['pass_cases'],ref['fail_cases'],ref['review_cases'])==(89,8,0)
 assert [(x['extension_mm'],x['pass'],x['fail'],x['review']) for x in search['candidates']]==[(0,5,16,0),(1,9,12,0),(2,9,12,0),(3,13,8,0),(4,17,4,0)]
 assert len([c for c in clearance['cases'] if c['extension_mm']==2 and c['status']=='CERTIFIED_NOMINAL_CLEARANCE'])==5
 assert all(r['status']!='PENETRATION' for r in fast['ring_fits'])
 assert all(r['status']=='CLEAR_FASTENERS_ONLY' for r in fast['motion_cases'])
 assert all(r['clear_straight_shaft_pose'] is not None for r in fast['tool_access'])
 assert all(c['status']=='PASS_DISCRETE_ASSEMBLY_STEP' for r in assembly['stages'] for c in r['cases'])
 assert sensor['roundtrip_cases']==189 and reg['pass']==19 and web['status']=='PASS'
 assert all(len(r['paths'])==51 and r['reconstruction_matrix_max_error']<1e-10 for r in mapping['characters'])
 assert len(gauges['parts'])==4 and sum(x['quantity'] for x in gauges['parts'])==6
 # Both external upstream file and the locally reconstructed input are locked here.
 original=R.parent/'research/tangible_reuse_20260925/atamid/Hardware/Mechanics/jointTUT.stl';expected='05bc819a65068a68afdb275a639b267ba840d8e2f574fd21368b655a3bf570e0';assert sha(original)==expected
 sourcefiles=[H/'cad/model.py',H/'research/tangible_2014_2016/audit_sources.py',H/'research/tangible_2014_2016/evidence.json',H/'generated/revO7/runs/o7_20260924_r1/bilateral_current/layout_search.json']
 sourcefiles+=list((H/'generated/revO7/runs/o7_20260924_r1/bilateral_current').glob('*_profile.json'))
 sourcefiles+=[H/'docs/O8_TUT_PROTOTYPE.zh-CN.md',Path(__file__)]
 files=set(sourcefiles)
 for d in (H/'cad/revO8',G,H/'bench/revO8',H/'tutorials/tut-prototype'):
  files.update(p for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.log','.pyc') and p!=DEST)
 # STEP/STL integrity is checked after binary STL export as well as before it.
 sys.path.insert(0,str(H/'cad/revO8'));from extend_forks import topology
 from reference_features import read_stl
 roundtrips=[]
 for folder in (G/'fork_extension_2mm',H/'bench/revO8/fit_gauges'):
  for p in folder.glob('*.stl'):
   t=read_stl(p);c=topology(t);assert not any(c[k] for k in ('boundary_edges','nonmanifold_edges','zero_area_faces')),(p,c);roundtrips.append({'file':p.relative_to(R).as_posix(),'topology':c})
 summary={'reference_core_discrete_cases':len(ref['cases']),'reference_pass_fail':[ref['pass_cases'],ref['fail_cases']],'fork_search_cases':sum(len(c['cases']) for c in search['candidates']),'fastener_only_cases':len(fast['motion_cases']),'assembly_translation_samples':sum(len(s['cases']) for s in assembly['stages']),'rotation_mappings':sum(len(c['paths']) for c in mapping['characters']),'neutral_to_pose_samples':sum(c['physical_path_samples'] for c in mapping['characters']),'max_sampled_bend_deg':max(c['max_bend_deg'] for c in mapping['characters']),'collision_method_regressions':reg['pass'],'sensor_ideal_roundtrips':sensor['roundtrip_cases'],'web_groups':len(web['checks'])}
 out={'schema':'revo8-research-evidence-v1','run_id':'o8_20260925_r1','status':'SCOPED_DIGITAL_EXPERIMENTS_COMPLETE_AWAITING_PROCESS_FIT_SAMPLES','summary':summary,'repository_files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'external_source_at_seal':{'repository':'https://github.com/oliglauser/atamid','commit':'9a152b1d82374d1960ebd2216563fb30b1b6875b','path':'Hardware/Mechanics/jointTUT.stl','sha256':expected,'verified_on_local_source':True},'stl_binary_roundtrip_checks':roundtrips,'superseded_history':['reference/core_motion_initial_registration.json is the incorrect initial pivot registration, not a final reference-design failure.'],'scope':'Hashes lock stored evidence; they do not prove physical performance, full TUT assembly, fit, strength, calibrated sensing or full-arm clearance. --verify checks repository files; external upstream source is checked at seal creation.','physical_tested':False,'full_joint_pass':False,'full_body_pass':False,'manufacturing_released':False}
 DEST.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(files),'summary':summary}))
if __name__=='__main__':main()
