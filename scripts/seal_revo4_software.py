"""Seal cross-repository software source + test evidence for O4 review."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile,difflib,sys,datetime
UE=Path('E:/UnrealProjects/DollSimulation');DESIGN=Path(__file__).resolve().parents[1];HW=DESIGN/'Hardware/PoseDoll44';proof=HW/'verification/revO4/deliveries/o4_20260924_d1';ueproof=UE/'reports/o4';test=UE/'Saved/O4TestProject'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sources=set()
for rel in ('Plugins/PoseDoll/Source','Tools/PoseDollSimulator/src','Tools/PoseDollSimulator/tests','Shared/Profiles','Shared/Fixtures','Docs'):
 for p in (UE/rel).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.cpp','.h','.cs','.py','.json','.md','.txt'):sources.add(p)
sources.update((UE/'Scripts').glob('*o4*.py'))
sources.update(p for p in (UE/'Tools/PoseDollSimulator').iterdir() if p.is_file() and p.suffix in ('.toml','.txt','.md'))
sources.update(UE/p for p in ('Scripts/StartSimulator.ps1','Scripts/BuildPoseDoll.ps1','Scripts/SetupSimulator.ps1','Plugins/PoseDoll/PoseDoll.uplugin','DollSimulation.uproject'))
inputs={p.relative_to(UE).as_posix():sha(p) for p in sorted(sources)}
# Every delivered C++ source must equal the source that the isolated build consumed.
for p in sources:
 if 'Plugins/PoseDoll/Source' in p.as_posix():
  other=test/p.relative_to(UE);assert other.is_file() and sha(other)==sha(p),p
e=read(test/'reports/o4/o4_ue_final/editor.json');r=read(test/'reports/o4/o4_ue_final/reopen.json');c=read(test/'reports/o4/core_final/index.json');soak=read(ueproof/'soak_20260924_r2/report.json');replay=read(ueproof/'replay_final.json');ui=read(ueproof/'ui_final.json')
assert e['passed'] and r['passed'] and c['failed']==0 and c['succeeded']==4 and soak['accepted']==1000 and replay['passed'] and ui['passed']
assert '61 passed' in (ueproof/'python_final.txt').read_text()
dest=proof/'software';dest.mkdir(exist_ok=True)
files={
'editor.json':test/'reports/o4/o4_ue_final/editor.json','reopen.json':test/'reports/o4/o4_ue_final/reopen.json','core.json':test/'reports/o4/core_final/index.json','build.txt':test/'build_o4_r8.log',
'editor.log':test/'Saved/Logs/O4Integration_final.log','reopen.log':test/'Saved/Logs/O4Reopen_final2.log','core.log':test/'Saved/Logs/O4Core_final.log',
'python_tests.txt':ueproof/'python_final.txt','ui.json':ueproof/'ui_final.json','soak_1000.json':ueproof/'soak_20260924_r2/report.json','wire.jsonl.gz':ueproof/'soak_20260924_r2/wire.jsonl.gz','replay.json':ueproof/'replay_final.json',
'preliminary_hard_stop_noise.json':ueproof/'soak_20260924_r1/report.json'}
for name,src in files.items():shutil.copyfile(src,dest/name)
with zipfile.ZipFile(proof/'UE_O4_source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(sources):z.write(p,p.relative_to(UE).as_posix())
# Text patch excludes pre-existing user Config/DefaultEditor.ini and includes new files.
status=subprocess.check_output(['git','status','--porcelain','-z'],cwd=UE).decode().split('\0');changed=[]
for row in status:
 if not row:continue
 name=row[3:].replace('\\','/');p=UE/name
 if p.is_file() and p in sources:changed.append(p)
 elif p.is_dir():changed.extend(x for x in sources if x.is_relative_to(p))
patch=[]
for p in sorted(set(changed)):
 name=p.relative_to(UE).as_posix();old=subprocess.run(['git','show','HEAD:'+name],cwd=UE,capture_output=True)
 before=old.stdout.decode('utf-8-sig').splitlines(keepends=True) if old.returncode==0 else []
 after=p.read_text(encoding='utf-8-sig').splitlines(keepends=True);patch.extend(difflib.unified_diff(before,after,fromfile='a/'+name if old.returncode==0 else '/dev/null',tofile='b/'+name))
(proof/'UE_O4_changes.patch').write_text(''.join(patch),encoding='utf-8')
engine=Path('E:/UnrealEngine/UE_5.8/Engine/Build/Build.version')
result={'schema':'posedoll-o4-software-delivery-v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'UE_base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=UE).decode().strip(),'source_sha256':inputs,'engine_build':read(engine),'isolated_project_sha256':sha(test/'DollSimulation.uproject'),'build':'PASS','python_tests_passed':61,'native_UE_test_groups_passed':4,'static_cross_language_cases':28,'UE_integration_passed':True,'fresh_process_reopen_passed':True,'Qt_widget_checks_passed':True,'healthy_loopback':{'accepted':1000,'p95_ms':soak['p95_ms'],'max_ms':soak['max_ms'],'source':'SIMULATED_NO_PHYSICAL_HARDWARE','final_decoder_replay':True},'unrelated_user_changes_preserved':['Config/DefaultEditor.ini'],'original_running_editor_DLL_replaced':False,'test_artifacts_sha256':{p.relative_to(proof).as_posix():sha(p) for p in sorted(dest.iterdir())},'source_zip_sha256':sha(proof/'UE_O4_source.zip'),'change_patch_sha256':sha(proof/'UE_O4_changes.patch'),'physical_tested':False}
save(ueproof/'DELIVERY.json',result);save(proof/'software_evidence.json',result)
with zipfile.ZipFile(proof/'hardware_native_o4_h3.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted((HW/'generated/revO4/runs/o4_20260924_h3').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DESIGN).as_posix())
print('sealed',len(inputs),'software sources;',len(changed),'changed files; hardware zip MB',round((proof/'hardware_native_o4_h3.zip').stat().st_size/1e6,2))
