from pathlib import Path
import json,hashlib,html
from build_revo22_fins import O,B,R

plates=json.loads((O/'manifest.json').read_text())['plates'];native=[]
for p in plates:
 r=json.loads((O/'verification'/f"{p['id']}_native_gcode.json").read_text());path=O/'projects'/f"{p['id']}_O22F1_PLA_fins.3mf"
 assert r['project_sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),p['id']
 assert r['all_fin_components_have_first_layer_extrusion'] and r['teeth_without_nearby_path']==0 and r['gcode']['out_of_bed_segment_count']==0
 assert all(x['nearest_extrusion_centerline_mm']<.05 for x in r['teeth_path_checks'])
 native.append(r)
layers=json.loads((O/'verification/body_layer_continuity.json').read_text());assert layers['unsupported_body_layer_island_count']==0 and layers['all_body_components_on_bed']
release=json.loads((O/'verification/release.json').read_text());assert all(not p['issues'] for p in release['geometry_layout_checks'])
designs=[json.loads(p.read_text()) for p in (O/'design').glob('*.json')]
main=[p for p in native if p['plate']!='S00'];mass=sum(p['estimated_filament_g'] for p in main);hours=sum(p['estimated_time_s'] for p in main)/3600
release.update({'status':'DIGITAL_CHECKS_PASSED_WITH_DOCUMENTED_BRIDGES_PHYSICAL_NOT_TESTED','all_11_native_projects_sliced_successfully':True,'all_fin_components_have_first_layer_extrusion':True,'unsupported_fin_body_layer_islands':0,'layer_audit_component_area_threshold_mm2':.02,'source_mesh_max_native_vertex_error_mm':max(p['original_vertices_preserved_within_mm'] for p in native),'intentional_teeth_instances_in_main_plates':sum(len(p['teeth_path_checks']) for p in main),'intentional_teeth_instances_including_S00':sum(len(p['teeth_path_checks']) for p in native),'max_tooth_center_to_extrusion_path_mm':max(x['nearest_extrusion_centerline_mm'] for p in native for x in p['teeth_path_checks']),'all_extrusion_centerlines_within_180mm_bed':True,'main_estimated_filament_g':mass,'main_estimated_hours':hours,'warnings':[{'plate':p['plate'],'message':p['slicer_warnings']} for p in native],'remaining_bridge_note':'Source hole roofs and several small ledges retain bridges. These are documented in remaining_bridge_geometry.json. Geometry sampling is not a physical print-quality or strength qualification.','source_geometry_note':'Original v/f arrays exact before packaging. Native Bambu float serialization changes coordinates by less than 0.00015 mm; topology preserved.','validation_scope':'CAD body clearance, protected volumes, bed roots, fin layer continuity, original part preservation, quantity/layout, native project settings, actual first-layer fin extrusion and tooth-center extrusion. Does not certify deposited bead clearance or physical removal/fit/strength.'})
(O/'verification/release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
readme=f'''# O22-F1 支撑鳍打印套件

入口：双击 `index.html`，用 Edge 或 Chrome 打开彩色三维页。可以旋转、缩放、单独选择零件、隐藏主体、查看剖切及拆除方向；无需联网。

## 交付内容

- `projects/`：A01–A10 共 186 个主套实例（185 个装机件 + P242 焊接量规），以及 S00 的 7 个额外试印件；11 个已经切片的 Bambu Studio 3MF 项目。
- `index.html`：实际打印几何的彩色三维查看页。蓝灰色保留；橙色是鳍和底脚；黄色是刻意嵌入零件的连接齿。颜色用于识别，实际同一种 PLA 打印，不需要 AMS。
- `assembly/tutorials/assembly-o22/index.html`：26 步完整安装教程、原盘编号图、三维装配模型、五金清单和接线说明。
- `零件与支撑清单.csv`：逐盘逐件的原编号、支撑分段、连接齿及最小间隙。
- `验证与打印说明.html` 和 `verification/`：检查结果、真实切片提示与保留桥接的位置。
- `design/`：150 种零件的支撑设计、齿的嵌入量及各分段的退出方向。
- `source/`：生成与验证脚本；修改时以原 O22 工程作为输入。

## 打印方法

1. 在 Bambu Studio 中将 `projects/*_O22F1_PLA_fins.3mf` **打开为项目**，保持 A1 mini、0.4 mm 喷嘴、PLA、首层和普通层高均为 0.20 mm、按层打印、100% 比例。
2. 保持自动支撑关闭、裙边关闭。模型中名为 `FIN_BODY` 和 `BREAKAWAY_TEETH` 的普通零件就是待打印的支撑，不要删去或改为切片器的支撑对象。
3. 保留现有摆放、分组和落盘高度；不要重新自动朝向、自动排列或把子零件拆开后自动落盘。原装配零件的网格、尺寸及 A01–A10 的编号都保持不变。
4. 先打印 S00 检查鳍能否分段取下、低矮托片、细轨和连接齿。主盘重点查看 A01 头部、A02 胸部及 A10 脚掌。若改变层高、材料、流量或喷嘴，必须重新检查间隙和切片。
5. 主套切片估算约 {mass:.0f} g PLA、{hours:.1f} 小时；S00 另计。只是切片估算，不含装配和手工拆支撑。

## 支撑拆除与安装

冷却后取下整件。先识别黄色齿并剪断，再剪开 0.20 mm 底脚连片；扶住蓝灰色厚实骨架，从橙色鳍宽面握持，按三维页所示方向逐片取出。相邻鳍的底脚可能连在一起，不要把整圈支撑硬扯下来。

细轨、弹片、轴承环、PCB 导轨及磁铁槽不能当作施力手柄。托夹低矮支撑不设置连接齿，从侧面推开托片，不向上撬细轨。清除残点后用实际五金和未通电 PCB 试装，再按盘内原编号分袋、进入 S01–S26 安装教程。

**安装教程中的颜色表示零件连接关系，不表示支撑。教程展示的是去支撑后的原件，以各页图例为准。**

## 已完成的数字检查

150 种原件源网格完全一致，主套数量仍为 186。11 盘无盘间实例遗漏，全部位于 180 mm 热盘范围内，盘内组合之间无交叠。鳍主体与原件交叠体积为零；只有已标成黄色的齿存在名义 0.08 mm 嵌入。

每个鳍主体连通实体都触底；以 0.20 mm 层高对鳍单独检查，没有发现面积大于 0.02 mm² 的先悬空后接合层片。高位分支从自身热盘根部连续上升，不在低层零件上起支撑。

11 盘均完成拓竹切片并通过原生网格、设置和路径核对：所有鳍连通实体都有首层挤出，所有 {sum(len(p['teeth_path_checks']) for p in native)} 个连接齿实例都有通过中心附近的实际挤出路径，未生成自动支撑。原生 3MF 浮点写入的最大坐标偏差为 {release['source_mesh_max_native_vertex_error_mm']:.8f} mm，三角形索引不变。

## 必须保留的验证边界

拓竹仍会提示部分零件浮空。预留的鳍顶拆除间隙会产生这种提示，孔顶和部分小悬挑也保留桥接；不能把这些提示全部当作误报，也不要为消除提示重新开启自动支撑。

重点位置：A01 的 X050 在 Z=37.8 mm；A02 的 X046 在 Z=84.4 mm；A10 的 W001 在 Z=20.0 mm、W016/W017 在 Z=8.6 mm。相关截面最远处距下方可用承托约 3.8–4.4 mm，这是几何采样距离，不是已验证的可桥接跨度。详见 `验证与打印说明.html`。

本套件尚未进行实物打印、拆除、装配、强度或表面质量测试。高位薄鳍的稳定性、孔顶桥接和接触面的实际质量须首件确认。CAD 与路径检查不能替代实际耗材、温度、流量和机器状态的验证。

原无支撑文件与旧自动支撑文件未被覆盖。鳍及单层齿结构参考 PrintFins FIN-SPEC（https://github.com/gittrahan/support-fins/blob/main/docs/FIN-SPEC.md）；本套几何按 O22 的零件和保护区独立生成。
'''
(O/'README.zh-CN.md').write_text(readme,encoding='utf-8')
rows=''.join(f'<tr><td>{p["plate"]}</td><td>{next(len(x["items"]) for x in plates if x["id"]==p["plate"])}</td><td>{p["estimated_filament_g"]:.1f} g</td><td>{p["estimated_time_s"]/3600:.1f} h</td><td>{html.escape(p["slicer_warnings"] or "无")}</td></tr>' for p in native)
reporthtml=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O22-F1 验证与打印说明</title><style>body{{font:16px/1.8 system-ui,"Microsoft YaHei",sans-serif;color:#193c44;background:#f3f6f3;margin:0}}main{{max-width:1080px;margin:30px auto;background:white;padding:34px;border-radius:12px}}h1,h2{{line-height:1.3}}h2{{margin-top:32px;font-size:22px}}a{{color:#146f7b}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{padding:10px;border-bottom:1px solid #dce5df;text-align:left}}.note{{background:#fff3d8;padding:16px;border-left:4px solid #d6a32b}}.pass{{background:#e4f2e8;padding:16px}}code{{background:#edf2ee;padding:2px 5px}}@media print{{main{{margin:0;padding:12px}}tr{{break-inside:avoid}}}}</style><main><a href="index.html">← 支撑鳍彩色三维页</a><h1>O22-F1 · 验证与打印说明</h1><p class="pass">150 种原件，186 个主套实例；11 盘完成切片。鳍主体无穿模，所有鳍实体触底，逐层检查无悬空鳍；实际首层路径及 {sum(len(p['teeth_path_checks']) for p in native)} 个齿的路径均已核对。</p><p class="note">尚未实物试印。切片器仍报告部分原件浮空；鳍顶存在拆除间隙，孔顶及小悬挑保留桥接。下表保留原始警告，不能视为全部已消除。</p><h2>打开项目与先后顺序</h2><p>在 Bambu Studio 中打开 <code>projects/*.3mf</code> 为项目：A1 mini / PLA / 0.4 mm 喷嘴，首层和普通层高均 0.20 mm，按层打印，自动支撑和裙边关闭。保持原摆放、分组与比例。<code>FIN_BODY</code> 和 <code>BREAKAWAY_TEETH</code> 是普通模型子零件，必须保留。</p><p>先试 S00，再重点检查主盘 A01 头部、A02 胸部、A10 脚掌的高位支撑与孔顶桥接。主套约 {mass:.0f} g PLA、{hours:.1f} h；S00 另计。数字检查不包含实物拆除难度、表面质量和强度验收。</p><h2>保留桥接的重点位置</h2><table><tr><th>盘 / 零件</th><th>起始打印层 Z</th><th>需观察的内容</th></tr><tr><td>A01 / X050 头部骨架</td><td>37.8 mm</td><td>窄边的鳍间悬挑，最远处距下方可用承托约 4.44 mm</td></tr><tr><td>A02 / X046 胸部骨架</td><td>84.4 mm</td><td>高位小平台，最远处约 3.79 mm；检查薄鳍稳定性</td></tr><tr><td>A10 / W001</td><td>20.0 mm</td><td>局部平台边缘，最远处约 4.44 mm</td></tr><tr><td>A10 / W016、W017 脚掌</td><td>8.6 mm</td><td>孔顶桥接，最远处约 4.16 mm；孔内未塞入封闭支撑</td></tr></table><p>上表是截面采样到上一层原件或下方鳍的水平距离，不能直接当作桥接跨度或打印质量结论。完整数值见 <a href="verification/remaining_bridge_geometry.json">桥接几何记录</a>。</p><h2>逐盘切片记录</h2><table><tr><th>打印盘</th><th>件数</th><th>PLA 估算</th><th>时间估算</th><th>Bambu 原始提示</th></tr>{rows}</table><h2>检查的范围</h2><p>原件 v/f 数组在包装前完全一致；拓竹写出后的最大坐标偏差 {release['source_mesh_max_native_vertex_error_mm']:.8f} mm，三角形索引一致。主体交叠体积为 0；功能保护区交叠小于 10⁻⁶ mm³ 数值容差。黄色齿名义嵌入 0.08 mm，橙色主体不嵌入原件。</p><p>独立鳍逐层截面检查采用 0.20 mm 层高、0.02 mm² 面积阈值和 0.005 mm 邻层容差。路径检查包含首层鳍、连接齿、无自动支撑、180 mm 范围及圆弧边界；路径范围是挤出中心线，不代表耗材实际熔融宽度的测量。</p><p><a href="verification/release.json">总验证 JSON</a> · <a href="verification/body_layer_continuity.json">逐层检查</a> · <a href="零件与支撑清单.csv">零件清单</a> · <a href="assembly/tutorials/assembly-o22/index.html">完整安装教程</a></p></main></html>'''
(O/'验证与打印说明.html').write_text(reporthtml,encoding='utf-8')
print(json.dumps({'main_g':mass,'main_hours':hours,'teeth_instances':release['intentional_teeth_instances_including_S00'],'min_body_gap_mm':min(r['min_gap_mm'] for r in designs if r['min_gap_mm'] is not None),'status':release['status']},ensure_ascii=False))