"""Withdraw F01 printing advice after the confirmed internal-ceiling coverage failure."""
from pathlib import Path
import json,hashlib,shutil,zipfile,os
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';A=B/'F01_F3_audit';OUT=B/'O22F3_Release'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def read(p):return p.read_text(encoding='utf-8-sig')
warning='F01 / O22-F3 试打建议已撤回：盒腔内顶板缺少支撑，当前请勿打印 F01。其它盘也不能沿用原检查结果视为已通过全面支撑覆盖验收。已有支撑的连接检查不等于所有悬空部位获得支撑。'
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>F01 内顶板漏支撑复核</title><style>body{font-family:system-ui,"Microsoft YaHei",sans-serif;line-height:1.7;max-width:1100px;margin:32px auto;padding:0 24px;color:#223b44}h1{font-size:30px}.notice{padding:18px;background:#ffe5e2;border-left:6px solid #b82131}img{max-width:100%;height:auto}a{color:#1e668a}li{margin:10px 0}</style><h1>F01 内腔顶板：已确认漏支撑</h1><p class="notice"><strong>暂勿打印当前 F01_O22F3_PLA_fins。</strong>此前建议先试 F01 不成立，已撤回。未修改打印几何；本页是对已交付文件的复核证据。</p><p>下图由交付零件的真实网格渲染。红色是漏掉的内顶面；橙色为现有支撑、黄色为连接齿。相机转向盒腔以展示问题。</p><img src="F01_unsupported_ceiling.png" alt="红色内顶面下方没有支撑，现有橙色支撑停在盒体外部下方"><ol><li>红色内顶面为 23 × 96 mm，面积 2,208 mm²；打印高度约 Z=101.97–126.90 mm。</li><li>现有连接齿最高仅到 Z=91.31 mm，未接触这一内顶面。</li><li>内顶面与热盘夹角约 15.73°。以 0.20 mm 层高计算，面在水平方向每层推进约 0.710 mm。</li><li>原生 Orca G-code 在 Z=110 mm 有约 27.74 mm 的连续路径缺少前层承托；两端仍有连接，切片将其标为 Overhang wall，线宽约 0.42 mm。这意味着依赖跨空成形，不能据此保证不下垂或失败。</li></ol><h2>实际相邻层出丝</h2><img src="F01_ceiling_Z110.svg" alt="109.8毫米与110毫米两层实际出丝及无前层承托路径"><h2>原检查为什么漏掉</h2><p>旧检查把一层的出丝合并成连通区域，只在整个区域几乎不接触前层时报告悬空。内顶板仍连着侧壁，因而被放过。鳍板生成又排除了被低层本体挡住的垂直落盘通路，却没有把因此失去支撑的关键面判为交付失败。之前报告的 149 / 145 处并不代表全部缺支撑区域。</p><h2>修正约束</h2><p>必须重新选择朝向，让盒腔内顶面可自支撑、朝上，或能从热盘建立不穿模的支撑通路；若仍不可行，再考虑将盒体改为单独安装件并核对安装、PCB 与姿态包络。不能从盒底上建立新鳍来违反全落盘要求，也不能继续仅增加盒体外侧支撑。</p><p>当前没有给出新打印版，也没有做熔丝或受力仿真；不能声称该件必然坍塌或能够可靠打印。</p><p><a href="F01_ceiling_audit.json">测量与路径证据 JSON</a> · <a href="F01_unsupported_ceiling.blend">实际网格标色 Blender 文件</a></p></html>'''
(A/'index.html').write_text(html,encoding='utf8')
(A/'暂勿打印_F01.txt').write_text(warning+'\n\n内顶面 2208 mm²，Z=101.97–126.90 mm；齿最高 Z=91.31 mm。实际 G-code 在 Z=110 mm 存在约 27.74 mm 无前层承托路径，两端有连接。详见 index.html 和 F01_ceiling_audit.json。\n尚未输出已修复版本。\n',encoding='utf8')
archive=B/'PoseDoll_O22F3_Support_Fins.zip';backup=A/'F3_original_delivery_before_withdrawal.zip'
assert archive.resolve().is_relative_to(R.resolve()) and backup.resolve().is_relative_to(R.resolve())
assert not backup.exists(),'Original-delivery backup already exists; inspect before rerunning.'
shutil.copy2(archive,backup);assert sha(archive)==sha(backup)
for root in [B/'a1mini_fins_v3',OUT]:
 target=root/'verification/F01_audit';target.mkdir(parents=True,exist_ok=True)
 for name in ['index.html','暂勿打印_F01.txt','F01_ceiling_audit.json','F01_ceiling_Z110.svg','F01_unsupported_ceiling.png','F01_unsupported_ceiling.blend']:shutil.copy2(A/name,target/name)
 (root/'暂勿打印_F01.txt').write_text(warning+'\n\n复核证据：verification/F01_audit/index.html\n打印几何保持原样，尚未提供已修复版。\n',encoding='utf8')
 for name,prefix in [('index.html',''),('验证说明.html',''),('assembly/tutorials/assembly-o22/index.html','../../../')]:
  p=root/name;s=read(p);banner='<div id="f01-withdrawal" style="background:#ffe5e2;color:#801827;border:3px solid #bd3240;padding:20px;font:600 16px/1.7 system-ui,Microsoft YaHei,sans-serif">'+warning+' <a href="'+prefix+'verification/F01_audit/index.html">查看已确认的问题与证据</a>。以下旧报告保留供审计，原 F01 试打建议作废。</div>'
  assert 'id="f01-withdrawal"' not in s
  if '<body>' in s:s=s.replace('<body>','<body>'+banner,1)
  else:s=s.replace('<main>','<main>'+banner,1)
  s=s.replace('这是 O22-F3 工程试打版。','这是已撤回 F01 试打建议的 O22-F3 存档版。').replace('先用 S01 验证拆齿与配合；S01 不能替代胸架等高件的单件验证。','当前暂停试打 F01，内顶壁需要重新设计支撑。').replace('先用 S01 验证齿的连接和拆除，再单独试打 F01 胸架。','原 F01 试打建议已撤回；需修复内顶壁支撑后重新验收。')
  p.write_text(s,encoding='utf8')
 p=root/'先读我.txt';s=read(p).replace('先试 S01，再试 F01；','F01 暂勿打印；');p.write_text(warning+'\n\n'+s,encoding='utf8')
 p=root/'verification/delivery_summary.json';d=json.loads(read(p));d.update(status='withdrawn_pending_support_redesign',F01_print_recommendation_withdrawn=True,complete_support_coverage_verified=False,known_blockers=[{'part':'X046','region':'controller enclosure internal ceiling','unsupported_area_mm2':2208,'evidence':'F01_audit/F01_ceiling_audit.json'}]);dump(p,d)
# Keep report hashes honest after adding the withdrawal banner to assembly HTML.
ap=OUT/'assembly/archive_manifest.json';d=json.loads(read(ap));d['files']={p.relative_to(OUT/'assembly').as_posix():sha(p) for p in sorted((OUT/'assembly').rglob('*')) if p.is_file() and p!=ap};d['F01_print_advice_withdrawn']=True;dump(ap,d)
p=OUT/'verification/release_integrity.json';d=json.loads(read(p));d.update(F01_print_recommendation_withdrawn=True,complete_support_coverage_verified=False,reason_not_accepted='Confirmed 2208 mm2 unsupported internal ceiling in F01. Previous connected-island test missed attached overhangs; all-plate support coverage requires renewed review.');dump(p,d)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):self.urls.extend(v for k,v in attrs if k in ['href','src'] and v)
count=0
for p in OUT.rglob('*.html'):
 l=Links();l.feed(read(p))
 for u in l.urls:
  q=urlsplit(u)
  if q.scheme or q.netloc or not q.path:continue
  f=(p.parent/unquote(q.path)).resolve();assert f.is_relative_to(OUT.resolve()) and f.exists(),(p,u);count+=1
