from pathlib import Path
import json,hashlib,zipfile,shutil
from build_revo22_fins import R,B
D=B/'O22F1_Release'
a=D/'assembly'
old=json.loads((a/'archive_manifest.json').read_text())
(D/'verification/original_assembly_archive_manifest.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
(a/'README.zh-CN.md').write_text('''# O22-F1 配套安装教程

直接用 Edge 或 Chrome 打开 tutorials/assembly-o22/index.html，可阅读 26 步安装说明、编号图、CAD 图、五金和接线表。点击“查看本步可旋转 CAD / 单件识别”会按需载入本地三维数据，已增加离线资源通路。

打印工程统一使用上级目录 ../projects/ 内的 O22-F1 支撑鳍 3MF。支撑标色、拆除方法与打印参数见 ../index.html。安装教程的颜色表示上下游骨架关系，教程内显示的是已经去掉支撑的原件。

原件编号及安装尺寸不变。按“打印盘找件 → G1–G5 通用装法 → S01–S25 关节 → S26 中央板 → 接线 → 分段上电”使用。电子制造资料继续使用原 PoseDoll_O22_Engineering_Package.zip。

原 O22 的首件验证边界保持有效。支撑鳍尚未实物试印，必须先检查拆除、孔槽、细轨、接触面和高位薄鳍。技术上仍可运行 python start_preview.py 使用本地 HTTP 查看，但不是阅读文字、图片或新版离线三维入口的必要条件。
''',encoding='utf-8')
current={str(p.relative_to(a)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.rglob('*')) if p.is_file() and p.name!='archive_manifest.json'}
(a/'archive_manifest.json').write_text(json.dumps({'schema':'POSEDOLL-O22F1-ASSEMBLY-ARCHIVE/1','adaptations':['Printing links point to O22-F1','Support-removal note added','Lazy embedded geometry supports local file viewing','Assembly geometry and installation steps preserved'],'files':current},ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copyfile(R/'scripts/finish_revo22_fins_release.py',D/'source/finish_revo22_fins_release.py')
qa={'review_date':'2026-10-05','tested_url':'http://127.0.0.1:8778/bench/revO22/O22F1_Release/index.html','support_viewer_samples':['S00 complete plate','P033 isolated with fin and tooth colors','X005 isolated low rail supports','A02 X046 isolated chest fins'],'assembly_viewer':{'step':'S03','available_steps':26,'offline_embedded_data_branch_loaded':True,'browser_console_errors':0},'missing_local_html_references':0,'literal_file_protocol_tested':False,'literal_file_protocol_note':'The automation browser blocks file://. The same embedded-data loading branch was successfully exercised over localhost with ?offline=1.','screenshots':['previews/S00.png','previews/P033.png','previews/X005.png','previews/X046.png','previews/assembly_S03.png']}
(D/'verification/viewer_review.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
files=sorted(p for p in D.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(D/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(D)).replace('\\','/') for p in files)+'\n',encoding='utf-8')
archive=B/'PoseDoll_O22F1_Support_Fins.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,'O22F1_Release/'+str(p.relative_to(D)).replace('\\','/'))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 projects=[n for n in z.namelist() if n.startswith('O22F1_Release/projects/') and n.endswith('.3mf')];assert len(projects)==11
 count=len(z.namelist())
sha=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256.txt').write_text(sha+'  '+archive.name+'\n',encoding='utf-8')
print(json.dumps({'archive':str(archive),'files':count,'native_projects':len(projects),'archive_bytes':archive.stat().st_size,'sha256':sha,'zip_crc_check':'PASS'},ensure_ascii=False))