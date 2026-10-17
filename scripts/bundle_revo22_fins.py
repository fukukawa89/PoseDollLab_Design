from pathlib import Path
import shutil,json,hashlib,gzip,base64,zipfile
from build_revo22_fins import O,B,R
DEST=B/'O22F1_Release';DEST.mkdir(exist_ok=True)
for name in ['index.html','viewer.js','scene.js','manifest.json','README.zh-CN.md','验证与打印说明.html','零件与支撑清单.csv']:
 shutil.copyfile(O/name,DEST/name)
for folder in ['projects','design','assembly']:
 shutil.copytree(O/folder,DEST/folder,dirs_exist_ok=True)
(DEST/'verification').mkdir(exist_ok=True)
for name in ['release.json','body_layer_continuity.json','remaining_bridge_geometry.json']:
 shutil.copyfile(O/'verification'/name,DEST/'verification'/name)
for pattern in ['*_slice.json','*_native_gcode.json']:
 for p in (O/'verification').glob(pattern):shutil.copyfile(p,DEST/'verification'/p.name)
(DEST/'source').mkdir(exist_ok=True)
names=['build_revo22_fins.py','add_revo22_island_fins.py','trim_revo22_fin_fringes.py','package_revo22_fins.py','publish_revo22_fins.py','verify_revo22_fins_layers.py','verify_revo22_fins_native.py','check_revo22_fins_islands.py','audit_revo22_fins_islands.py','review_revo22_fins_bridges.py','finalize_revo22_fins.py','bundle_revo22_fins.py','pack_revo22_a1mini.py','build_revo22_supports.py','verify_revo22_a1mini.py','verify_revo22_native_supports.py','o22_support_gcode.py']
for name in names:shutil.copyfile(R/'scripts'/name,DEST/'source'/name)
(DEST/'source/README.zh-CN.md').write_text('''# 设计与验证脚本

这些脚本用于审阅和在原 O22 仓库内继续修改，不是独立安装程序。标准打印入口是 ../projects/ 中的最终 3MF。

依赖：Python 3.13、NumPy 2.5.3、manifold3d 3.3.2、Shapely 2.1.2；切片使用本机 Bambu Studio 02.08.02.61。软件路径和本地依赖目录见源码。

需要原工程的 print_batch、a1mini/manifest.json、a1mini_supports/design 保护区与面选择、原生支持项目模板，以及 .local/o22-easy-support/S00/manifest.json。脚本应放回原仓库 scripts 目录运行，不能直接在本交付目录运行。

流程：定义鳍方向、分段、保护区；生成连续触底的薄鳍；独立逐层检查；针对原件新层区域添加定点鳍；裁掉不可打印的层边缘；重新核对触底、碰撞和退出路径；写入原生项目、切片并检查实际路径。任何修改后必须重新进行这些检查，不能沿用本次报告。

最终几何在 3MF 内以普通子零件保留：原件、FIN_BODY、BREAKAWAY_TEETH。原件不被布尔修改；颜色查看数据来自最终几何。输入文件散列见 ../verification/source_inputs.json。
''',encoding='utf-8')
inputs={}
manifest=json.loads((O/'manifest.json').read_text())
for plate in manifest['plates']:
 for it in plate['items']:
  source=B/it['source_3mf'];inputs[it['source_3mf']]=hashlib.sha256(source.read_bytes()).hexdigest()
for p in [B/'a1mini/manifest.json',*sorted((B/'a1mini_supports/design').glob('*.json'))]:inputs[str(p.relative_to(B)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
(DEST/'verification/source_inputs.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
# Preserve the original HTTP viewer, and add a lazy file:// data path.
a=DEST/'assembly/tutorials/assembly-o22';scene=json.loads((a/'scene.json').read_text());guide=json.loads((a/'guide-data.json').read_text());raw=(a/scene['geometry_url']).resolve().read_bytes()
payload={'guide':guide,'scene':scene,'geometry_gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
(a/'offline-data.js').write_text('window.O22_ASSEMBLY_OFFLINE='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')
p=a/'app.js';s=p.read_text(encoding='utf-8');start=s.index("if(location.protocol==='file:')throw Error(");end=s.index("canvas=$('#model');",start)
s=s[:start]+'''let raw;if(location.protocol==='file:'){await new Promise((ok,no)=>{let el=document.createElement('script');el.src='offline-data.js';el.onload=ok;el.onerror=()=>no(Error('离线三维数据载入失败，请确认已完整解压。'));document.head.appendChild(el)});let d=window.O22_ASSEMBLY_OFFLINE;guide=d.guide;scene=d.scene;let bytes=Uint8Array.from(atob(d.geometry_gzip_base64),x=>x.charCodeAt(0));raw=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()}else{[guide,scene]=await Promise.all([json('guide-data.json'),json('scene.json')]);const res=await fetch(scene.geometry_url);if(!res.ok)throw Error('几何文件载入失败');raw=await res.arrayBuffer();}''' +s[end:]
p.write_text(s,encoding='utf-8')
print('Release',DEST,'files',len([p for p in DEST.rglob('*') if p.is_file()]),'offline_geometry_mb',len(raw)/1e6)