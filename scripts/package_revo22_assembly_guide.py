"""Package the plate-aware guide with its own pictures, CAD buffer and bench references.
Existing engineering/print plate archives are read-only inputs and are not resealed.
"""
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit,unquote
from html.parser import HTMLParser
import hashlib,json,re,posixpath,zipfile
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'Hardware/PoseDoll44';B=H/'bench/revO22';G=H/'tutorials/assembly-o22'
files={p.relative_to(H).as_posix():p.read_bytes() for p in G.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
geo=H/'tutorials/full-doll-o22/geometry_universal.bin';files[geo.relative_to(H).as_posix()]=geo.read_bytes()
for folder,pattern in [('source','*.py'),('profiles','*.json'),('physical_tests','*'),('firmware_binaries','*.bin')]:
    for p in (B/folder).glob(pattern):
        if p.is_file():files[p.relative_to(H).as_posix()]=p.read_bytes()
for rel in ['harness/routing_plan.json','manufacturing/electronic_bom.json','manufacturing/electronic_bom.tsv','manufacturing/RFQ.zh-CN.md','a1mini/manifest.json','a1mini/README.zh-CN.md']:
    p=B/rel;files[p.relative_to(H).as_posix()]=p.read_bytes()
for p in (B/'a1mini/previews').glob('*.svg'):files[p.relative_to(H).as_posix()]=p.read_bytes()
external='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>使用已保存的原工程包</title><link rel="stylesheet" href="style.css"><main><h1>这一文件在原工程包中</h1><p>本下载包包含完整装配文字、26 张 CAD 示意图、可旋转模型、接线表、电子 BOM、首件资料、原固件和局部诊断工具。为避免重复下载，没有再塞入全部打印模型和 KiCad 制造资料。</p><ul><li>打印文件：使用已保存的 PoseDoll_O22_A1mini_Print_Plates.zip。</li><li>Gerber、钻孔、原生 PCB 及原工程文件：使用 PoseDoll_O22_Engineering_Package.zip。</li></ul><p>如果正在原项目电脑上阅读，可打开 <a href="http://127.0.0.1:8770/bench/revO22/a1mini/index.html">原打印盘页面</a> 或 <a href="http://127.0.0.1:8770/tutorials/full-doll-o22/index.html">原设计页面</a>；这两个地址需要原项目预览服务运行。</p><p><a href="index.html">返回拼装教程</a></p></main></html>'''
files['tutorials/assembly-o22/external-files.html']=external.encode('utf8')
# Directly-opened HTML remains readable. A local HTTP server enables the 3D buffer.
serve='''from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import webbrowser
root=Path(__file__).resolve().parent
with ThreadingHTTPServer(('127.0.0.1',8772),partial(SimpleHTTPRequestHandler,directory=str(root))) as server:
    url='http://127.0.0.1:8772/tutorials/assembly-o22/index.html'
    print(url+'  (Ctrl+C to stop)')
    webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
'''
files['start_preview.py']=serve.encode('utf8')
readme='''# O22 拼装教程包

直接打开 tutorials/assembly-o22/index.html 可阅读全部文字、打印盘编号图、26 张 CAD 装配图与接线图。ASSEMBLY.zh-CN.md 是相同内容的文字版。

如需旋转 CAD，在已安装 Python 的电脑上，进入本文件所在目录运行 `python start_preview.py`；它只监听本机 127.0.0.1:8772，并打开浏览器。用 Ctrl+C 结束。没有 Python 时仍可直接阅读 HTML 图片与清单。

按“打印盘找件 → G1–G5 通用装法 → S01–S25 关节 → S26 中央板 → 接线 → 分段上电”的顺序使用。912 件金属件、46 颗磁铁均已分配到具体步骤。诊断脚本只在你明确指定串口时读设备，不烧录、不输出 UE 动画，也不把局部原始诊断当已通过标定的测量。

打印 3MF 与制造 Gerber 请继续使用先前保存的两个原包：PoseDoll_O22_A1mini_Print_Plates.zip、PoseDoll_O22_Engineering_Package.zip。网页中未放进本教程包的原项目下载入口会转到说明页，而不是失效路径。

本教程不改变人偶设计；O11 配合和摩擦使用用户已通过的结论，O22 电子与整机实物项目仍须首件验证。
'''
files['README.zh-CN.md']=readme.encode('utf8')
# Replace only unavailable navigation links in the packaged copy, not the live site.
key='tutorials/assembly-o22/index.html';text=files[key].decode('utf-8-sig');missing=[]
def href(match):
    target=match.group(1);u=urlsplit(target)
    if u.scheme or target.startswith('#'):return match.group(0)
    resolved=posixpath.normpath(posixpath.join(posixpath.dirname(key),unquote(u.path)))
    if resolved in files:return match.group(0)
    missing.append(target);return 'href="external-files.html"'
text=re.sub(r'href="([^"]+)"',href,text)
text=text.replace('下载完整教程包 ↓','原打印 / 工程文件说明 ↗').replace(' download>','>')
files[key]=text.encode('utf8')
mdkey='tutorials/assembly-o22/ASSEMBLY.zh-CN.md';text=files[mdkey].decode('utf8')
for target in missing:text=text.replace(']('+target+')','](external-files.html)')
files[mdkey]=text.encode('utf8')
manifest={'schema':'POSEDOLL-O22-ASSEMBLY-ARCHIVE/1','files':{k:hashlib.sha256(v).hexdigest() for k,v in sorted(files.items())},'unbundled_navigation_to_explanation':sorted(set(missing)),'hardware_access_during_packaging':False}
files['archive_manifest.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf8')
path=B/'PoseDoll_O22_Assembly_Guide.zip'
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for k,v in sorted(files.items()):z.writestr('PoseDoll_O22_Assembly/'+k,v)
with zipfile.ZipFile(path) as z:assert z.testzip() is None
h=hashlib.sha256(path.read_bytes()).hexdigest();path.with_suffix('.zip.sha256').write_text(h+'  '+path.name+'\n',encoding='utf8')
print(json.dumps({'archive':path.name,'files':len(files),'bytes':path.stat().st_size,'sha256':h,'original_packages_modified':False},ensure_ascii=False))
