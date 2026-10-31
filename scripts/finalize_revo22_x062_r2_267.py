"""Verify and zip the completed R2 trial without replacing R1."""
from pathlib import Path
import json,hashlib,zipfile,numpy as np,shutil
from build_revo22_x062_r2_262 import B,S,put,sha
D=B/'X062_SupportTrial_R2';R1=B/'X062_SupportTrial_R1';m=json.loads((D/'manifest.json').read_text());a=json.loads((D/'verification/native_final.json').read_text());g=json.loads((D/'verification/trial_geometry.json').read_text());h=json.loads((D/'verification/hole_clearance_and_reduction.json').read_text());n=np.load(D/'parts/X062.npz');old=np.load(R1/'parts/X062.npz')
assert sha(D/m['project'])==m['project_sha256']==a['project_sha256']==h['project_sha256'];assert sha(D/'parts/X062.npz')==m['parts_npz_sha256']==g['parts_npz_sha256'];assert np.array_equal(n['v'],old['v'])and np.array_equal(n['f'],old['f']);assert a['native_review_resolved']and a['external_island_count']==0 and a['critical_external_count']==0;assert g['all_fins_bed_rooted']and g['fin_body_intersection_mm3']<1e-6 and g['all_fin_bodies_have_continuous_body_and_other_fin_clearance'];assert h['all_supports_clear_of_expanded_hole_guards'];assert len(list(D.rglob('*.3mf')))==1
assert sha(R1/'X062_R1_A1mini_PLA.3mf')=='86adb7aedaa551fdf2c563d3f8eaf588e8bff7f8445b811c8c4322b450343446'
for rel,hash0 in json.loads((R1/'checksums.json').read_text()).items():assert sha(R1/rel)==hash0,rel
hist=[]
for label in ['r2a','r2b','r2c','r2d']:
 p=S/'candidates/X062'/label;de=json.loads((p/'design/X062.json').read_text());au=json.loads((p/'verification/native_final.json').read_text());hist.append(dict(candidate=label,tooth_count=de['tooth_count'],native_project_sha256=au['project_sha256'],external_islands=au['external_island_count'],critical_external_runs=au['critical_external_count'],passed=au['native_review_resolved']))
put(D/'verification/optimization_history.json',dict(baseline_R1_teeth=411,candidates=hist,limits_unchanged=True,global_minimum_proven=False,selection='Fewest teeth among the passing native-sliced candidates in this run.'))
put(D/'verification/ui_review.json',dict(actual_WebGL_mesh_loaded=True,normal_model_roles=4,fin_extraction_meshes=29,old_R1_new_R2_comparison_checked=True,both_hole_views_checked=True,guard_is_visualization_only_not_in_3mf=True,fin_arrow_and_highlight_visually_checked=True,Blender_render_visually_checked=True,browser_console_errors=0,project_sha256=m['project_sha256']))
(D/'请先阅读.txt').write_text('X062 单件支撑试印 R2\n\n打印：X062_R2_A1mini_PLA.3mf\nA1 mini / 0.4 mm 喷嘴 / PLA / 0.20 mm 层高；保留摆放和项目参数，关闭自动支撑。\n预计约 3 小时 23 分、26.81 g，含支撑。\n\n连接齿 411 → 229，减少 44.3%；28 片鳍主体全部落到热盘。\n两个磁铁盖 M2 槽、孔口和径向入口禁止放置连接齿。\n本体、孔位与打印朝向同已打印 R1。\n\n查看：index.html；若浏览器不载入模型，运行 start_preview.py。\n蓝色本体保留；橙色鳍和黄色齿移除；绿色线框只是禁入区，不打印。\n安装图文：安装说明.html。\n\n逐层实际出料检查通过：203 层，无残留独立悬空区或超过既定筛查阈值的无承托路径。\n这不是实物打印保证，也未证明全局最少齿数。\n\n重点复测原堵孔：支撑已避开通道，但该侧理想直线插入扫掠仍轻微擦到原骨架（约 0.51 mm³）。本轮保留已实测本体，未扩孔；完整人工装入动作尚待验证。\n剪除交叉齿的相连中段和残枝后，再逐片退出支撑鳍。\n',encoding='utf-8')
files=sorted(p for p in D.rglob('*')if p.is_file()and p.name!='checksums.json');checks={p.relative_to(D).as_posix():sha(p)for p in files};put(D/'checksums.json',checks);dest=B/'X062_R2_减齿试印包.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,Path(D.name)/p.relative_to(D))
with zipfile.ZipFile(dest)as z:
 assert z.testzip()is None
 assert len([p for p in z.namelist()if p.endswith('.3mf')])==1
 for rel,hash0 in checks.items():assert hashlib.sha256(z.read(D.name+'/'+rel)).hexdigest()==hash0
print('R2_RELEASE_VERIFIED',json.dumps(dict(zip=str(dest),zip_bytes=dest.stat().st_size,zip_sha256=sha(dest),project_sha256=m['project_sha256'],files=len(checks)+1,R1_all_files_unchanged=True,history=hist),ensure_ascii=False),flush=True)
