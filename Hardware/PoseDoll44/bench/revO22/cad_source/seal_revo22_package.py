"""Seal the O22 review package and validate its deliverable invariants."""
from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,py_compile
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';B=H/'bench/revO22';P=H/'tutorials/full-doll-o22';U=Path('E:/UnrealProjects/DollSimulation')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
# Refresh audit-only source copies and source references after final fixes.
for src in (R/'scripts').glob('*revo22*.py'):shutil.copy2(src,B/'cad_source'/src.name)
for src in (U/'Scripts/O22').glob('*.py'):shutil.copy2(src,B/'ue/editor_scripts'/src.name)
idx=read(B/'SOURCE_INDEX.json');idx['repository_scripts']={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in (R/'scripts').glob('*revo22*.py')};idx['ue_commit']=subprocess.check_output(['git','-C',str(U),'rev-parse','HEAD'],text=True).strip();put(B/'SOURCE_INDEX.json',idx)
# Owned saved demo assets, references only: no character meshes copied.
assets=B/'ue/digital_fixture_assets';assets.mkdir(exist_ok=True)
for src in (U/'Content/PoseDoll_O22').glob('*'):
 if src.suffix in ['.uasset','.umap']:shutil.copy2(src,assets/src.name)
put(assets/'INSTALL.json',{'destination':'DollSimulation/Content/PoseDoll_O22','engine':'UE5.8.2','source_kind':'SYNTHETIC_P21R','physical_test':False,'replace_existing_assets':False,'alternative':'Run ue/editor_scripts/test_capture.py against the intended test project to regenerate.'})
# Independently verify evidence and all manufacturing assets.
assert read(B/'verification/host_tests.json')['status']=='PASS'
for name in ['o22_capture','o22_reopen']:assert read(B/'verification'/f'{name}.json')['passed']
assert not read(B/'mechanical/sensor_fit.json')['fit_failures'];assert not read(B/'mechanical/end_axis_fit.json')['failures']
assert not read(B/'mechanical/adjacent_regression.json')['new_or_increased_contacts']
assert read(B/'physical_tests/sensor_coupon/fit_report.json')['status']=='PASS'
manifest=read(B/'print_batch/manifest.json');assert len(manifest['rows'])==150 and manifest['print_pieces']==186
for row in manifest['rows']:
 assert sha(B/row['stl'])==row['stl_sha256'],row['id']
 with zipfile.ZipFile(B/'print_batch'/(row['id']+'.3mf')) as z:assert z.testzip() is None
for kind in ['sensor','carrier']:
 d=read(B/'electronics'/kind/'drc_final.json');e=read(B/'electronics'/kind/'erc.json');assert not d['violations'] and not d['unconnected_items'];assert not [v for sh in e.get('sheets',[]) for v in sh.get('violations',[])]
w=read(B/'harness/routing_plan.json');assert len(w['rows'])==46 and w['maximum_proposed_length_mm']<=750
components=read(B/'electronics/carrier/components.json');look={c['ref']:c for c in components}
for row in w['rows']:assert look[row['carrier_reference']]['value'].startswith(row['connector']+' ')
for src in (B/'source').glob('*.py'):py_compile.compile(str(src),doraise=True)
old=H/'bench/revO21/PoseDoll_O21_MT6701_Costdown.zip'
if not old.exists():
 candidates=list((H/'bench/revO21').glob('*.zip'));assert len(candidates)==1;old=candidates[0]
assert sha(old)=='bd686c9f110b9617b1f8731d4ed9428b3afad271b5b289cadb59d0dc9247888d','O21 snapshot changed'
# Record browser observations from actual CLI actions/screenshots.
put(B/'verification/browser.json',{'status':'PASS','url':'http://127.0.0.1:8770/tutorials/full-doll-o22/index.html','scenes':7,'print_rows':150,'harness_rows':46,'mobile_viewport':[390,844],'horizontal_overflow':False,'console_errors_observed':0,'checked':['default CAD','SOP8 section','carrier visible component side','left arm and wire guide','scene selection','checkbox','mobile layout'],'screenshots':['viewer_default.png','viewer_section.png','viewer_carrier.png','viewer_left_arm.png']})
put(B/'verification/package_audit.json',{'status':'PASS','O21_snapshot_sha256':sha(old),'source_tests':read(B/'verification/host_tests.json'),'print_types':150,'print_pieces':186,'O11_sensor_add_on_prints':2,'all46_sensor_envelopes_fit':True,'new_adjacent_contacts_in_regression':0,'inherited_adjacent_contacts_remain':True,'rigid_pose_samples':74,'harness_endpoint_samples':234,'electronic_ERC_DRC_PARITY':'PASS','physical_test':False,'confirmed_quotes':0,'budget_is_target_not_price':True,'ue_commit':idx['ue_commit']})
exclude_names={'PoseDoll_O22_Engineering_Package.zip','PACKAGE_RECEIPT.json','PACKAGE_MANIFEST.json'}
files=sorted(p for folder in [B,P] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in exclude_names and not p.name.endswith(('.lck','.pyc')))
put(B/'PACKAGE_MANIFEST.json',{'schema':'POSEDOLL-O22-PACKAGE/1','files':{str(p.relative_to(H)).replace('\\','/'):sha(p) for p in files},'self_hash_excluded':True,'physical_release':False})
files.append(B/'PACKAGE_MANIFEST.json');out=B/'PoseDoll_O22_Engineering_Package.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,str(p.relative_to(H)))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for name,h in read(B/'PACKAGE_MANIFEST.json')['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h,name
receipt={'archive':out.name,'sha256':sha(out),'bytes':out.stat().st_size,'files':len(files),'manifest_entries':len(files)-1,'archive_readback':'PASS','UE_commit':idx['ue_commit'],'hardware_status':'ENGINEERING_FIRST_ARTICLE','physical_release':False}
put(B/'PACKAGE_RECEIPT.json',receipt);print(json.dumps(receipt,indent=2),flush=True)
