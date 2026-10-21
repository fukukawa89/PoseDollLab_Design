"""Seal the digitally checked C7 print and full assembly-animation package."""
from o22f7_animation import *
import zipfile,re,collections,importlib.util,threading,urllib.request,urllib.error
from urllib.parse import urlsplit,unquote
import sys
sys.dont_write_bytecode=True
C=WORK/'structure_revision';N=B/'O22F7_PLA_AssemblyRevision';NG=N/'assembly/tutorials/assembly-o22';A=NG/'animation';V=N/'verification/C7'
p=read(C/'C7_package_verification.json');seq=read(A/'sequence.json');g=read(NG/'guide-data.json');m=read(N/'manifest.json');browser=read(C/'C7_browser_review.json')
assert p['passed'] and browser['passed'] and len(p['checks'])==2255
assert p['sequence_sha256']==sha(A/'sequence.json') and not seq['coverage']['unverified_insertion_steps']
assert all(q['passed'] for q in p['checks']) and not browser['console_errors']
assert read(A/'coverage.json')['release_ready']
for t in ['最终检查显示整个人偶且不显示单件盘位','最终检查阶段标签']:
 if t not in browser['tests']:browser['tests'].append(t)
browser.update(sequence_sha256=sha(A/'sequence.json'),app_sha256=sha(A/'app.js'),release_ready=True,unresolved_steps=[],scope='Browser controls, plate lookup, desktop/mobile circuit diagrams, exact chapter end poses, maintained parked root, final completion labels. Physical assembly and continuous collision-free paths are not certified.')
browser['screenshots_sha256']={s:sha(R/'output/playwright'/s) for s in browser['screenshots']}
put(C/'C7_browser_review.json',browser);put(A/'browser-review.json',browser);put(V/'browser_review.json',browser)
(V/'screenshots').mkdir(exist_ok=True)
for s in browser['screenshots']:shutil.copy2(R/'output/playwright'/s,V/'screenshots'/s)
for name in ['C7_release_metadata_transition.json','C7_package_verification.json']:shutil.copy2(C/name,V/name)
# Inherited electrical facts remain unchanged; native pin validation is retained.
oldg=read(G/'guide-data.json');assert g['routes']==oldg['routes'] and g['pin_order']==oldg['pin_order'];assert sha(NG/'evidence/carrier_native_pads.json')==sha(G/'evidence/carrier_native_pads.json')
electrical={'passed':True,'sensor_routes':46,'pin_checks_inherited':230,'route_and_pin_order_equal_original':True,'carrier_native_pads_sha256':sha(NG/'evidence/carrier_native_pads.json'),'original_verification_sha256':sha(G/'verification.json'),'physical_electrical_tested':False};put(V/'electrical_inheritance.json',electrical)
summary={k:v for k,v in p.items() if k!='checks'};summary.update(status='RELEASED_DIGITAL_CHECKS_PASSED',complete=True,content_checks=len(p['checks']),browser_checks=len(browser['tests']),browser_passed=True,unresolved_steps=[],original_manufacturing_files_preserved=164,original_release_archive_preserved=True,electrical_routes_and_pin_order_unchanged=True,verification_scope='PLA native slicing/support checks, all-instance animation coverage, current plate mapping, listed key mechanical paths and sampled added-interference comparisons. No physical printing, assembly, strength or fatigue test.',previous_release_summary='verification/prior_release/verification/summary.json',hole_support_exception_ids=[r['id'] for r in m['rows'] if r['retained_hole_support_exception']],all_holes_automatically_clear_after_print=False)
assert len(summary['hole_support_exception_ids'])==17
put(N/'verification/summary.json',summary)
current=dict(summary,evidence_relative_to_package_root={'content':'verification/C7/package_verification.json','browser':'verification/C7/browser_review.json','motion':'verification/C7/W005_C7_sequence_interfaces.json','rotation':'verification/C7/C7_chest_rotation_review.json','electrical':'verification/C7/electrical_inheritance.json'})
for path in [NG/'verification.json',A/'verification.json',N/'verification/assembly_guide.json',N/'verification/assembly_animation.json']:put(path,current)
# Explicitly identify unchanged historical evidence retained for traceability.
write(N/'verification/读我.txt','当前发布结论见 summary.json；本次左锁骨拆分、打印与动画验证见 C7/。prior_release/ 保留旧版记录，不应作为本版安装顺序。其他原有验证目录用于追溯未改动零件及 O22F7 转角补强。\n')
m['body_changed_from_F5_type_ids']=sorted((set(m['body_changed_from_F5_type_ids'])-{'W005'})|{'W005A','W005B'});m['restored_original_support_type_ids']=[s for s in m['restored_original_support_type_ids'] if s!='W005'];put(N/'manifest.json',m);write(N/'audit-data.js','window.AUDIT='+json.dumps(m,ensure_ascii=False,separators=(',',':'))+';window.AUDIT_DETAILS={};window.AUDIT_MESHES={};')
release={'version':m['version'],'revision':seq['revision'],'status':'RELEASED_DIGITAL_CHECKS_PASSED','complete':True,'date':'2026-10-16','plates':15,'changed_plates':['D05','D15'],'changed_parts':['W005A','W005B'],'unchanged_plates':13,'assembly_animation':{'complete':True,'entry':'assembly/tutorials/assembly-o22/animation/index.html','chapters':26,'actions':1658,'unresolved_steps':[],'sequence_sha256':sha(A/'sequence.json')},'summary':'verification/summary.json','physical_print_tested':False,'physical_assembly_tested':False,'strength_or_fatigue_tested':False,'all_animation_paths_continuously_collision_certified':False};put(N/'RELEASED.json',release)
# Regenerate the secondary print-file index from the final manifest as well.
links_html=''.join('<li><a href="../../../'+plate['project']+'">'+plate['id']+' · PLA 工程</a></li>' for plate in m['plates'])
write(NG/'external-files.html','<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O22F7 打印文件</title><link rel="stylesheet" href="style.css"><main><h1>O22F7 · 15 盘 PLA · 装配修订版 r4</h1><p><a href="index.html#plates">返回当前盘图与取件清单</a> · <a href="../../../打印与拆撑.html">打印与拆撑</a></p><ul>'+links_html+'</ul></main></html>')
assert (NG/'external-files.html').read_text('utf8').count('.3mf"')==15
# Check every static local HTML asset in the actual deliverable.
bad=[];links=0
for path in N.rglob('*.html'):
 for target in re.findall(r'(?:href|src)=[\"\']([^\"\']+)',path.read_text('utf-8-sig')):
  u=urlsplit(target)
  if u.scheme or '${' in target or not u.path:continue
  links+=1
  if not (path.parent/unquote(u.path)).is_file():bad.append((path.relative_to(N).as_posix(),target))
