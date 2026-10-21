"""Build a clean O22-F2 review/print delivery from verified final artifacts."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,zipfile,shutil,collections,csv,datetime
from build_revo22_fins_v2 import R,B,O
OUT=B/'O22F2_Release'
def copy(src,rel):
 dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((O/'manifest.json').read_text(encoding='utf8'));g=json.loads((O/'verification/geometry_final.json').read_text());summary=json.loads((O/'verification/delivery_summary.json').read_text())
assert not OUT.exists(), 'Use a fresh release destination; do not replace an existing release silently.'
OUT.mkdir()
for n in ['index.html','viewer.js','scene.js','risk-data.js','manifest.json','新旧盘号与安装编号对照.csv','待复核出丝位置.csv','验证说明.html','先读我.txt','start_preview.py']:copy(O/n,n)
for p in manifest['plates']:
 name=f"{p['id']}_O22F2_PLA_fins.3mf";s=next(v for v in summary['plates'] if v['plate']==p['id']);assert sha(O/'projects'/name)==s['project_sha256']
 with zipfile.ZipFile(O/'projects'/name) as z:assert z.testzip() is None;assert 'Metadata/plate_1.gcode' in z.namelist()
 copy(O/'projects'/name,Path('projects')/name)
 for tag in ['native_mesh','extrusion_contacts']:copy(O/'verification'/f"{p['id']}_{tag}.json",Path('verification')/f"{p['id']}_{tag}.json")
for n in ['geometry_final.json','remaining_regions.json','delivery_summary.json']:copy(O/'verification'/n,Path('verification')/n)
shutil.copytree(O/'verification/regions',OUT/'verification/regions')
shutil.copytree(O/'assembly',OUT/'assembly')
for n in ['O22_F2_Final_Reference.blend','O22_F2_Orientation_Study.blend','O22_F2_True_Contact_Closeup.blend','final_reference.png','orientation_study.png','true_contact.png']:copy(O/'blender'/n,Path('blender')/n)
for p in g['parts']:
 pid=p['id'];assert sha(O/'parts'/f'{pid}.npz')==p['npz_sha256']
 copy(O/'parts'/f'{pid}.npz',Path('reference/parts')/f'{pid}.npz');copy(O/'design'/f'{pid}.json',Path('reference/design')/f'{pid}.json');copy(O/'orientation'/f'{pid}.json',Path('reference/orientation_search')/f'{pid}.json')
for p in (O/'optimization').glob('*/comparison.json'):copy(p,Path('reference/orientation_comparisons')/(p.parent.name+'.json'))
for name in ['verify_revo22_f2_geometry.py','verify_revo22_f2_extrusions.py','verify_revo22_f2_native_mesh.py','classify_revo22_f2_regions.py','o22_f2_gcode.py']:copy(R/'scripts'/name,Path('reference/verification_code')/name)
(OUT/'reference/README.txt').write_text('本目录用于复核设计，不是额外打印盘。parts/*.npz 包含保形原网格、旋转后零件、鳍和齿的数组；其 SHA-256 与 verification/geometry_final.json 一致。design 为最终尺寸和连接记录。orientation_search 是候选朝向几何初筛，orientation_comparisons 是已保存的详细候选比较；这些不是受力仿真结果。verification_code 保存检查方法供审阅，脚本依赖原设计工程、Python 和几何库，不能在此目录独立运行。打印入口为上级 projects；彩色识别请用上级 index.html。\n',encoding='utf8')
# Identity coverage: no lost or substituted main instance.
old=json.loads((B/'a1mini/manifest.json').read_text());orig=collections.Counter(it['object_name'] for p in old['plates'] if not p.get('optional') for it in p['items'])
new=collections.Counter(it['original_object_name'] for p in manifest['plates'] if not p.get('optional') for it in p['items']);assert orig==new,(orig-new,new-orig)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):self.urls += [v for k,v in attrs if k in ['src','href'] and v]
count=0;missing=[]
for p in OUT.rglob('*.html'):
 parser=Links();parser.feed(p.read_text(encoding='utf-8-sig'))
 for u in parser.urls:
  b=urlsplit(u)
  if b.scheme or b.netloc or not b.path:continue
  q=(p.parent/unquote(b.path)).resolve();count+=1
  if not q.exists() or not q.is_relative_to(OUT.resolve()):missing.append((str(p.relative_to(OUT)),u))
assert not missing,missing
assert len(list((OUT/'projects').glob('*.3mf')))==12
assert len(list((OUT/'verification/regions').glob('*.svg')))==148
# Check remapped assembly identities without changing assembly matrices.
a=json.loads((OUT/'assembly/tutorials/assembly-o22/guide-data.json').read_text());expected={it['original_object_name'].split()[0]:it['object_name'].split()[0] for p in manifest['plates'] if not p.get('optional') for it in p['items']}
for v in a['parts'].values():
 if v.get('original_address') in expected:assert v['address'].startswith(expected[v['original_address']]+'（')
report={'version':'O22-F2','date':'2026-10-06','main_identity_multiset_matches_original':True,'main_instances':sum(new.values()),'native_projects':12,'source_types':len(g['parts']),'local_web_links_checked':count,'missing_or_external_local_links':missing,'annotated_slice_regions':148,'assembly_steps':len(a['steps']),'physical_print_tested':False,'force_or_thermal_simulated':False,'whole_doll_print_reliability_accepted':False,'reason_not_accepted':'148 original-part extrusion regions still lack predecessor coverage in the stated digital model; no physical print/strength validation.'}
(OUT/'verification/release_integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
files=[p for p in OUT.rglob('*') if p.is_file()];catalog={'version':'O22-F2','date':'2026-10-06','status':'engineering_trial','files':[{'path':str(p.relative_to(OUT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]}
(OUT/'交付清单.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf8')
archive=B/'PoseDoll_O22F2_Support_Fins.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,arcname='O22F2_Release/'+str(p.relative_to(OUT)).replace('\\','/'),compress_type=zipfile.ZIP_STORED if p.suffix.lower() in ['.3mf','.npz','.png','.blend'] else zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
archive.with_suffix('.zip.sha256.txt').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps({'release':str(OUT),'archive':str(archive),'archive_MiB':archive.stat().st_size/1048576,'files':len(files)+1,'sha256':sha(archive),'checks':report},ensure_ascii=False,indent=2),flush=True)
