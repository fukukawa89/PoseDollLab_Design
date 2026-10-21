"""Side-by-side actual CAD renders, with final geometry and image provenance."""
from revo23_smooth import *
from package_revo23 import NAMES
from html import escape

digest=sha(B/'assembly.npz');assert digest==sha(GROOT/'assembly.npz')
assert read(GROOT/'detail_scenes.json')['geometry_sha256']==digest
out=B/'verification/user_review_G';out.mkdir(exist_ok=True)
for source in (GROOT/'images').glob('*.png'):
    if 'material_diagnosis' not in source.name and 'native_only' not in source.name:shutil.copy2(source,out/source.name)
old=B/'verification/user_review_F'
for name in ('thigh_l_hip_connection.png','frame__forearm_l_actual.png','frame__pelvis_actual.png'):
    shutil.copy2(old/name,out/('O23F_'+name))
counts=read(B/'verification/physical_rod_count.json');loads=read(B/'verification/load_paths.json')
motion=read(B/'verification/daily_motion.json');edge=read(B/'verification/edge_paths.json')
def figure(name,caption):
    return f'<figure><a href="{name}"><img src="{name}" alt="{escape(caption)}" loading="lazy"></a><figcaption>{escape(caption)}</figcaption></figure>'
def pair(a,al,b,bl):return '<div class="grid">'+figure(a,al)+figure(b,bl)+'</div>'
parts=read(B/'assembly.json')['items']
gallery=''.join(figure(x['key'].replace('/','__')+'_actual.png',NAMES.get(x['body'],x['body'])) for x in parts if x['role']=='structure')
html=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O23G 连接修订与全身检查</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f3ed;color:#253332;font:17px/1.7 "Microsoft YaHei",sans-serif}}main{{max-width:1160px;margin:auto;padding:40px 24px}}h1{{font-size:34px;margin:0 0 10px}}h2{{font-size:24px;margin:8px 0}}p{{max-width:950px}}section{{border-top:1px solid #cad0c8;padding:24px 0 34px}}.eyebrow{{letter-spacing:2px;font-size:13px;color:#52635e}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.gallery{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}figure{{margin:0}}img{{display:block;width:100%;border-radius:10px}}figcaption{{padding:8px 0;color:#52635e;font-size:14px}}a{{color:#1e655f}}code{{font-size:12px;word-break:break-all}}.note{{color:#52635e;font-size:14px}}.status{{padding:16px 20px;background:#e6ece5;border-radius:10px}}@media(max-width:720px){{.grid,.gallery{{grid-template-columns:1fr}}h1{{font-size:27px}}}}
</style><main><p class="eyebrow">POSEDOLL LAB / O23G / 实际几何对照</p><h1>圆整连接，完整落脚</h1>
<p>这次修正杆身的杂乱形状、半悬空的外壁端部、小臂球状支撑，并把主要连接成对布置。下面均为实际 CAD 渲染，可点击放大。</p>
<p><a href="../../preview/index.html?revision=O23G-review-{digest[:12]}">打开可旋转三维模型 ↗</a> · <a href="../../SMOOTH_CONNECTIONS.zh-CN.md">完整设计与检查说明 ↗</a></p>
<div class="status">24 个结构件逐一检查 · {motion['pose_count']} 个日常姿态 + {edge['pose_count']} 个过渡姿态通过 · 每个结构件与相邻单个部件最多 {counts['maximum_rods_per_adjacent_component']} 根连接</div>
<section><h2>1. 大腿：完整圆杆与加宽底座</h2><p>杆身重新生成完整圆截面；需要避让的位置采用圆截面弯杆。连接不再被旧骨架表面裁出缺口，外壁端落在完整内壁的加宽底座上。左右大腿的两端连接采用镜像布局。</p>
{pair('O23F_thigh_l_hip_connection.png','O23F：旧杆身及端部形状','frame__thigh_l_hip_front.png','O23G：圆截面连接与内壁底座')}
{pair('frame__thigh_l_actual.png','O23G：左大腿完整结构件','frame__thigh_r_actual.png','O23G：右大腿完整结构件')}
<p class="note">关节安装端仍保留原有孔座、磁铁和传感器所需的功能形状；这些部位不会全部变成圆柱。</p></section>
<section><h2>2. 小臂：去掉球状支撑</h2><p>旧球状支撑和多余残段已移除。所需连接改为少量连续圆杆；近肘端两条杆分担连接，末端用加宽底座接入内壁。带横孔的块状件是实际布线固定座。</p>
{pair('O23F_frame__forearm_l_actual.png','O23F：球状支撑与旧连接残段','frame__forearm_l_actual.png','O23G：连续圆杆与穿带固定座')}
{pair('frame__forearm_l_actual.png','O23G：左小臂','frame__forearm_r_actual.png','O23G：右小臂，主连接与左侧镜像')}
</section><section><h2>3. 骨盆：两侧髋部连接对称</h2><p>后侧外壁继续保持镜像，左右髋部的主连接也已成对布置。腰部的偏置安装端和部分原关节接口仍有必要差异，因此完整零件尚不完全对称；本页明确展示这些差异。</p>
{pair('O23F_frame__pelvis_actual.png','O23F：外露连接不对称','frame__pelvis_actual.png','O23G：左右髋支路镜像，保留偏置腰接口')}
</section><section><h2>全身检查</h2><p>24 个结构件均为单个闭合实体，所有记录的圆杆和外壁底座均做材料完整性复核，未新增外壁碎孔。{len(loads['rows'])} 处安装区域已完成几何截面筛查，最小值 {min(r['conservative_cut_area_mm2'] for r in loads['rows']):.2f} mm²。布线固定座、通道和维修工具空间同步复查。</p><p class="note">截面筛查用于发现细颈，不能等同于实物强度合格。打印层方向、静载、疲劳、持姿和线束反复弯折仍待实物验证。非相邻部位接触按约定列为提示；未缩减原动作检查集。</p><div class="gallery">{gallery}</div></section>
<p><a href="../../verification/smooth_connections.json">连接与对称性数据</a> · <a href="../../verification/load_paths.json">截面筛查数据</a> · <a href="../../harness/布线与试装说明.zh-CN.md">布线说明</a></p><p class="note">几何版本：<code>{digest}</code></p></main></html>'''
if (B/'verification/stl_export_repair.json').exists() and read(B/'verification/stl_export_repair.json')['passed']:
    html=html.replace('<section><h2>1.', '<p class="status">导出修复完成：32 件 STL 封闭且实际切片通过；原装配几何未改变。<a href="../stl_export_review/index.html">查看原因、检查结果与下载文件 ↗</a></p><section><h2>1.',1)
html=html.replace('<title>','<link rel="icon" href="data:,"><title>',1)
(out/'index.html').write_text(html,encoding='utf8')
put(out/'provenance.json',dict(geometry_sha256=digest,comparison_source_sha256=FHASH,
    source='Direct Blender Workbench renders of actual assembly meshes; no image synthesis or retouching.',
    images={x.name:sha(x) for x in out.glob('*.png')}))
print('REVIEW G',out,flush=True)
