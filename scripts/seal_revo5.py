"""Seal O5 digital evidence without changing O1-O4 or committing either repository.
Verification reads delivered archives in place; it does not overwrite a checkout.
"""
from pathlib import Path
import argparse,datetime,difflib,hashlib,importlib.metadata,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
HW=ROOT/'Hardware/PoseDoll44'
RUN=HW/'verification/revO5/runs/o5_20260924_r1'
OUT=HW/'verification/revO5/deliveries/o5_20260924_d1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL)
def archive(path,files,base):
 with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(set(files)):z.write(p,p.relative_to(base).as_posix())
 with zipfile.ZipFile(path) as z:return {n:digest(z.read(n)) for n in z.namelist()}
def verify():
 m=read(OUT/'DELIVERY_MANIFEST.json');errors=[];checked=0
 for path,h in m['files_sha256'].items():
  p=ROOT/path;checked+=1
  if not p.is_file() or sha(p)!=h:errors.append(path)
 for path,members in m['archives'].items():
  with zipfile.ZipFile(ROOT/path) as z:
   assert set(z.namelist())==set(members),path
   for name,h in members.items():
    checked+=1
    if digest(z.read(name))!=h:errors.append(path+'!'+name)
 print(json.dumps({'verified':not errors,'checked_hashes':checked,'errors':errors,'physical_tested':False,'manufacturing_released':False}))
 return int(bool(errors))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');ap.add_argument('--ue-root',type=Path);a=ap.parse_args()
 if a.verify:return verify()
 assert a.ue_root,'--ue-root is required for sealing'
 ue=a.ue_root.resolve();assert not (OUT/'DELIVERY_MANIFEST.json').exists(),'Use a new delivery id, do not overwrite a seal'
 OUT.mkdir(parents=True,exist_ok=True);lock=read(RUN/'source_lock_revO5.json')
 assert git(ROOT,'rev-parse','HEAD').decode().strip()==lock['repositories']['design']['head']
 assert git(ue,'rev-parse','HEAD').decode().strip()==lock['repositories']['ue']['head']
 # All captured historical design sources, old delivery bytes, review inputs and user edits are immutable.
 for path,h in lock['repositories']['design']['sources_sha256'].items():assert sha(ROOT/path)==h,path
 for repo,base in [('design',ROOT),('ue',ue)]:
  for path,h in lock['repositories'][repo]['user_uncommitted_sha256'].items():assert sha(base/path)==h,path
 old=read(HW/'verification/revO4/deliveries/o4_20260924_d1/DELIVERY_MANIFEST.json')
 for path,h in old['files_sha256'].items():assert sha(ROOT/path)==h,path
 for path,h in lock['review_package_sha256'].items():assert sha(HW/'docs/revO5_review_source'/path)==h,path
 # Tests ran in an isolated UE project; every compiled plugin source must still match.
 isolated=ROOT/'.local/o5_ue_project';compiled={}
 for p in (ue/'Plugins/PoseDoll/Source').rglob('*'):
  if p.is_file():
   name=p.relative_to(ue).as_posix();assert sha(p)==sha(isolated/name),name;compiled[name]=sha(p)
 for src,dest in [('reports/o5/late_editor.json','late_editor.json'),('reports/o5/bridge_editor.json','bridge_editor.json'),('reports/o4/o5_baseline_regression/editor.json','editor_regression.json'),('reports/o4/o5_baseline_regression/reopen.json','reopen.json')]:
  data=(isolated/src).read_bytes();assert json.loads(data)['passed'];(RUN/dest).write_bytes(data)
 automation=read(RUN/'ue_automation/index.json');assert automation['succeeded']==5 and not automation['failed']
 for file,needle in [('ue_build_nonunity.txt','Result: Succeeded'),('ue_build_unity.txt','Result: Succeeded'),('python_router.txt','75 passed'),('hardware_bridge_tests.txt','24 passed'),('remote_runtime_final.txt','PASS'),('gateway_native.txt','PASS')]:assert needle in (RUN/file).read_text(encoding='utf-8',errors='replace'),file
 builds=read(RUN/'idf_release_builds.json');assert len(builds['builds'])==7 and all(r['exit']==0 for r in builds['builds'])
 # PDR4 runtime is separately compiled by host C tests; it is not linked into the A firmware.
 idf_inputs={k:h for k,h in builds['sources'].items() if not any(x in k for x in ['remote_link','remote_runtime','test_'])}
 idf_inputs['Firmware/PoseDollFullBody/main/pd41_config.h']=lock['repositories']['design']['sources_sha256']['Firmware/PoseDollFullBody/main/pd41_config.h']
 for p,h in idf_inputs.items():assert sha(ROOT/p)==h,p
 arm_path=HW/'generated/revO5/runs/o5_20260924_r1/arm/shared_arm_screen.json';arm=read(arm_path)
 for p,h in arm['input_sha256'].items():assert sha(ROOT/p)==h,p
 power=read(RUN/'power_budget_arm_revO5.json');assert power['shared_arm_draft']['source_sha256']==sha(arm_path)
 assert all(v['neutral']['exact_counterexamples'][0]['intersection_mm3']>0 for c in arm['characters'] for v in c['variants'])
 golden=ROOT/'Tools/PoseDollHardwareBridge/tests/pdg5_golden.bin';assert sha(golden)==sha(ROOT/'.local/o5_gateway_r1/pdg5_golden.bin')
 findings=[]
 for c in arm['characters']:
  for v in c['variants']:findings.append({'character':c['character'],'variant':v['variant'],'poses':len(v['cases']),'max_J50_draft_mm':v['max_J50_draft_length_mm'],'neutral_counterexamples':v['neutral']['exact_counterexamples']})
 result={'schema':'o5-digital-delivery-v1','run_id':'o5_20260924_r1','user_scope':'No hardware available; digital work only','tested':{'ue_builds':['non-unity','forced-unity'],'ue_automation_groups':5,'ue_python_tests':75,'bridge_python_tests':24,'native_C':['PDR4 codec/runtime','PDG5/PDC5 acquisition/codec'],'idf_roles':[r['role'] for r in builds['builds']],'late_editor_cases':8,'bridge_editor_cases':4,'original_editor_regression':True,'fresh_process_reopen':True},'physical_tested':False,'flashed':False,'manufacturing_released':False,'task_state':{'T0':'DIGITAL_INPUT_AND_DELIVERY_LOCK_COMPLETE','T1':'DIGITAL_RECOVERY_PASS; C_DRIVER_INTEGRATION_NOT_RUN','T2':'PARTIAL_CATALOG_AND_CONDITIONAL_DC; CRIMP_INRUSH_THERMAL_OPEN','T3':'CODE_BUILDS_AND_DIGITAL_CHAIN_PASS; REAL_SERIAL_SPI_CAN_NOT_RUN','T4':'PARTIAL_COMMON_ARM_TRIAL; EXACT_SHARED_COLLISIONS_FOUND','T5':'PARTIAL_OUTPUT_GEOMETRY_ONLY; BOARD_ROUTING_DRIVERS_AND_JOINT_QUALIFICATION_OPEN','T6':'NOT_RUN_NO_PHYSICAL_HARDWARE'},'mechanical_findings':findings,'decision':'A remains acquisition baseline; C freeze deferred. Resolve shared shoulder/N2/RF layout before further C board miniaturization. No change to mass/height/axes/wireless requirements.','baseline_preservation':{'design_sources':len(lock['repositories']['design']['sources_sha256']),'old_O4_delivery_files':len(old['files_sha256']),'user_config_preserved':True},'idf_compiled_input_sha256':idf_inputs,'ue_tested_source_sha256':compiled,'tools':{'python':sys.version,'numpy':importlib.metadata.version('numpy'),'pytest':importlib.metadata.version('pytest'),'pyserial':importlib.metadata.version('pyserial'),'KiCad':'10.0.6','CadQuery':'2.7 via configured CQ-editor adapter','ESP_IDF':'6.1','UE_build':read(Path('E:/UnrealEngine/UE_5.8/Engine/Build/Build.version'))},'known_failed_attempts':['Initial direct Python CAD launch lacked CadQuery; configured adapter succeeded','Initial CAD transformShape rejected a rigid transform; replaced by validated rigid Location and rerun'],'unrun':['No real AS5048/ESP32/RS485','No STM32 driver execution','No new PCB routing/DRC acceptance','No actual crimp/current/thermal/bend/torque/lifetime/physical calibration','No complete loaded nine-axis arm or whole-body qualification']}
 save(RUN/'results_revO5.json',result)
 # UE snapshot and patch exclude the user's existing DefaultEditor.ini changes.
 user_paths=set(lock['repositories']['ue']['user_uncommitted_sha256'])
 ue_paths=set(lock['repositories']['ue']['sources_sha256'])-user_paths
 ue_paths.update(p for p in git(ue,'ls-files','--others','--exclude-standard').decode().splitlines() if p.startswith(('Plugins/PoseDoll/Source/','Scripts/','Tools/PoseDollSimulator/','Docs/')))
 ue_paths.update(['Docs/PDS1_PROTOCOL.md','Docs/O5_RECOVERY.zh-CN.md'])
 ue_paths={p for p in ue_paths if (ue/p).is_file()}
 ue_hashes={p:sha(ue/p) for p in sorted(ue_paths)}
 changes=[p for p in git(ue,'diff','--name-only','HEAD').decode().splitlines() if p not in user_paths]
 patch=git(ue,'diff','--binary','HEAD','--',*changes).decode('utf-8') if changes else ''
 for p in sorted(set(git(ue,'ls-files','--others','--exclude-standard').decode().splitlines())&ue_paths):
  content=(ue/p).read_text(encoding='utf-8').splitlines(keepends=True)
  patch+='diff --git a/'+p+' b/'+p+'\nnew file mode 100644\n'+''.join(difflib.unified_diff([],content,fromfile='/dev/null',tofile='b/'+p))
 (OUT/'UE_O5_changes.patch').write_text(patch,encoding='utf-8')
 archives={}
 z=OUT/'UE_O5_source.zip';archives[z.relative_to(ROOT).as_posix()]=archive(z,[ue/p for p in ue_paths],ue)
 native=list((HW/'generated/revO5/runs/o5_20260924_r1').rglob('*'));native=[p for p in native if p.is_file()]
 native.extend(ROOT/p for p in arm['input_sha256']);z=OUT/'hardware_native_and_inputs_o5.zip';archives[z.relative_to(ROOT).as_posix()]=archive(z,native,ROOT)
 # Logs are normally ignored by Git; preserve their raw bytes in a delivered zip.
 z=OUT/'raw_logs_o5.zip';archives[z.relative_to(ROOT).as_posix()]=archive(z,[p for p in RUN.rglob('*') if p.is_file()],ROOT)
 design_sources=dict(lock['repositories']['design']['sources_sha256'])
 files=git(ROOT,'ls-files','-co','--exclude-standard').decode().splitlines()
 for p in files:
  if ('revO5' in p or '/revO5_review_source/' in p or '/O5_' in p or p.endswith('REVIEW_REQUEST_REVO5.zh-CN.md') or p.startswith('Tools/PoseDollHardwareBridge/') or p in ['scripts/seal_revo5.py','scripts/analyze_revo5_power.py','scripts/Run-RevO5-LinkTests.cmd','scripts/Run-RevO5-GatewayTests.cmd']) and not p.startswith(('Hardware/PoseDoll44/generated/','Hardware/PoseDoll44/verification/')):
   if (ROOT/p).is_file():design_sources[p]=sha(ROOT/p)
 source_lock={'schema':'o5-final-source-lock-v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_refs':{k:v['head'] for k,v in lock['repositories'].items()},'commit_state':'Working tree delivery; no commit or push performed','design':dict(sorted(design_sources.items())),'ue':ue_hashes,'user_uncommitted_preserved':lock['repositories']['ue']['user_uncommitted_sha256'],'native_inputs':arm['input_sha256'],'ue_patch_baseline':lock['repositories']['ue']['head'],'patch_normalization':'UE git patch follows LF normalization; source zip retains exact tested working-file bytes'}
 save(OUT/'FINAL_SOURCE_LOCK.json',source_lock)
 # Direct tracked/intended files plus archives: old baseline files are included for drift detection.
 direct=dict(design_sources)
 for base in [OUT,RUN,HW/'generated/revO5/runs/o5_20260924_r1']:
  for p in base.rglob('*'):
   if p.is_file() and p.suffix.lower() in ('.json','.txt','.md','.zip','.patch'):direct[p.relative_to(ROOT).as_posix()]=sha(p)
 direct['Hardware/PoseDoll44/docs/REVIEW_REQUEST_REVO5.zh-CN.md']=sha(HW/'docs/REVIEW_REQUEST_REVO5.zh-CN.md')
 save(OUT/'DELIVERY_MANIFEST.json',{'schema':'o5-sealed-digital-delivery-v1','run_id':'o5_20260924_r1','files_sha256':dict(sorted(direct.items())),'archives':archives,'manufacturing_released':False})
 return verify()
if __name__=='__main__':raise SystemExit(main())
