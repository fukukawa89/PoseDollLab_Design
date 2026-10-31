"""Seal a separate O20 package after mechanical and browser review."""
from base import *
import shutil,zipfile,hashlib
REPO=H.parents[1];PAGE=H/'tutorials/full-doll-o20';HERE=Path(__file__).resolve().parent

def main():
 geom=g.read(OUT/'geometry_verification.json');paths=g.read(OUT/'path_verification.json');exp=g.read(OUT/'export_verification.json');browser=g.read(OUT/'browser_review.json');mass=g.read(OUT/'mass_comparison.json');bom=g.read(OUT/'bom_comparison.json')
 assert geom['status']=='REGRESSION_PASS_WITH_INHERITED_OVERLAPS' and not geom['new_collisions']
 assert not any(f['classification']=='ADJACENT' for p in geom['poses'] for f in p['findings'])
 assert paths['status']=='PASS' and paths['within_capture_domain_adjacent_overlap_samples']==0 and exp['status']=='PASS' and browser['status']=='PASS'
 unchanged={}
 for folder in ('electronics','firmware_source','firmware_binaries'):
  for p in (H/'bench/revO19'/folder).rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   rel=p.relative_to(H/'bench/revO19');assert g.sha(p)==g.sha(BENCH/rel);unchanged[str(rel).replace('\\','/')]=g.sha(p)
 for name in ('device.py','usb_capture.py','codec_fixture.bin'):
  p=H/'bench/revO19/source'/name;assert g.sha(p)==g.sha(BENCH/'source'/name);unchanged['source/'+name]=g.sha(p)
 g.write(OUT/'inherited_runtime_electronics.json',{'status':'BYTE_IDENTICAL_TO_O19','files':unchanged,'new_firmware_build_required':False,'hardware_flashed':False})
 harness=g.read(BENCH/'harness/cut_and_binding_plan.json');harness['o20_note']='Same electrical endpoints and outer beam paths as O19. Bind wires to retained beam outer surface. Enclosed lightening cores are not wire conduits. Wire flexibility/slack requires assembled review.';g.write(BENCH/'harness/cut_and_binding_plan.json',harness)
 shutil.copy2(H/'docs/DESIGN_REVO20.zh-CN.md',BENCH/'DESIGN.zh-CN.md')
 for p in HERE.glob('*.py'):
  dst=BENCH/'cad_source'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst)
 shutil.copy2(HERE/'verify_package.py',BENCH/'source/verify_package.py')
 names=['changes.json','bom_comparison.json','mass_comparison.json','geometry_verification.json','path_verification.json','export_verification.json','viewer_geometry.json','runtime_verification.json','browser_review.json','inherited_runtime_electronics.json','user_decisions.json','toe_mesh_precision_experiment.json']
 for name in names:
  src=OUT/name;dst=BENCH/'verification'/name;dst.parent.mkdir(exist_ok=True);shutil.copy2(src,dst)
 for p in (REPO/'output/playwright/o20').glob('*.png'):shutil.copy2(p,BENCH/'verification'/p.name)
 for p in PAGE.iterdir():
  if not p.is_file():continue
  dst=BENCH/'viewer'/p.name;dst.parent.mkdir(exist_ok=True)
  if p.suffix in ('.html','.js'):
   s=p.read_text(encoding='utf-8-sig').replace('../../bench/revO20/','../').replace('../../docs/DESIGN_REVO20.zh-CN.md','../DESIGN.zh-CN.md')
   s=s.replace('../PoseDoll_O20_Universal_Design.zip','../README.zh-CN.md').replace('下载 O20 单人偶设计包','阅读本地设计包说明').replace('../full-doll-o19/index.html','../DESIGN.zh-CN.md').replace('已保存的 O19 ↗','O19保存记录 ↗');dst.write_text(s,encoding='utf-8')
  else:shutil.copy2(p,dst)
 status={'revision':'O20','status':'LIGHTWEIGHT_DIGITAL_DESIGN','saved_O19_commit':'98c084a','saved_O19_tag':'posedoll-o19-leg-alignment-20260930','print_pieces':186,'print_types':115,'on_doll_print_pieces':185,'assembly_fixture_pieces':1,'raw_channels':46,'semantic_dof':41,'height_mm':geom['neutral_exact_geometry']['height_mm'],'changed_prints':17,'printed_pieces_removed':2,'stock_fasteners_removed':8,'extra_friction_parts':0,'o11_coupon_user_validation':'PASS_REPORTED_2026-09-30','hip_offset_each_side_mm':16,'hip_layout_user_accepted':True,'nonadjacent_contacts_user_accepted_as_pose_avoidance':True,'collision_regression_cases':24,'additional_raw_axis_samples':156,'within_capture_domain_axis_samples':88,'within_capture_domain_axis_sample_collisions':0,'out_of_capture_raw_extreme_states_with_inherited_contacts':48,'new_part_adjacent_collision_regression_passed':True,'continuous_collision_proof':False,'O20_physical_load_tested':False,'ue_end_to_end_tested':False,'manufacturing_release':False,'mass_reduction_solid_equivalent_g':mass['reduction']['PETG_modeled_total_equivalent_g'],'mass_is_weighed':False}
 g.write(BENCH/'DESIGN_STATUS.json',status)
 (BENCH/'README.zh-CN.md').write_text('# O20 单台USB人偶：少10件，打印体积少2.8%\n\nO19已保存：98c084a / posedoll-o19-leg-alignment-20260930。O20独立提供115种、186件单台打印清单，其中185件装在人偶上，1件为焊接治具。\n\n合并两侧脚趾固定外壳，少2件打印件、4颗M3×20螺钉、4个M3螺母。14件骨架中23段芯孔及控制盒开孔使CAD打印实体少约16.845 cm³。按历史PETG实心口径合计约减29.35 g，非称重；实际值应对比相同切片设置。\n\n双髋各外移16 mm按用户决定保留。远端部件相碰按姿势避让处理，相邻机构仍检查。O11配合与可调摩擦已由用户报告通过，不增加摩擦冗余。\n\nW001–W017为新打印件，其余沿用；W016/W017用原肩轴和垫片。空心杆切片查看最大5 mm内腔桥接，避免无法取出的内部支撑。制造网格已回读验证；新杆加载刚度与UE端到端尚未实测。\n\n运行python serve_preview.py，打开http://127.0.0.1:8771/viewer/index.html。完整性检查：python source/verify_package.py。已有采集/USB测试：python source/test_device.py、python source/test_usb.py。\n\n详见DESIGN.zh-CN.md、PRINT_UNIVERSAL.csv、DESIGN_STATUS.json及verification。cad_source的正式构建入口为design.py、export.py；复建依赖仓库冻结历史输入，打印无需复建。\n',encoding='utf-8')
 g.write(BENCH/'source_lock.json',{'O19_commit':'98c084a','O19_archive_sha256':g.sha(H/'bench/revO19/PoseDoll_O19_Universal_Design.zip'),'source_sha256':{str(p.relative_to(REPO)).replace('\\','/'):g.sha(p) for p in [*HERE.glob('*.py'),H/'docs/DESIGN_REVO20.zh-CN.md',OUT/'changed_parts.npz',OUT/'changes.json']}})
 files={str(p.relative_to(BENCH)).replace('\\','/'):g.sha(p) for p in BENCH.rglob('*') if p.is_file() and p.name not in ('FILES_SHA256.json','PoseDoll_O20_Universal_Design.zip','local_test_result.json') and '__pycache__' not in p.parts}
 g.write(BENCH/'FILES_SHA256.json',{'schema':'POSEDOLL-O20-FILES/1','files':files})
 archive=BENCH/'PoseDoll_O20_Universal_Design.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name in sorted([*files,'FILES_SHA256.json']):z.write(BENCH/name,name)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,dig in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==dig,name
 g.write(OUT/'package_verification.json',{'status':'PASS','files_checked':len(files),'zip_sha256':g.sha(archive),'zip_bytes':archive.stat().st_size,'physical_qualification':False})
 print('O20 sealed',len(files),'files',g.sha(archive),flush=True)
if __name__=='__main__':main()