# Prevent release helper from silently reissuing this explicitly withdrawn status.
p=R/'scripts/release_revo22_f3.py';s=read(p);needle="assert m['version']==d['version']=='O22-F3'";assert needle in s;s=s.replace(needle,needle+"\nassert d.get('status')=='engineering_trial', 'F3 printing advice withdrawn: resolve F01 ceiling coverage before reissuing.'",1);p.write_text(s,encoding='utf8');shutil.copy2(p,OUT/'reference/verification_code'/p.name)
p=OUT/'交付清单.json';catalog=json.loads(read(p));catalog['status']='withdrawn_pending_support_redesign';catalog['files']=[{'path':q.relative_to(OUT).as_posix(),'bytes':q.stat().st_size,'sha256':sha(q)} for q in sorted(OUT.rglob('*')) if q.is_file() and q!=p];dump(p,catalog)
tmp=B/'PoseDoll_O22F3_Support_Fins.withdrawal.zip';assert not tmp.exists();assert tmp.resolve().is_relative_to(R.resolve())
with zipfile.ZipFile(tmp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.comment=b'F01 PRINTING ADVICE WITHDRAWN: unsupported internal ceiling. Read root notice before using.'
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,'O22F3_Release/'+p.relative_to(OUT).as_posix(),compress_type=zipfile.ZIP_STORED if p.suffix.lower() in ['.3mf','.npz','.png'] else zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(tmp) as z:assert z.testzip() is None;assert 'O22F3_Release/暂勿打印_F01.txt' in z.namelist()
os.replace(tmp,archive);archive.with_suffix('.zip.sha256.txt').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps({'withdrawal_recorded':True,'print_meshes_unchanged':True,'original_archive_preserved':str(backup),'archive_sha256':sha(archive),'local_links_checked':count,'audit':str(A/'index.html')},ensure_ascii=False,indent=2),flush=True)
