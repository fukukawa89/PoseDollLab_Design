"""Seal O18 with validated geometry and the byte-identical O17 electronics."""
from base import *
import shutil,zipfile,hashlib,subprocess
REPO=H.parents[1];PAGE=H/'tutorials/full-doll-o18';OLD=H/'bench/revO17';HERE=Path(__file__).resolve().parent

def main():
 geom=g.read(OUT/'geometry_verification.json');exp=g.read(OUT/'export_verification.json')
 assert geom['status']=='REGRESSION_PASS_WITH_INHERITED_OVERLAPS' and not geom['new_collisions'] and len(geom['poses'])==24
 assert exp['status']=='PASS'
 browser=g.read(OUT/'browser_review.json');assert browser['status']=='PASS'
 # Run the unchanged reference tests against the new profile in the package.
 tests=[]
 for name,count in [('test_device.py',15),('test_usb.py',6)]:
  run=subprocess.run([sys.executable,str(BENCH/'source'/name)],cwd=REPO,capture_output=True,text=True,encoding='utf-8',errors='replace')
  log=run.stdout+run.stderr;(OUT/(name+'.log')).write_text(log,encoding='utf-8')
  assert run.returncode==0,log;tests.append({'file':name,'tests':count,'exit_code':0})
 g.write(OUT/'runtime_verification.json',{'status':'PASS','tests':tests,'total_tests':21,'runtime_source_revision':'O17 byte-identical','tested_device_profile':'o18_usb_universal_v1','wire_protocol':'P17R/1','real_hardware_connected':False,'ue_end_to_end_tested':False})
 unchanged={}
 for folder in ('electronics','firmware_source','firmware_binaries'):
  shutil.copytree(OLD/folder,BENCH/folder,dirs_exist_ok=True)
  for p in (OLD/folder).rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   rel=p.relative_to(OLD);assert g.sha(p)==g.sha(BENCH/rel);unchanged[str(rel).replace('\\','/')]=g.sha(p)
 for name in ('device.py','usb_capture.py','codec_fixture.bin'):
  assert g.sha(OLD/'source'/name)==g.sha(BENCH/'source'/name)
  unchanged['source/'+name]=g.sha(BENCH/'source'/name)
 for name in ('POWER_AND_USB.zh-CN.md','requirements-reference.txt','serve_preview.py'):
  shutil.copy2(OLD/name,BENCH/name)
 g.write(OUT/'inherited_runtime_electronics.json',{'status':'BYTE_IDENTICAL_TO_O17','files':unchanged,'original_firmware_build_report':g.read(H/'generated/revO17/firmware_verification.json'),'new_firmware_build_required':False,'hardware_flashed':False})
 shutil.copy2(H/'docs/DESIGN_REVO18.zh-CN.md',BENCH/'DESIGN.zh-CN.md')
 for p in HERE.glob('*.py'):
  dst=BENCH/'cad_source'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst)
 shutil.copy2(HERE/'verify_package.py',BENCH/'source/verify_package.py')
 selected=['changes.json','bom_comparison.json','feasibility.json','geometry_verification.json','export_verification.json','viewer_geometry.json','runtime_verification.json','browser_review.json','inherited_runtime_electronics.json']
 for name in selected:
  dst=BENCH/'verification'/name;dst.parent.mkdir(exist_ok=True);shutil.copy2(OUT/name,dst)
 for p in (REPO/'output/playwright/o18').glob('*.png'):shutil.copy2(p,BENCH/'verification'/p.name)
 for p in PAGE.iterdir():
  if not p.is_file():continue
  dst=BENCH/'viewer'/p.name;dst.parent.mkdir(exist_ok=True)
  if p.suffix in ('.html','.js'):
   s=p.read_text(encoding='utf-8-sig').replace('../../bench/revO18/','../').replace('../../docs/DESIGN_REVO18.zh-CN.md','../DESIGN.zh-CN.md')
   s=s.replace('../PoseDoll_O18_Universal_Design.zip','../README.zh-CN.md').replace('下载 O18 单人偶设计包','阅读本地设计包说明');dst.write_text(s,encoding='utf-8')
  else:shutil.copy2(p,dst)
 g.write(BENCH/'FIRST_PRINT.json',{'status':'COUPON_BEFORE_FULL_DOLL','full_doll_print_release':False,'optional_coupon_pieces_excluded_from_188':2,
  'parts':[{'id':'Q001','quantity':1,'path':'coupon/Q001.stl','role':'one-piece hinge housing'}, {'id':'Q002','quantity':1,'path':'coupon/Q002.stl','role':'matching hinge rotor'},
  {'id':'N001','quantity':1,'path':'print_batch/N001.stl','role':'O17 sensor cassette'}, {'id':'N004','quantity':1,'path':'print_batch/N004.stl','role':'O17 hinge magnet cartridge'}],
  'stock':[{'sku':k,'quantity':q} for k,q in [('SHOULDER_D4_L8_M3_L6',1),('W_M4_D12_T1',2),('W_M4_D9_T0P8',1),('A8_SS',2),('NUT_M3',2),('W_M3_D9_T0P8',1),('SCREW_M3_L8',1),('NUT_M2',2),('SCREW_M2_L5',2),('MAGNET_D6_T2P5_DIAMETRIC',1),('AS5048A_MINI_PCBA',1)]],
  'consumable':'O17 qualified nonconductive magnet adhesive; clean magnet bottom seat',
  'checks':['nut and washer side insertion','retained washer reaction plane','shoulder screw adjustment and preload retention','roof crushing and print layer strength','creep and repeated motion','sensor/magnet service access and angle repeatability'],
  'not_a_complete_46_channel_capture_system':True})
 status={'revision':'O18','status':'SIMPLIFICATION_PROTOTYPE_KNOWN_INHERITED_COLLISIONS','saved_O17_commit':'5a5ac22','saved_O17_tag':'posedoll-o17-prototype-20260930',
  'print_pieces':188,'print_types':117,'raw_channels':46,'semantic_dof':41,'height_mm':geom['neutral_exact_geometry']['height_mm'],
  'merged_housings':14,'removed_stock_fasteners':56,'collision_regression_cases':24,'new_part_collision_regression_passed':True,
  'inherited_overlap_cases':geom['inherited_overlap_cases'],'continuous_collision_proof':False,'physical_tested':False,'ue_end_to_end_tested':False,'manufacturing_release':False}
 g.write(BENCH/'DESIGN_STATUS.json',status)
 (BENCH/'README.zh-CN.md').write_text('# O18 一体单轴外壳简化版\n\nO17已保存：5a5ac22 / posedoll-o17-prototype-20260930。O18单台188件、117种打印件，额外小样Q001/Q002不计入整机数量。保留46路测量，去掉14件半壳和56件壳体紧固件。\n\n先读DESIGN.zh-CN.md、POWER_AND_USB.zh-CN.md和FIRST_PRINT.json。整机仍有已知干涉，不可把本轮增量回归通过当作整机放行。先验证关节小样。\n\nsource中的测量/USB引擎与固件沿用O17版本，P17R/1未变；profiles是O18配置，必须实测标定。\n\n运行python serve_preview.py后打开http://127.0.0.1:8771/viewer/index.html。离线测试：python source/test_device.py、python source/test_usb.py。完整校验：python source/verify_package.py。这些测试不会连接或刷写实物。\n\nCAD复建依赖设计仓库冻结的O15/O17输入，cad_source不是独立依赖全集。验证报告与网页截图见verification。\n',encoding='utf-8')
 g.write(BENCH/'source_lock.json',{'O17_commit':'5a5ac22','O17_archive_sha256':g.sha(OLD/'PoseDoll_O17_Universal_Design.zip'),
  'source_sha256':{str(p.relative_to(REPO)).replace('\\','/'):g.sha(p) for p in [*HERE.glob('*.py'),H/'docs/DESIGN_REVO18.zh-CN.md']}})
 files={str(p.relative_to(BENCH)).replace('\\','/'):g.sha(p) for p in BENCH.rglob('*') if p.is_file() and p.name not in ('FILES_SHA256.json','PoseDoll_O18_Universal_Design.zip','local_test_result.json') and '__pycache__' not in p.parts}
 g.write(BENCH/'FILES_SHA256.json',{'schema':'POSEDOLL-O18-FILES/1','files':files})
 archive=BENCH/'PoseDoll_O18_Universal_Design.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name in sorted([*files,'FILES_SHA256.json']):z.write(BENCH/name,name)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,dig in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==dig,name
 g.write(OUT/'package_verification.json',{'status':'PASS','files_checked':len(files),'zip_sha256':g.sha(archive),'zip_bytes':archive.stat().st_size,'physical_qualification':False})
 print('O18 sealed',len(files),'files',g.sha(archive),flush=True)

if __name__=='__main__':main()