assert not bad,bad
put(N/'verification/asset_links.json',{'passed':True,'local_links_checked':links,'revision':seq['revision']})
# Exercise the portable launcher's actual server with this final directory.
spec=importlib.util.spec_from_file_location('c7_final_launcher',N/'start_preview.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);server,url=mod.create_preview(N);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=url.rsplit('/',1)[0]+'/'
try:
 with urllib.request.urlopen(base+'assembly/tutorials/assembly-o22/animation/sequence.json') as response:assert hashlib.sha256(response.read()).hexdigest()==sha(A/'sequence.json');assert response.headers['X-PoseDoll-Version']=='O22F7'
 with urllib.request.urlopen(base+'manifest.json') as response:assert json.loads(response.read())['complete'] is True
 try:urllib.request.urlopen(base.replace(base.split('/')[-2],'wrong-package')+'index.html');raise AssertionError('Wrong prefix was accepted')
 except urllib.error.HTTPError as e:assert e.code==404
finally:server.shutdown();server.server_close();thread.join()
put(V/'portable_launcher_review.json',{'passed':True,'current_sequence_loaded':True,'current_released_manifest_loaded':True,'wrong_package_path_rejected':True,'launcher_sha256':sha(N/'start_preview.py')})
# Keep the relevant authoring/checking source as engineering evidence.
(V/'sources').mkdir(exist_ok=True)
for name in ['build_o22f7_clavicle_c7.py','build_o22f7_c7_animation.py','verify_o22f7_clavicle_c7_surfaces.py','check_o22f7_clavicle_c7_function.py','check_o22f7_clavicle_c7_exact_gap.py','check_o22f7_clavicle_c7_preassembly.py','check_o22f7_c7_stock.py','check_o22f7_c7_sequence_paths.py','check_o22f7_c7_chest_rotation.py','verify_o22f7_c7_supports.py','verify_o22f7_c7_package.py','check_o22f7_c7_browser.js','finalize_o22f7_c7_metadata.py','seal_o22f7_c7_final.py']:shutil.copy2(R/'scripts'/name,V/'sources'/name)
put(N/'assembly/archive_manifest.json',{'schema':'POSEDOLL-O22F7-ASSEMBLY-ARCHIVE/4','revision':seq['revision'],'status':seq['status'],'unresolved_steps':[],'files':{path.relative_to(N/'assembly').as_posix():sha(path) for path in sorted((N/'assembly').rglob('*')) if path.is_file() and path.name!='archive_manifest.json' and '__pycache__' not in path.parts}})
files=sorted(path for path in N.rglob('*') if path.is_file() and path.name!='SHA256SUMS.txt' and '__pycache__' not in path.parts);checks={path.relative_to(N).as_posix():sha(path) for path in files};write(N/'SHA256SUMS.txt',''.join(digest+'  '+rel+'\n' for rel,digest in checks.items()))
target=B/'O22F7_PLA_完整打印与拼装动画包_20261016_r4.zip';assert target.resolve().parent==B.resolve() and not target.exists();partial=target.with_suffix('.building.zip');assert not partial.exists()
print('SEAL',len(files)+1,'files',links,'links checked; writing archive',flush=True)
with zipfile.ZipFile(partial,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for path in files+[N/'SHA256SUMS.txt']:z.write(path,path.relative_to(N).as_posix())
print('ZIP_WRITTEN',partial.stat().st_size,'verifying CRC and every file hash',flush=True)
with zipfile.ZipFile(partial) as z:
 assert z.testzip() is None;assert set(z.namelist())==set(checks)|{'SHA256SUMS.txt'}
 for rel,digest in checks.items():assert hashlib.sha256(z.read(rel)).hexdigest()==digest,rel
 assert z.read('SHA256SUMS.txt')==(N/'SHA256SUMS.txt').read_bytes()
original=read(WORK/'before.json');assert sha(B/'O22F7_PLA_完整打印包_20261016.zip')==original['archive_sha256']
partial.rename(target);digest=sha(target);write(target.with_suffix('.zip.sha256'),digest+'  '+target.name+'\n')
delivery={'status':'RELEASED_DIGITAL_CHECKS_PASSED','archive':str(target),'directory':str(N),'sha256':digest,'bytes':target.stat().st_size,'files':len(files)+1,'every_archived_file_verified':True,'original_release_archive_unchanged':True,'content_checks':len(p['checks']),'browser_checks':len(browser['tests']),'local_html_links_checked':links,'plates':15,'installed_print_instances':186,'hardware_instances':960,'assembly_chapters':26,'assembly_actions':1658,'sensor_routes':46,'physical_print_tested':False,'physical_assembly_tested':False,'strength_or_fatigue_tested':False,'complete_swept_volume_certification':False,'preview_url':'http://127.0.0.1:14381/O22F7-3bb29f82690948a8a4be92768ea705ee/assembly/tutorials/assembly-o22/animation/index.html'};put(C/'final_delivery.json',delivery);print(json.dumps(delivery,ensure_ascii=False),flush=True)
