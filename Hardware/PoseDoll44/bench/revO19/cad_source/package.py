"""Seal O19 without mutating the frozen O18 baseline."""
from base import *
import shutil,zipfile,hashlib
REPO=H.parents[1];PAGE=H/'tutorials/full-doll-o19';HERE=Path(__file__).resolve().parent

def main():
 geom=g.read(OUT/'geometry_verification.json');paths=g.read(OUT/'path_verification.json');exp=g.read(OUT/'export_verification.json');browser=g.read(OUT/'browser_review.json')
 assert geom['status']=='REGRESSION_PASS_WITH_INHERITED_OVERLAPS' and not geom['new_collisions']
 assert paths['status']=='PASS' and exp['status']=='PASS' and browser['status']=='PASS'
 unchanged={}
 for folder in ('electronics','firmware_source','firmware_binaries'):
  for p in (H/'bench/revO18'/folder).rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   rel=p.relative_to(H/'bench/revO18');assert g.sha(p)==g.sha(BENCH/rel);unchanged[str(rel).replace('\\','/')]=g.sha(p)
 for name in ('device.py','usb_capture.py','codec_fixture.bin'):
  p=H/'bench/revO18/source'/name;assert g.sha(p)==g.sha(BENCH/'source'/name);unchanged['source/'+name]=g.sha(p)
 g.write(OUT/'inherited_runtime_electronics.json',{'status':'BYTE_IDENTICAL_TO_O18','files':unchanged,'new_firmware_build_required':False,'hardware_flashed':False})
 # The connectors and wire-chain endpoints are unchanged; rod binding moves.
 harness=g.read(BENCH/'harness/cut_and_binding_plan.json');harness['o19_note']='Electrical chain and connector endpoints are unchanged. Four beam midspans have moved: bind wires to the new actual rods and verify flex/slack on the assembled doll. Frozen wire cut estimates do not certify the new binding path.';g.write(BENCH/'harness/cut_and_binding_plan.json',harness)
 shutil.copy2(H/'docs/DESIGN_REVO19.zh-CN.md',BENCH/'DESIGN.zh-CN.md')
 for p in HERE.glob('*.py'):
  dst=BENCH/'cad_source'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst)
 shutil.copy2(HERE/'verify_package.py',BENCH/'source/verify_package.py')
 selected=['changes.json','bom_comparison.json','geometry_verification.json','path_verification.json','export_verification.json','viewer_geometry.json','runtime_verification.json','browser_review.json','inherited_runtime_electronics.json','o11_user_validation.json','hip_orientation_search.json','hip_mount_candidates.json','hip_mount_refined.json','hip_mount_final_search.json','hip_mount_compromise.json','hip_branch_search.json','rejected_straight_span_collisions.json']
 for name in selected:
  src=OUT/name
  if not src.exists():continue
  dst=BENCH/'verification'/name;dst.parent.mkdir(exist_ok=True);shutil.copy2(src,dst)
 for p in (REPO/'output/playwright/o19').glob('*.png'):shutil.copy2(p,BENCH/'verification'/p.name)
 for p in PAGE.iterdir():
  if not p.is_file():continue
  dst=BENCH/'viewer'/p.name;dst.parent.mkdir(exist_ok=True)
  if p.suffix in ('.html','.js'):
   s=p.read_text(encoding='utf-8-sig').replace('../../bench/revO19/','../').replace('../../docs/DESIGN_REVO19.zh-CN.md','../DESIGN.zh-CN.md')
   s=s.replace('../PoseDoll_O19_Universal_Design.zip','../README.zh-CN.md').replace('下载 O19 单人偶设计包','阅读本地设计包说明').replace('../full-doll-o18/index.html','../DESIGN.zh-CN.md').replace('已保存的 O18 ↗','O18保存记录 ↗');dst.write_text(s,encoding='utf-8')
  else:shutil.copy2(p,dst)
 status={'revision':'O19','status':'LEG_ALIGNMENT_CANDIDATE_WITH_INHERITED_COLLISIONS','saved_O18_commit':'08e8f8b','saved_O18_tag':'posedoll-o18-prototype-20260930','print_pieces':188,'print_types':117,'raw_channels':46,'semantic_dof':41,'height_mm':geom['neutral_exact_geometry']['height_mm'],'new_leg_carriers':4,'extra_friction_parts':0,'o11_coupon_user_validation':'PASS_REPORTED_2026-09-30','hip_offset_each_side_mm':16,'collision_regression_cases':24,'additional_interpolation_samples':43,'new_part_collision_regression_passed':True,'continuous_collision_proof':False,'o19_physical_tested':False,'ue_end_to_end_tested':False,'manufacturing_release':False}
 g.write(BENCH/'DESIGN_STATUS.json',status)
 (BENCH/'README.zh-CN.md').write_text('# O19 腿杆对齐优化\n\nO18已保存：08e8f8b / posedoll-o18-prototype-20260930。O19仍为一台188件、117种打印件，替换L001至L004四件腿杆；原端部与46路测量不变。\n\nO11小样的配合和可调摩擦已获用户实测通过，不增加摩擦冗余。髋中心各外移16mm与既有整机干涉仍保留，详见DESIGN.zh-CN.md和DESIGN_STATUS.json。\n\n运行python serve_preview.py，打开http://127.0.0.1:8771/viewer/index.html。完整性检查：python source/verify_package.py。采集/USB测试：python source/test_device.py、python source/test_usb.py。\n\n四件新STL与3MF见print_batch/L001至L004；旧件按同目录单台清单使用。verification含数字几何检查、用户O11报告及未采用的髋零偏移试算。四轴分解插值不等同于连续机构轨迹证明。\n\nCAD复建依赖仓库内冻结旧版输入；cad_source中experiment/search脚本是探索记录，不是正式打印件生成器。正式构建入口为design.py、export.py。USB固件与电子件未改动；原标定仍需与实物传感器对应。\n',encoding='utf-8')
 g.write(BENCH/'source_lock.json',{'O18_commit':'08e8f8b','O18_archive_sha256':g.sha(H/'bench/revO18/PoseDoll_O18_Universal_Design.zip'),'source_sha256':{str(p.relative_to(REPO)).replace('\\','/'):g.sha(p) for p in [*HERE.glob('*.py'),H/'docs/DESIGN_REVO19.zh-CN.md',OUT/'changed_parts.npz',OUT/'changes.json']}})
 files={str(p.relative_to(BENCH)).replace('\\','/'):g.sha(p) for p in BENCH.rglob('*') if p.is_file() and p.name not in ('FILES_SHA256.json','PoseDoll_O19_Universal_Design.zip','local_test_result.json') and '__pycache__' not in p.parts}
 g.write(BENCH/'FILES_SHA256.json',{'schema':'POSEDOLL-O19-FILES/1','files':files})
 archive=BENCH/'PoseDoll_O19_Universal_Design.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name in sorted([*files,'FILES_SHA256.json']):z.write(BENCH/name,name)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,dig in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==dig,name
 g.write(OUT/'package_verification.json',{'status':'PASS','files_checked':len(files),'zip_sha256':g.sha(archive),'zip_bytes':archive.stat().st_size,'physical_qualification':False})
 print('O19 sealed',len(files),'files',g.sha(archive),flush=True)
if __name__=='__main__':main()
