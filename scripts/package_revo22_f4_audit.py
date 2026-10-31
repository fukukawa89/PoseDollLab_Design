"""Freeze a complete inspection-only bundle; not a new print release."""
from pathlib import Path
import sys,json,hashlib,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';D=O/'review';F3=B/'O22F3_Release'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
s=read(D/'all_parts.json');assert s['inspection_complete'] and s['type_count']==150 and s['main_instance_count']==186 and s['candidate_native_checked']==102 and s['completed_native_projects']==26
assert s['audit_schema']=='local-extrusion-v2-preserve-nested-islands' and not s['unmapped_native_regions'] and not s['F4_print_release_approved']
g=read(O/'candidate_geometry.json');assert len(g)==102 and all(x['geometric_constraints_passed'] for x in g)
controls=read(O/'audit/controls_v2/summary.json');assert controls['passed']
native_rows=[]
for engine,src in [('Orca','projects'),('Bambu','crosscheck_bambu')]:
 for p in (O/'audit/native_baseline'/engine).glob('*.json'):
  r=read(p);assert r['audit_schema']==s['audit_schema']
  project=F3/src/(p.stem+'.3mf');assert hashlib.sha256(project.read_bytes()).hexdigest()==r['project_sha256']
  native_rows.append({'engine':engine,'project':project.name,'sha256':r['project_sha256'],'detached':len(r['detached_bead_regions']),'unresolved_paths':r['unresolved_count']})
assert len(native_rows)==26
assert sum(1 for r in s['rows'] if r['Orca_spans']+r['Orca_islands']>0)==len(read(D/'evidence/layers/index.json'))
for row in s['rows']:
 for name in [f"records/{row['id']}.json",f"records/{row['id']}.js",f"geometry/{row['id']}_baseline.js"]:assert (D/name).exists()
 if row['candidate_label']:assert (D/'geometry'/f"{row['id']}_candidate.js").exists()
raw=D/'evidence/raw';raw.mkdir(exist_ok=True)
for engine in ['Orca','Bambu']:
 (raw/engine).mkdir(exist_ok=True)
 for p in (O/'audit/native_baseline'/engine).glob('*.json'):shutil.copy2(p,raw/engine/p.name)
for name,source in [('baseline_geometry.json',O/'audit/baseline/all_parts.json'),('candidate_geometry.json',O/'candidate_geometry.json'),('candidate_native.json',O/'native_candidate_progress_v2.json'),('orientation_choices.json',O/'native_review_choices.json')]:shutil.copy2(source,raw/name)
shutil.copytree(O/'audit/controls_v2',raw/'controls_v2',dirs_exist_ok=True)
readme=f"""O22 全零件支撑检查 · 2026-10-06

检查范围：150 类 / 186 个主套打印实例（185 件装机零件 + 1 件治具），另有 7 个额外样件。
原生切片：Orca 13/13、Bambu 13/13，均完成逐层实际出丝检查。
几何初筛：102 类保留局部缺覆盖区；综合实际出丝后，{s['native_review_types']} 类保留待处理项，{s['no_flags_types']} 类未检出本次检查所列问题。
这些是保守的几何筛查标记，不代表所有被标记零件一定会打印失败；未标记也不等于实物验收通过。

已建立 408 套重新定向的支撑候选，其中 102 套完成实际 Orca 单件切片复核。
这 102 套候选通过：支撑主体不穿模、每个鳍落盘、连接齿与两侧实体连接、功能保护区不被侵入、高薄板加强等几何约束。
整套候选仍有待处理的出丝位置，尚未发布为 F4 打印包。
本轮本体改形为 0；源本体及装配几何保留。

打开 index.html 查看真实三维网格；蓝色为保留的本体，橙色为鳍主体，黄色为连接齿，红框为待处理的实际出丝区域。
如果直接打开浏览器无法加载，可运行 start_preview.py（只使用 Python 标准库）。
完整清单：all_parts.csv。逐件原始记录：records/。相邻层实际出丝图：evidence/layers/。
原生出丝报告、几何报告、控制样例与哈希校验：evidence/raw/、integrity.json。
本报告不包含用于开始打印的 3MF；实验候选仍保存在项目工作目录 a1mini_fins_v4/candidates/。

F01 胸架的原内顶壁问题已确认。候选把该面倾角从约 15.7°提高到约 52.5°；其余部位仍须继续处理，不能将局部改善当作整件通过。
已有支撑根部和连接齿的实体检查，不能替代所有悬空区域的承托检查。
旧版只检查整个截面是否悬空的方法会漏掉侧壁相连的屋顶；本轮已修正。
本轮检查器还修正了转换嵌套空腔截面时遗漏内部独立实体的问题，最终结果全部采用修正版，旧统计已隔离。
没有实物试打、材料热变形或支撑力学仿真。完整方法见 METHOD.txt。
"""
(D/'README.txt').write_text(readme,encoding='utf8')
(D/'start_preview.py').write_text("""from pathlib import Path\nfrom http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler\nfrom functools import partial\nimport webbrowser\nroot=Path(__file__).resolve().parent\nserver=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))\nurl='http://127.0.0.1:'+str(server.server_address[1])+'/index.html'\nprint(url,flush=True)\nwebbrowser.open(url)\ntry:server.serve_forever()\nexcept KeyboardInterrupt:pass\nfinally:server.server_close()\n""",encoding='utf8')
integrity={'inspection_complete':True,'physical_print_qualified':False,'source_bodies_changed':0,'audited_native_projects':native_rows,'geometry_controls_passed':True,'native_controls_passed':True,'source_model_hashes_verified':150,'files':[]}
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='integrity.json':integrity['files'].append({'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'integrity.json').write_text(json.dumps(integrity,ensure_ascii=False,indent=2),encoding='utf8')
dest=B/'O22_full_support_audit_20261006.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,Path('O22_support_audit')/p.relative_to(D))
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
result={'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(integrity['files'])+1,'inspection_only':True,'unresolved_types':s['native_review_types'],'no_flags_types':s['no_flags_types']}
(O/'audit_bundle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False),flush=True)

