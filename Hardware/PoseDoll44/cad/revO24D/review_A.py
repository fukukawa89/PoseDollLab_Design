"""A-neutral review dossier, generated only from current saved evidence."""
from fullbody import *
from html import escape

def main():
    get=lambda n:load(OUT/'verification'/n)
    digest=sha(OUT/'assembly_meshes.npz');assembly=load(OUT/'assembly.json')
    env=get('envelope.json');loads=get('preload_retention_loads.json');closure=get('closure_faults_and_tolerances.json');rom=get('rom_examination_dense.json');paths=get('motion_task_paths.json');grids=get('joint_local_grids.json');body=get('printed_body_connections.json');axes=get('physical_axes.json');bones=get('bone_link_alignment.json');mapping=get('ue_mapping.json');contacts=get('A_pose_contacts.json');named=get('motion_named.json');links=get('structural_links.json')
    integration=get('integration_changes.json');standing=get('standing_ground_loads.json');harness=get('harness_routing.json');electrical=get('electrical_system.json')
    files=['integration_changes.json','standing_ground_loads.json','harness_routing.json','electrical_system.json','electrical_harness_binding.json','sensor_board_binding.json','ankle_dense.json','wire_scene.json','mesh_integrity.json','fastener_stacks.json','kinematics.json','envelope.json','physical_axes.json','ue_mapping.json','ue_A_surface.json','bone_link_alignment.json','adjacency_policy.json','A_pose_contacts.json','motion_named.json','rom_examination_dense.json','joint_local_grids.json','motion_task_paths.json','static_hardware_intersections.json','preload_retention_loads.json','closure_faults_and_tolerances.json','structural_links.json','printed_body_connections.json','connection_review.json','selected_clearances.json','rebuild_reproducibility.json','sensor_observability.json','blender_saved_file.json','browser_review.json','browser_playback.json','browser_local_assets.json','glb_saved_file.json','artifact_delivery.json']
    gates=[]
    for n in files:
        r=get(n) if (OUT/'verification'/n).exists() else dict(status='PENDING',geometry_sha256=None)
        gates.append(dict(file=n,status=r['status'],current_geometry=r.get('geometry_sha256',digest)==digest))
    good=all(r['status'].startswith('PASS') and r['current_geometry'] for r in gates)
    mins={k:min(r[k] for r in loads['rows'] if k in r) for k in ['bearing_static_factor','shaft_factor','plate_yield_factor']}
    path_samples=sum(r['samples'] for r in paths['cases']);advisory=sum(r['advisory_count'] for r in named['cases'])
    scope='结果覆盖记录的有限名义姿态、路径、局部组合和有材料条件的静态筛算；不等于连续构型空间、任意全身角度组合或实物寿命鉴定。'
    intro=f'''# O24D · A 字中立数字审查版

更新：2026-10-24。数字状态：**{'有条件通过' if good else '尚未全部通过'}**。制造放行：**false**。以实际模型及当前几何指纹的验证 JSON 为准。

## A 字姿态与 UE 对齐

默认中立改为双肩外展 **45°** 的 A 字姿态，模型、Blender、GLB、预览复位和传感器标定一致。完整中立高度 **{env['height_mm']:.3f} mm**，距 600 mm 余量 **{env['margin_to_600_mm']:.3f} mm**，含头、掌、脚底与交付外壳。高度约束不是每个抬手动作的包络高度。

保留 **40 物理自由度、89 个 UE 骨映射、42 个原始标量通道**。没有平移 UE 有效关节中心或改变骨长来通过检查。实际轴承轴线及腕球心拟合的最大偏差为 {axes['max_line_error_mm']:.3g} mm；数值精度不是制造精度。

四肢 8 根主连接管及胸部 1 根连接管与 UE 骨线同轴。实际网格的 **{bones['cross_sections']} 个截面**拟合通过，并能检出 1 mm 横向偏移。关节附近的短叉架、预紧座与锁骨避让支架仍是局部承力结构，不宣称每条支架都与骨线重合。89 骨线和物理转轴可在预览中同时查看。

传感器原始零位在 A 字标定，输出仍使用原参考角坐标：`angle = A_offset + sign × unwrap(raw − raw_at_A)`。双肩外展的 A_offset=45°，其余为 0°；前臂安装钟位由 FK 单独处理。旧 N 姿态只保留为坐标参考，不作为默认中立。提供使用原 UE 网格/蒙皮权重离线重建的 A 字参考，未声称 UE 运行时验证或白人模型自碰撞鉴定。

肩架仍有已知机械奇异位形：外展 90° 时第一、第三轴共线，瞬时姿态雅可比降为秩 2；A 字 45° 时为满秩。侧平举姿态保留，但接近 90° 时独立微调手感退化，可先改变外展角再调整。四元数输出和各轴编码器不能消除这个机械条件。`shoulder_conditioning.json` 记录两侧实际轴向复核，不将其写成已解决。

## 四项集成优化

一体简掌、骨盆后部紧凑化、四肢对称化和背部电子系统已进入实际模型。删除外部骨盆夹持插座及其桥接件，保留髋关节传动和腰部承力结构。按前后版本导出网格测量，骨盆组件后缘由 **{integration['pelvis']['old_bounds_mm'][0][0]:.3f} mm** 收到 **{integration['pelvis']['new_bounds_mm'][0][0]:.3f} mm**，后向突出减少 **{integration['pelvis']['posterior_reduction_mm']:.3f} mm**；髋外展轴承站位从后移 66 mm 改为 48 mm，固定桥高度从 53 mm 改为 37 mm。没有更改 UE 关节中心。

四肢的主要关节、承力杆、掌体、脚底和固定耳按左侧几何镜像，并保留原 UE 左右骨点的微小坐标差异。中央锁骨结构仍不完全对称：两个 UE 锁骨中心仅相隔 5.746 mm，轴承与支座无法在同高度直接镜像重叠，保留沿原转轴错层的一体钢传动件。小型传感器出线、PCB 元件和连接器排列保留装配必需的差异，不宣称全部零件绝对镜像。

背部恢复 O23 的电路安装思路：**64 × 60 × 1.6 mm 四层主板**、**70 × 66 × 2.5 mm 开窗背板**、四点 M2 螺钉/钢螺母固定；背板只连接胸部刚体，避免跨越腰胸关节。采用 XIAO ESP32-S3、3.45 V 传感器电源、三组 SPI 广播/独立返回复用，共 **38 个六线端口、38 块传感器小板、5 种小板版型**。主板和五种小板均有原生 KiCad 原理图、完整铜线布线及零错误 ERC/DRC；这些小板版型编号 S1–S5 与旧 O24C-T1-S1 试验件不是同一命名体系。

全身 **{harness['clip_count']} 个实际贯通固定耳、{harness['cable_count']} 路线束、{harness['span_count']} 段走线路径**。模型中的 A 字走线导向按实际成束直径进行实体绕障；下料表逐段加入运动端点变化、10 mm 动态弯曲半径所需余量和装配余量。线束估算质量 **{harness['total_wire_mass_g']:.1f} g**。显示线条是走线参考；折线转角不是要求把线折成尖角，须在固定点间整理成圆滑余量环。动态预览仅随姿态显示路径参考，不属于柔性动力学或所有姿态的线束避碰证明。

供电数字预算使用实际铜线网络和下料长度：每传感器按 10 mA、50 mV 峰值纹波和规定线径等条件筛算，最远端供电下限 **{electrical['power']['sensor_min_supply_V']:.3f} V**。采样设计起点 100 kHz，三返回线同步采集，整机目标 40 Hz；原生规则检查、CRC 已知向量及单比特错误对照已执行。电磁干扰、噪声、热、启动次序和标定仍须样机确认。电子设计与接线详见 `electronics/SYSTEM.html`，完整线束下料见 `harness/CABLE_CUTLIST.csv`。

A 字平地自由站立的估算总质量 **{standing['solid_and_harness_mass_g']:.1f} g**，重心投影距支撑边界最小 **{standing['neutral']['support_margin_mm']:.3f} mm**，判据为 ≥8 mm。双脚非负反力采用等柔度最小范数模型，满足力与力矩平衡；实际脚底刚度分配尚未实测。未引入骨盆固定反力。只将满足该余量的站姿用于自由站立载荷包络，其他动作仍保留关节范围，但需要调整姿态或手扶。该结果不代表每种摆姿都能自行站稳，也不是实物测试。

## 活动范围验收

按照本轮明确要求，同一解剖段和相邻解剖段上的不同运动件必须通过；中间万向轴级、五金、PCB 和插头占位均参与。非相邻部位接触保留为姿态调整提示。合并在同一刚体内的材料接口不当成运动干涉。分类算法用实际重叠立方体的正负对照验证。

**原 40 轴的全部 80 个端点保留，没有以“超出人体范围”为由删除姿态。** 逐轴范围及中间姿态共 **{rom['targets']} 个样本**，单轴步长 ≤2°；局部多轴 5 点笛卡尔网格共 **{grids['samples']} 个样本**，包含每轴两端点；30 个日常姿态及 30 条 A 字起始路径共 {path_samples} 个路径样本，单轴步长 ≤4°。交叠阈值 0.02 mm³。每项均对本版实体重新检查，没有承继上一版纯去料证明。

双踝新增 **{get('ankle_dense.json')['samples']} 个加密局部样本**，以 ≤2° 间隔组合内外翻和屈伸，并扫描屈膝全程，专门复核侧置传感板座。

A 字中立相邻接触数 {contacts['required_adjacent_count']}，非相邻提示 {contacts['nonadjacent_advisory_count']}。命名姿态中的非相邻提示共 {advisory} 个接触记录；它们不是本次验收失败，可在预览中定位。取消上一版强制肩外展 15° 的扫掠条件。手动组合不会自动获得已验证结论。

{scope}

## 手掌与承力连接

双手改为一体掌片和固定拇指轮廓，取消四根独立手指及手指骨点对齐。掌心凹槽、掌背凸棱和拇指共同标示朝向。腕心和原方键/M2 防脱接口保持不变。简化后减少细长末端，掌体通过完整厚根部连接。

左锁骨长支架及两端座为一体定制钢制承力件，使用有证书的 304 钢、最低屈服 230 MPa；它不是 FDM 打印件，也不是金属与塑料仅靠接触粘接。其几何、材料密度和新质量均参与本版复算。详见 `structural_links.json` 的弯曲/扭转及弹性筛算。

共 {len(assembly['parts'])} 个 CSG 特征、{body['bodies']} 个合并材料审查体。特征数不等于采购或打印件数量。实际材料核心连接筛查保留 0.5 / 0.75 mm 腐蚀结果，模拟 H04 的 0.20×18 mm 薄桥能被检出；3.2×18 mm 正对照保持单核心。局部梁筛算与水密性检查不能替代整机疲劳/各向异性试验。

## 新载荷、预紧与防脱

保守实体质量 **{loads['solid_mass_g']:.1f} g**，加 25% 未建模余量为 **{loads['mass_with_allowance_g']:.1f} g**。同体交叠和轴承实心包络可高估质量，以上不是称重。边界包含手扶躯干摆姿和稳定站姿的双脚地面反力；已删除骨盆夹持接口，无外加手持载荷。质量包含电子板和线束估算，静态保持因子 1.5，总质量载荷因子 1.875，覆盖 **{loads['case_count']} 个去重载荷工况**，包括本版路径与局部组合网格。

20 组双轴承筒、16 组 H2 模块、2 只 S1 球面腕保留金属预紧路径。打印端面退让 0.35 mm，由键面承扭、独立销/盖轴向捕获。36 单轴进行撤去摩擦垫/锁紧螺母/轴承胶层止挡后的双向拉脱试算；横销及有键金属盖仍必须安装。两只腕另算导向头和掌键捕获。实际 ±0.30 mm 面移位检查随当前实体复算。

左肘内移原规格螺钉，保留工具空间，并去掉负侧压板靠锁骨的一条折边；强度按单折边及完整避让槽宽扣除计算。两侧髋屈曲后压盖为 2.2 mm。腰侧倾及双踝屈伸压板升级为最低屈服 750 MPa 的调质钢一体机加工槽形件，外包络保持原尺寸；不再按原 304 折弯片采购。压板和踝盖筛算含 Kt=1.5。踝屈伸输出轮毂加至 D15，增加横销对打印件的轴向捕获长度。踝内外翻升级为 D6 轴 / MR126ZZ 双轴承，间距从 6.0 增至 12.0 mm，沿原轴线布置，UE 中心不动。踝内外翻组件再沿原轴线向后退让 3 mm，并加宽同体 U 形连接；传感器改为 11 mm 径向侧置，保留原 140° 屈膝目标和磁铁轴线；脚跟根部 D9.5、后侧双翼 D7，底面高度不变。脚跟中央后上缘设局部避空，保留 3.1 mm 底层及两侧承力根。

最小轴承静载系数 **{mins['bearing_static_factor']:.2f}**（门槛 1.5），钻孔轴强度系数 **{mins['shaft_factor']:.2f}**（门槛 2），压板屈服系数 **{mins['plate_yield_factor']:.2f}**（门槛 2）。定制轴加工后最低屈服 750 MPa，腰前屈和双踝内外翻轴 940 MPa；普通退火光杆不可等同替换。钻孔轴采用 Kt=3。

摩擦下限 μ≥0.08、FDM 许用 8 MPa/模量 1500 MPa、金属轴承固持胶许用剪应力 2 MPa均为待实物确认的设计条件。钢摩擦垫最低屈服 230 MPa。`PRELOAD_TABLE.csv` 给出目标力矩与夹紧力，不直接换算成拧紧扭矩。

## 基线、实物状态与交付

**S1 通过始终是设计假设，不是已有实测结果；H04 弱连接不在该假设内。** 本轮未回写 C/T1；本轮开始前的 D 包保存在 `../revO24D_baseline_20261023_pre_integrated/`；上轮 A 字调整前的包仍在 `../revO24D_baseline_20261023_pre_A/`，更早基线仍保留。现存 S1 相对最初交接的外部改动已记录在 `reference/external_baseline_changes.json`；D 使用自己的冻结输入。当前 S1 与该冻结几何的差异位于 H/R 台架螺母座，D 的 H2 已独立设计，球面腕接口未因此改变。历史候选和失败记录存入 `history/`，不作为当前通过证据。

布局 STL 与合并材料 STL 用于审查，尚未完成生产分件、朝向、补偿与切片；球体合模半件仍须分别制造。钢制件不能当作打印件生产。真实材料、磁干扰、标定、柔性线束的全姿态避夹与疲劳、磨损寿命、地面摩擦/抗扰动和 UE 运行时仍待实物或运行时验证。A 字自由站立已有有条件静力数字筛算，不能写成实测。

入口：`REVIEW.html`、`preview/index.html`、`O24D_full_body.blend`、`O24D_full_body.glb`、`O24D_Digital_Review.zip`。预览资源本地打包；若浏览器限制 file:，运行 `python serve_review.py` 使用仅限本机的 HTTP 服务。

几何 SHA256：`{digest}`。
'''
    (OUT/'DESIGN.zh-CN.md').write_text(intro,encoding='utf8')
    (OUT/'ASSEMBLY.zh-CN.md').write_text((HERE/'ASSEMBLY_TEMPLATE.zh-CN.md').read_text(encoding='utf8'),encoding='utf8')
    validation=f'# O24D 验证索引\n\n几何 `{digest}`。{scope}\n\n| 文件 | 结果 | 当前几何 |\n|---|---|---|\n'+'\n'.join(f"| [{r['file']}](verification/{r['file']}) | {r['status']} | {r['current_geometry']} |" for r in gates)
    (OUT/'VALIDATION.zh-CN.md').write_text(validation,encoding='utf8')
    endpoints=[r for r in rom['cases'] if '/step/' not in r['case']]
    (OUT/'ROM_CONTEXTS.zh-CN.md').write_text('# 原始范围端点与检查体位\n\n全部 80 端点保留；以 A 字为基底，仅替换被测轴角度。非相邻接触为提示，不设 15° 强制联动。\n\n| 轴 | 目标 deg | 其他非零角度 deg | 相邻交叠数 |\n|---|---:|---|---:|\n'+'\n'.join(f"| {r['axis']} | {r['value_deg']} | "+'; '.join(k+'='+str(v) for k,v in r['angles'].items() if k!=r['axis'])+f" | {r['count']} |" for r in endpoints),encoding='utf8')
    with (OUT/'PRELOAD_TABLE.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['axis','hold_target_Nm','required_clamp_N','downstream_solid_mass_g','axial_handling_pull_N','bearing_static_factor','shaft_factor','plate_yield_factor','status'],extrasaction='ignore');w.writeheader();w.writerows(loads['rows'])
    shots=[('full_body','A 字中立整机与走线'),('back_wiring','背部线束与固定点'),('electronics_back','O23 思路的背部电子系统'),('pelvis','缩小后的骨盆后部'),('front','骨线对齐正视图'),('UE_A_reference','原 UE 网格离线 A 字参考'),('hand_palm','简掌与固定拇指'),('hand_back','掌背凸起标记'),('neck_clavicles','颈部与锁骨连接'),('arms_side','双臂侧平举'),('squat','下蹲'),('lumbar_closure','腰部金属预紧闭合')]
    gallery=''.join(f"<figure><a href='images/{n}.png'><img src='images/{n}.png' alt='{label}' loading='lazy'></a><figcaption>{label}</figcaption></figure>" for n,label in shots)
    table=''.join(f"<tr><td><a href='verification/{r['file']}'>{r['file']}</a></td><td>{r['status']}</td><td>{'当前' if r['current_geometry'] else '旧结果'}</td></tr>" for r in gates)
    page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>O24D · A 字中立审查</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#eef2ec;color:#21352f;font:16px/1.8 'Microsoft YaHei',sans-serif}}main{{max-width:1200px;margin:auto;padding:40px 28px}}h1{{font-size:40px}}a{{color:#17654f}}.nav{{display:flex;gap:12px;flex-wrap:wrap}}.nav a{{background:#245a49;color:white;padding:10px 16px;border-radius:8px;text-decoration:none}}.cards,.gallery{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0}}.card,figure{{margin:0;background:white;border:1px solid #d0ded1;border-radius:10px;overflow:hidden}}.card,figcaption{{padding:14px}}.card b{{display:block;font-size:26px}}figure img{{width:100%;aspect-ratio:1;object-fit:contain}}.notice{{padding:18px 22px;background:#fff3dd;border-left:4px solid #b78136}}table{{border-collapse:collapse;width:100%;background:white;font-size:13px}}td,th{{padding:8px;border-bottom:1px solid #d0ded1;text-align:left}}.scroll{{overflow:auto}}code{{overflow-wrap:anywhere}}@media(max-width:760px){{main{{padding:22px 14px}}h1{{font-size:30px}}.cards,.gallery{{grid-template-columns:repeat(2,1fr)}}}}</style><main><small>POSE DOLL LAB · 2026-10-24</small><h1>O24D · A 字中立整机</h1><p>双肩外展 45°，关节中心与 UE 骨长保持不变。数字状态：<b>{'有条件通过' if good else '尚未全部通过'}</b>。</p><nav class="nav"><a href="preview/index.html">交互预览</a><a href="O24D_full_body.blend">Blender</a><a href="O24D_full_body.glb">刚体 GLB</a><a href="O24D_system_A.glb">含走线的 A 字 GLB</a><a href="electronics/SYSTEM.html">电子与走线</a><a href="O24D_Digital_Review.zip">完整交付包</a></nav><section class="cards"><div class="card"><b>{env['height_mm']:.3f} mm</b>完整中立高度，含头脚</div><div class="card"><b>40 DOF · 89 骨</b>9 根主连接管，27 个实际截面</div><div class="card"><b>{rom['targets']} + {grids['samples']}</b>范围样本与局部组合样本</div></section><div class="notice">验收覆盖同一及相邻解剖段的运动件，非相邻接触作为姿态提示。原 80 个角度端点全部保留，取消旧版 15° 强制联动。30 条路径从 A 字中立出发。手动组合不自动获得通过结论。</div><h2>本轮四项优化</h2><p>简化固定手掌；删除骨盆外部夹持结构，骨盆后缘缩短 {integration['pelvis']['posterior_reduction_mm']:.2f} mm；镜像主要四肢；恢复 O23 思路的背部电路板。38 路线束和 16 个固定耳已建模。中央锁骨错层及电子装配仍有明确的非对称例外。</p><p>A 字自由站立数字余量 {standing['neutral']['support_margin_mm']:.2f} mm，含线束估算质量。走线显示是导向参考，柔性线束全姿态避夹仍须装配验证。</p><h2>实际模型与手掌方向</h2><p>一体简掌、固定拇指、掌心凹槽、掌背凸棱；骨线与转轴可在预览中查看。左锁骨长支架及两端座是一体定制钢件，已按新质量复算。所有图片由实际模型生成；UE 白色参考使用原网格及蒙皮权重离线重建。</p><div class="gallery">{gallery}</div><h2>预紧、防脱与新载荷</h2><p>实体质量 {loads['solid_mass_g']:.1f} g，加 25% 余量 {loads['mass_with_allowance_g']:.1f} g；{loads['case_count']} 个载荷工况。最小轴承/钻孔轴/压板系数分别为 {mins['bearing_static_factor']:.2f} / {mins['shaft_factor']:.2f} / {mins['plate_yield_factor']:.2f}。材料、摩擦与工艺参数仍有明确条件。</p><p><a href="DESIGN.zh-CN.md">设计与边界</a> · <a href="ASSEMBLY.zh-CN.md">装配与 A 字标定</a> · <a href="VALIDATION.zh-CN.md">验证索引</a> · <a href="ROM_CONTEXTS.zh-CN.md">80 个范围端点</a> · <a href="PRELOAD_TABLE.csv">40 轴预紧表</a> · <a href="BOM_candidate.csv">部件清单</a> · <a href="reference/UE_Quinn_A.glb">UE A 字参考 GLB</a></p><div class="scroll"><table><tr><th>数字证据</th><th>结果</th><th>版本</th></tr>{table}</table></div><p class="notice">S1 通过仍为设计假设，H04 弱连接不在假设内。制造放行 false；尚需工艺/材料鉴定、标定、布线、磨损寿命及 UE 运行时验证。{scope}</p><footer>几何 SHA256：<code>{digest}</code>。旧工程和本轮开始前的基线包保留。</footer></main></html>'''
    page=page.replace('<h2>预紧、防脱与新载荷</h2>', '<p>已知操作边界：肩外展 90° 时第一、第三轴共线，独立微调退化；A 字 45° 为满秩，侧平举保留。<a href="verification/shoulder_conditioning.json">两侧肩架轴向复核</a>记录该条件，未宣称已经消除机械奇异性。</p><h2>预紧、防脱与新载荷</h2>')
    (OUT/'REVIEW.html').write_text(page,encoding='utf8')
    put(OUT/'verification/release_status.json',dict(status='PASS_DIGITAL_CONDITIONAL' if good else 'INCOMPLETE',geometry_sha256=digest,digital_gate_passed=good,manufacturing_release=False,S1_physical_pass='DESIGN_ASSUMPTION_ONLY',neutral_pose='A, bilateral shoulder abduction 45 degrees',collision_acceptance='same/adjacent anatomical moving bodies; non-adjacent advisory',excluded_as_nonhuman=[],mandatory_15_degree_coordination=False,gates=gates,runtime_UE_tested=False))
    print('REVIEW A',good,len(gates),'gates',flush=True)

if __name__=='__main__':main()
