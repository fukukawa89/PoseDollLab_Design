from pathlib import Path
import json,hashlib,zipfile,re,shutil
B=Path('PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO22');D=B/'X062_SupportTrial_R1';old=B/'O22F4_Compact';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((D/'manifest.json').read_text());g=json.loads((D/'verification/trial_geometry.json').read_text());n=json.loads((D/'verification/native_final.json').read_text());assert sha(D/m['project'])==m['project_sha256']==n['project_sha256'];assert sha(D/'parts/X062.npz')==m['parts_npz_sha256']==g['parts_npz_sha256'];assert n['native_review_resolved']and g['all_fins_bed_rooted']and g['fin_body_intersection_mm3']==0 and g['all_fin_bodies_have_continuous_body_and_other_fin_clearance'];assert len(list(D.rglob('*.3mf')))==1
assert sha(old/'parts/X062.npz')=='242cfb76cb0b4e1c4ce64c7679f30207dedecf39221be58674bb2bfc817f7ed5'
# Include the unchanged X062 installation steps and figures for convenient reading.
a=old/'assembly/tutorials/assembly-o22/index.html';s=a.read_text();sections=[x for x in re.findall(r'<article class="assembly-step">.*?</article>',s,re.S)if 'id="S12"'in x or 'id="S13"'in x];assert len(sections)==2
for i,x in enumerate(sections):
 x=re.sub(r'<button\b[^>]*>.*?</button>','',x,flags=re.S);x=re.sub(r'href="#(G\d+)"',r'href="../O22F4_Compact/assembly/tutorials/assembly-o22/index.html#\1"',x);x=x.replace('本步需打开打印盘：A06、A07。','盘号沿用原装配说明；本次试印仅替换其中 X062。');sections[i]=x
for filename in ['S12.png','S13.png']:
 (D/'images').mkdir(exist_ok=True);shutil.copy2(a.parent/'images'/filename,D/'images'/filename)
css='<style>body{max-width:1100px;margin:30px auto;padding:0 22px;font:16px/1.7 system-ui,"Microsoft YaHei";color:#203d42}img{max-width:100%;height:auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd8d3;padding:8px;text-align:left}a{color:#087282}.assembly-step{margin:35px 0}button{display:none}</style>'
(D/'安装说明.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>X062 安装沿用说明</title>'+css+'<h1>X062 · 安装沿用说明</h1><p><a href="index.html">返回支撑查看器</a></p><p>本次仅更改打印姿态与支撑。X062 右锁骨本体、孔位及配合结构保持原 O22 设计。下列两步及图片摘自原合盘包；其中 G1–G5 紧固方法链接仍指向原完整装配说明。</p>'+''.join(sections)+'</html>',encoding='utf8')
p=D/'index.html';s=p.read_text();s=s.replace('../O22F4_Compact/assembly/tutorials/assembly-o22/index.html#S12','安装说明.html#S12').replace('../O22F4_Compact/assembly/tutorials/assembly-o22/index.html#S13','安装说明.html#S13').replace('此链接需要原 O22F4_Compact 文件夹仍在旁边。','两步安装说明及配图已随包附上；完整紧固方法沿用原合盘包。');p.write_text(s,encoding='utf8')
ui=dict(model_loaded=True,new_model_roles=3,fin_extraction_meshes=30,old_new_comparison_checked=True,selected_fin_highlight_and_arrow_visually_checked=True,browser_console_errors=0,printed_model_sha256=m['project_sha256'],physical_print_tested=False)
(D/'verification/ui_review.json').write_text(json.dumps(ui,indent=2),encoding='utf8')
files=sorted(p for p in D.rglob('*')if p.is_file()and p.name!='checksums.json');checks={p.relative_to(D).as_posix():sha(p)for p in files};(D/'checksums.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
archive=B/'X062_R1_单件试印包.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,Path(D.name)/p.relative_to(D))
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None
 assert len([p for p in z.namelist()if p.endswith('.3mf')])==1
 for rel,h in checks.items():assert hashlib.sha256(z.read(D.name+'/'+rel)).hexdigest()==h
print('X062_R1_RELEASE_VERIFIED',len(checks)+1,'files','zip_bytes',archive.stat().st_size,'zip_sha256',sha(archive),'original_X062_unchanged',True,flush=True)
