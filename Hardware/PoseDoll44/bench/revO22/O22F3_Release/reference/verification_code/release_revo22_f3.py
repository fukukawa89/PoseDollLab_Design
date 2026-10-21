"""Freeze verified O22-F3 artifacts into a clean, self-contained trial release."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, hashlib, zipfile, shutil, collections, re
R=Path(__file__).resolve().parents[1]
B=R/'Hardware/PoseDoll44/bench/revO22'
O=B/'a1mini_fins_v3'
OUT=B/'O22F3_Release'
ARCHIVE=B/'PoseDoll_O22F3_Support_Fins.zip'
def read(p):return p.read_text(encoding='utf-8-sig')
def data(p):return json.loads(read(p))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8')
def jswrite(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2))
def copy(src,rel):
 dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
# Correct edition-specific prose, leaving assembly procedures and body meshes intact.
a=O/'assembly'
p=a/'README.zh-CN.md';s=read(p).replace('打印 3MF 与制造 Gerber 请继续使用先前保存的两个原包：PoseDoll_O22_A1mini_Print_Plates.zip、PoseDoll_O22_Engineering_Package.zip。网页中未放进本教程包的原项目下载入口会转到说明页，而不是失效路径。','本版打印工程位于上级 projects（Orca）和 crosscheck_bambu（拓竹），两套几何相同，只选一套打印。F01–F12 是主套，S01 是额外试件。彩色支撑识别、拆除说明与验证状态见上级 index.html。PCB 制造 Gerber 仍使用原 PoseDoll_O22_Engineering_Package.zip。');write(p,s)
old='版本：O22 / A1 mini 10 盘，2026-10-02。图示只展开零件帮助识别，不模拟真实插入轨迹；实际预装和穿装次序按文字步骤。本套件已包含 O22-F{v} 的 11 盘支撑鳍打印工程；KiCad 制造资料仍使用原工程包。可选 T01 传感器小样属于原 O22 工程，本次未另作支撑鳍版本。'
new='本教程保留 O22 装配结构，打印排盘更新为 O22-F3 / A1 mini：F01–F12 共 12 个主套盘，另有 S01 额外试件盘。图示只展开零件帮助识别，不模拟真实插入轨迹；实际预装和穿装次序按文字步骤。KiCad 制造资料仍使用原工程包。旧 T01 电子传感小样不是本版 S01，未包含在这套支撑鳍打印工程中。'
for fn in ['index.html','ASSEMBLY.zh-CN.md']:
 p=a/'tutorials/assembly-o22'/fn;s=read(p)
 for v in ['1','3']:s=s.replace(old.format(v=v),new)
 write(p,s)
p=a/'bench/revO22/a1mini/README.zh-CN.md';s=read(p)
if not s.startswith('> 历史资料'):write(p,'> 历史资料：以下是原 O22 的 A 系列排盘说明，只供安装编号与原电子小样核对。本次打印使用交付包根目录 projects 或 crosscheck_bambu 中的 F 系列和 S01，参数与打印状态以根目录先读我.txt 为准。\n\n'+s)
m=data(O/'manifest.json');g=data(O/'verification/geometry_final.json');d=data(O/'verification/delivery_summary.json')
assert m['version']==d['version']=='O22-F3'
assert d.get('status')=='engineering_trial', 'F3 printing advice withdrawn: resolve F01 ceiling coverage before reissuing.'
assert g['all_geometry_checks_passed'] and len(g['parts'])==150
assert all(p['source_mesh_exact_before_rigid_rotation'] and not p['body_changed'] for p in g['parts'])
assert d['tooth_print_presence_checks_pass'] and d['all_fin_roots_have_actual_first_layer_extrusion']
assert not d['physical_print_tested'] and not d['fin_force_or_thermal_simulated']
oldm=data(B/'a1mini/manifest.json')
orig=collections.Counter(it['object_name'] for p in oldm['plates'] if not p.get('optional') for it in p['items'])
newm=collections.Counter(it['original_object_name'] for p in m['plates'] if not p.get('optional') for it in p['items'])
assert orig==newm and sum(newm.values())==186
assert len(m['plates'])==13 and sum(len(p['items']) for p in m['plates'] if p.get('optional'))==7
# Preflight immutable geometry and project/report identities before creating output.
for p in g['parts']:assert sha(O/'parts'/f"{p['id']}.npz")==p['npz_sha256']
for p in m['plates']:
 stats=next(x for x in d['plates'] if x['plate']==p['id'])
 for engine,folder,report_dir in [('orca','projects',O/'verification'),('bambu','crosscheck_bambu',O/'verification/bambu')]:
  f=O/folder/f"{p['id']}_O22F3_PLA_fins.3mf";h=sha(f);assert h==stats[engine]['project_sha256']
  for tag in ['native_mesh','extrusion_contacts']:
   result=data(report_dir/f"{p['id']}_{tag}.json");assert result['project_sha256']==h
   if tag=='native_mesh':assert result['native_mesh_preserved'] and result['automatic_supports_disabled']
   else:assert result['teeth_missing_printed_layer']==0 and result['gcode_out_of_bed_segments']==0
  with zipfile.ZipFile(f) as z:assert z.testzip() is None;assert 'Metadata/plate_1.gcode' in z.namelist()
assert not OUT.exists(), 'Fresh release destination required; do not overwrite an existing release.'
assert not ARCHIVE.exists()
OUT.mkdir()
print('All input geometry, native projects and hashes match final reports.',flush=True)
for n in ['index.html','viewer.js','scene.js','risk-data.js','manifest.json','新旧盘号与安装编号对照.csv','待复核出丝位置.csv','验证说明.html','先读我.txt','start_preview.py']:copy(O/n,n)
for p in m['plates']:
 for engine,folder,reldir in [('orca','projects','verification'),('bambu','crosscheck_bambu','verification/bambu')]:
  name=f"{p['id']}_O22F3_PLA_fins.3mf";copy(O/folder/name,Path(folder)/name)
  for tag in ['native_mesh','extrusion_contacts','slice']:copy(O/reldir/f"{p['id']}_{tag}.json",Path(reldir)/f"{p['id']}_{tag}.json")
 for tag in ['final_run']:copy(O/'verification'/f"{p['id']}_{tag}.json",Path('verification')/f"{p['id']}_{tag}.json")
for n in ['geometry_final.json','delivery_summary.json','remaining_regions.json','toolchain.json','freecad_toolchain.json','plate_clearance.json','document_and_profile_checks.json','selection.json','final_run.json','neck_width_refinements.json']:
 copy(O/'verification'/n,Path('verification')/n)
shutil.copytree(O/'verification/regions',OUT/'verification/regions')
shutil.copytree(O/'assembly',OUT/'assembly',ignore=shutil.ignore_patterns('archive_manifest.json','README_F2.txt','__pycache__'))
for n in ['final_chest.blend','final_chest.png','contact_closeup.blend','contact_closeup.png','contact_closeup.npz','contact_closeup.json']:copy(O/'blender'/n,Path('blender')/n)
for p in g['parts']:
 for folder,ext in [('parts','npz'),('design','json')]:copy(O/folder/f"{p['id']}.{ext}",Path('reference')/folder/f"{p['id']}.{ext}")
for name in ['verify_revo22_f3_geometry.py','verify_revo22_f3_extrusions.py','verify_revo22_f3_native_mesh.py','qualify_revo22_f3_tooth_tips.py','classify_revo22_f3_regions.py','o22_f3_gcode.py','o22_f2_gcode.py','build_revo22_fins_v3.py','release_revo22_f3.py']:
 copy(R/'scripts'/name,Path('reference/verification_code')/name)
write(OUT/'reference/README.txt','本目录用于复核设计，不是额外打印盘。parts/*.npz 包含保形原网格、旋转后零件、鳍和齿的数组；SHA-256 与 verification/geometry_final.json 一致。design 为最终尺寸与连接记录。最终没有永久本体改形；未采用的改形和朝向试验不混入本交付。verification_code 保存检查方法供审阅，脚本依赖原设计工程、Python 和几何库，不能在这里独立运行。打印入口在上级 projects 或 crosscheck_bambu；彩色识别请打开上级 index.html。\n')
for name in ['f3-final-full.png','f3-contact.png','f3-risk-location.png','f3-risk-layers.png','f3-assembly-cad.png']:copy(R/'output/playwright'/name,Path('verification/browser_qa')/name)
jswrite(OUT/'verification/browser_qa/checks.json',{'viewer_F01_actual_mesh_rendered':True,'ghost_contact_view_rendered':True,'risk_selector_and_adjacent_layer_svg_link_passed':True,'assembly_rotatable_CAD_loaded':True,'assembly_F_addresses_visible':True,'assembly_console_errors':0,'visual_check_only_not_force_simulation':True})
# A new assembly hash catalog replaces the inherited source package catalog.
ac={p.relative_to(OUT/'assembly').as_posix():sha(p) for p in sorted((OUT/'assembly').rglob('*')) if p.is_file()}
jswrite(OUT/'assembly/archive_manifest.json',{'schema':'POSEDOLL-O22-F3-ASSEMBLY-ARCHIVE/1','date':'2026-10-06','files':ac})
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):self.urls += [v for k,v in attrs if k in ['src','href'] and v]
count=0;missing=[]
for p in OUT.rglob('*.html'):
 parser=Links();parser.feed(read(p))
 for u in parser.urls:
  b=urlsplit(u)
  if b.scheme or b.netloc or not b.path:continue
  q=(p.parent/unquote(b.path)).resolve();count+=1
  if not q.exists() or not q.is_relative_to(OUT.resolve()):missing.append((str(p.relative_to(OUT)),u))
assert not missing,missing
assert len(list(OUT.rglob('*.3mf')))==26
assert len(list((OUT/'verification/regions').glob('*.svg')))==149
assert len(list((OUT/'reference/parts').glob('*.npz')))==150
assembly=data(OUT/'assembly/tutorials/assembly-o22/guide-data.json')
assert len(assembly['steps'])==26
expected={it['original_object_name'].split()[0]:it['object_name'].split()[0] for p in m['plates'] if not p.get('optional') for it in p['items']}
matched=0
for v in assembly['parts'].values():
 if v.get('original_address') in expected:
  assert v['address'].startswith(expected[v['original_address']]+'（');matched+=1
assert assembly['f3_plate_manifest_sha256']==sha(OUT/'manifest.json')
report={'version':'O22-F3','date':'2026-10-06','main_identity_multiset_matches_original':True,'main_instances':186,'extra_sample_instances':7,'native_projects':26,'source_types':150,'source_body_meshes_unchanged':True,'project_and_NPZ_hashes_match_final_reports':True,'local_web_links_checked':count,'missing_or_external_local_links':missing,'annotated_orca_slice_regions':149,'bambu_slice_regions':145,'assembly_steps':26,'assembly_remapped_instances_checked':matched,'physical_print_tested':False,'force_or_thermal_simulated':False,'whole_doll_print_reliability_accepted':False,'reason_not_accepted':'Part-body extrusion island candidates remain (Orca 149 / Bambu 145); no physical print, removal or fin strength validation.'}
jswrite(OUT/'verification/release_integrity.json',report)
files=sorted(p for p in OUT.rglob('*') if p.is_file())
jswrite(OUT/'交付清单.json',{'version':'O22-F3','date':'2026-10-06','status':'engineering_trial','files':[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
print('Release integrity passes; archiving',len(files)+1,'files.',flush=True)
with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,arcname='O22F3_Release/'+p.relative_to(OUT).as_posix(),compress_type=zipfile.ZIP_STORED if p.suffix.lower() in ['.3mf','.npz','.png'] else zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(ARCHIVE) as z:assert z.testzip() is None
h=sha(ARCHIVE);ARCHIVE.with_suffix('.zip.sha256.txt').write_text(h+'  '+ARCHIVE.name+'\n',encoding='ascii')
print(json.dumps({'release':str(OUT),'archive':str(ARCHIVE),'archive_MiB':round(ARCHIVE.stat().st_size/1048576,1),'files':len(files)+1,'sha256':h,'checks':report},ensure_ascii=False,indent=2),flush=True)
