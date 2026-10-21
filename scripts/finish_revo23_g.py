"""Publish only the checked G assembly; preserve all earlier review snapshots."""
from revo23_smooth import *
from package_revo23 import writecsv,NAMES

def publish():
    st=read(GROOT/'staging.json');digest=sha(GROOT/'assembly.npz');assert digest==st['geometry_sha256']
    for k,h in st['candidate_files'].items():assert sha(GROOT/(k.replace('/','__')+'.npz'))==h
    positive=read(GROOT/'positive_sweep_rebuild.json');assert positive['passed']
    for r in positive['rows']:assert sha(GROOT/(r['key'].replace('/','__')+'.npz'))==r['candidate_sha256']
    for name in ('daily_motion.json','edge_motion.json','fixed_interfaces.json','smooth_connections.json','continuous_walls.json','physical_rod_count.json','load_paths.json'):
        d=read(GROOT/name);assert d['geometry_sha256']==digest and d['passed'],name
    loads=read(GROOT/'load_paths.json');assert min(r['conservative_cut_area_mm2'] for r in loads['rows'])>=20
    g=read(GROOT/'geometry.json');assert g['geometry_sha256']==digest and not g['geometry']['invalid_parts'] and g['kinematics']['passed'] and g['geometry']['height_under_800mm']
    access=read(GROOT/'verification/backpack_tool_access.json');assert access['geometry_sha256']==digest and access['slim_tool_plan_passed'] and access['pcb_removal']['passed']
    wire=read(GROOT/'wire_fixture_verification.json');assert wire['passed']
    for k,h in wire['candidate_mesh_hashes'].items():assert sha(GROOT/(k.replace('/','__')+'.npz'))==h
    routes=read(GROOT/'harness/routing_plan.json');assert routes['capacity_passed'] and not routes['body_sections_missing_seats']
    cfg=read(CFG);cfg['revision']=GREV
    cfg['notes']=[x for x in cfg['notes'] if not x.startswith(('O23F:','O23G:'))]
    cfg['notes'].append('O23G: full circular struts with buried broad wall feet; old cut-off rod remnants removed outside functional envelopes; bilateral principal connections, documented offset-interface exceptions; no more than three connections to any single adjacent module.')
    put(CFG,cfg)
    shutil.copy2(GROOT/'assembly.npz',B/'assembly.npz');shutil.copy2(GROOT/'assembly.json',B/'assembly.json')
    for name,target in [('geometry.json','geometry.json'),('daily_motion.json','daily_motion.json'),('edge_motion.json','edge_paths.json'),
        ('fixed_interfaces.json','fixed_interfaces.json'),('smooth_connections.json','smooth_connections.json'),('smooth_connections.json','clean_design.json'),
        ('physical_rod_count.json','physical_rod_count.json'),('continuous_walls.json','continuous_walls.json'),('load_paths.json','load_paths.json'),
        ('verification/backpack_tool_access.json','backpack_tool_access.json')]:shutil.copy2(GROOT/name,B/'verification'/target)
    positive['geometry_sha256']=digest;put(B/'verification/positive_sweeps.json',positive)
    for name,target in [('wire_seats.json','wire_seats.json'),('wire_channels.json','wire_channels.json'),('wire_fixture_verification.json','wire_fixture_verification.json'),('harness/routing_plan.json','routing_plan.json')]:
        r=read(GROOT/name);r['geometry_sha256']=digest
        if target=='routing_plan.json':r['schema']='POSEDOLL-O23G-HARNESS/1'
        put(B/'harness'/target,r)
    shutil.copy2(GROOT/'harness/preliminary_cut_list.csv',B/'harness/preliminary_cut_list.csv')
    parts,p,c=load_g();N=frames(p,p['neutral_raw_deg']);kept={}
    for k,x in parts.items():
        if x['role']=='structure':kept[k+'|v'],kept[k+'|f']=vf(raw_keep(k,parts,p,N))
    np.savez_compressed(B/'retained_interfaces.npz',**kept)
    put(B/'design/smooth_revision.json',dict(revision=GREV,geometry_sha256=digest,source_geometry_sha256=FHASH,
        minimum_geometric_cut_screen_mm2=20,scope='Geometric bottleneck screen, not a strength rating or manufacturing qualification.',manufacturing_release=False))
    print('PUBLISHED G',digest,flush=True)

def notes():
    digest=sha(B/'assembly.npz');g=read(B/'verification/geometry.json')['geometry'];s=read(B/'verification/smooth_connections.json')
    counts=read(B/'verification/physical_rod_count.json');loads=read(B/'verification/load_paths.json');h=read(B/'harness/routing_plan.json')
    channels=read(B/'harness/wire_channels.json')['rows'];ex=read(B/'verification/export_formats.json')
    daily=read(B/'verification/daily_motion.json');edge=read(B/'verification/edge_paths.json')
    mass=read(B/'verification/gravity_demand.json')['printed_geometry_solid_equivalent_g']['O23G']
    before=read(FHISTORY/'verification/gravity_demand.json')['printed_geometry_solid_equivalent_g']['O23F']
    writecsv(B/'连接杆数量表.csv',['部位','连接对象','连接杆数','上限'],[dict(部位=NAMES.get(r['part'].split('/',1)[1],r['part']),连接对象=k,连接杆数=v,上限=3) for r in counts['rows'] for k,v in r['counts'].items()])
    writecsv(B/'连接截面筛查.csv',['部位','安装面编号','截面筛查mm2','截面模量代理mm3','说明'],[dict(部位=NAMES.get(r['body'],r['body']),安装面编号=r['land'],截面筛查mm2=round(r['conservative_cut_area_mm2'],2),截面模量代理mm3=round(r['conservative_section_modulus_mm3'],2),说明='几何筛查；不是许用载荷或实测强度') for r in loads['rows']])
    exceptions=[r['part'] for r in s['symmetry'] if not r['all_rods_mirrored']]
    export_note=(f"**{len(ex['rows'])} 件 STL 全部通过封闭性、面朝向、单实体和实际离线切片检查**，同步更新同网格的 3MF。原装配几何未修改，导出网格修整的最大声明表面偏差小于 0.0011 mm。详见 [STL 修复与切片验证](STL_EXPORT_REPAIR.zh-CN.md)。" if ex.get('native_print_slicing_verified') else f"提供 {len(ex['rows'])} 个索引 3MF 评审文件；STL 回读拓扑仍有 {len(ex['stl_failures'])} 件未通过。")
    print_note=('已完成 A1 mini / PLA / 0.4 mm 喷嘴的离线切片验证，包含自动支撑；打印方向和支撑拆除仍需首件试打确认。' if ex.get('native_print_slicing_verified') else '切片和打印层方向尚待验证。')
    content=f'''# O23G 圆整连接与完整落脚

本版针对 O23F 的杆身杂乱凸起、外壁边缘连接不足、小臂球状支撑及连接不对称进行全身复查。实际装配高度 **{g['height_mm']:.2f} mm**；UE 对应骨段、实际髋轴中心、测量轴、五指握拳和背盒配置继续沿用。没有新增五金型号。

## 本轮修改

- 新连接直接生成完整圆截面，直段为圆柱，避让段为平滑圆截面弯杆；不再与旧骨架材料相交裁切，不再叠加球形节点。
- 外壁端落在完整内壁上，使用平滑加宽底座；端部探测体至少 98% 埋入底座，底座与外壁的有效贴合盘至少 96% 位于完整壁体内。避开开口边缘的半悬空连接。
- 清除旧接口保护范围中混入的截断杆和碎片。保留区按原关节安装结构及固定配合件复核；没有扩大孔位来掩盖干涉。
- 小臂删去原有球状鼓包；薄弱的近肘端改用两条圆杆分担受力。骨盆左右髋端各两条承力连接。每个结构件与相邻单个关节或完整背盒最多 **{counts['maximum_rods_per_adjacent_component']} 根**连接，未超过三根上限。
- 所有外壁保持左右镜像。大腿、上臂、小臂、脚掌及锁骨的主连接镜像布置；骨盆左右髋支路也镜像。头、腰、骨盆的腰接口，以及肘、小腿、脚趾的部分连接需适配偏置机构，仍有差异，**不宣称整件及所有内部连接完全镜像**。详细例外：`{', '.join(exceptions)}`。

![实际 O23G 装配](images/three_quarter.png)

## 实际几何检查

- 24 个结构件均为单个闭合实体；全部已记录的圆杆截面完整保留；外壁未新增细碎破口。
- {len(loads['rows'])} 个安装区域完成 1 mm 体素最小割筛查；最小几何截面指标 **{min(r['conservative_cut_area_mm2'] for r in loads['rows']):.2f} mm²**。该指标已按网格方向折减，用于查找细颈，不能当作材料许用应力或承载认证。
- **{daily['pose_count']} 个日常姿态 + {edge['pose_count']} 个过渡姿态**：必须处理的相邻部位干涉为零（体积报告容差 0.05 mm³）。固定配合件另外复核；非相邻接触按已约定规则列为提示。没有通过缩减原动作检查集来获得通过结果。
- 背盒安装工具路径和载板拆出路径已复查；靠近 XIAO 的一颗板螺钉仍需直径 3 mm 的细工具，普通直径 6 mm 工具的失败记录继续保留。
- **{len(h['seats'])} 个真实线材固定座、{len(channels)} 条固定段通道、46 路五芯线束**重新校核。走线不能切坏新的圆杆截面；各活动关节继续保留松弛弧线。

详见 [连接截面筛查](连接截面筛查.csv)、[连接数量表](连接杆数量表.csv)、[完整连接检查](verification/smooth_connections.json)、[布线方案](harness/routing_plan.json)。

## 交付和限制

按建模实体体积换算的全部打印几何 PLA 等效质量为 **{mass:.1f} g**，O23F 为 **{before:.1f} g**；不含五金和电路，不等于切片耗材质量。{export_note}

这是数字工程评审稿。{print_note}实物静载、疲劳、摩擦持姿和线束反复弯折尚未验证，不能据此宣称实物强度已经合格。背部控制板仍为未布线的布局稿。

原 O23F 完整快照保留在 [历史目录](history/O23F_before_smooth_connections_20261021/DESIGN.zh-CN.md)。

几何 SHA-256：`{digest}`。
'''
    (B/'SMOOTH_CONNECTIONS.zh-CN.md').write_text(content,encoding='utf8');(B/'DESIGN.zh-CN.md').write_text(content,encoding='utf8')
    for name in ('CLEAN_SYMMETRIC_WALLS.zh-CN.md','CONTINUOUS_WALLS.zh-CN.md','FINGERS_STRUCTURE_HARNESS.zh-CN.md'):
        (B/name).write_text('# 当前版本 O23G\n\n本轮修正连接杆、旧接口残段和小臂支撑；最新状态见 [O23G 设计说明](SMOOTH_CONNECTIONS.zh-CN.md)。\n',encoding='utf8')
    wire_note=f'''# O23G 布线与试装

本说明对应几何 `{digest}`。固定座位置和预裁长度取自本目录当前 [routing_plan.json](routing_plan.json) 与 [preliminary_cut_list.csv](preliminary_cut_list.csv)。新圆杆和底座截面受保护，不以切槽减薄承力结构来让线材通过。

## 线材和连接

采用 AWG30 细多股软铜线，含绝缘层外径不大于 0.7 mm。46 个传感器各用 5 根独立线直达背板，不把传感器串接。颜色顺序：黑 GND、红 SENSOR_3V45、蓝 CLK、绿 DO、黄 CSN。不能仅凭 AWG 推断柔性和疲劳寿命；供应商的最小弯曲半径需满足本设计 10 mm 的活动弯曲半径。

当前预裁表最长单线 {h['maximum_preliminary_length_mm']} mm，每种颜色合计约 {h['preliminary_active_m_each_color']:.3f} m，五色合计约 {5*h['preliminary_active_m_each_color']:.3f} m；这些数值不含采购和试装损耗。预裁长度包含端接余量，实物试装后再最终截短。

## 固定和活动余量

共 {len(h['seats'])} 个打印固定座及 {len(channels)} 条肢段内部通道。使用名义宽度 2.5 mm 的细扎带穿过固定座横孔，轻束线材，不压伤绝缘层。线材沿固定座及通道走线；小臂到肘、肩、腰、髋、膝、踝等活动连接之间保留松弛弧线，不能拉直或跨轴拉紧。各段分配长度记录在 routing_plan.json 的 links 内。

固定座横孔、承压顶面、线束预留空间及通道已经按实际最终几何校核。活动线圈按 {h['pose_samples']} 个姿态的最大端点间距加余量估算；这不等于完成了柔性线缆碰撞或疲劳仿真。首件要逐关节缓慢摆动，确认无夹线、磨线和拉扯，再固定线束。长线信号完整性尚待实物电测；控制板仍为未布线的布局稿。
'''
    (B/'harness/布线与试装说明.zh-CN.md').write_text(wire_note,encoding='utf8')
    delivery=read(B/'DELIVERY.json');delivery['O23G_changes']=dict(full_round_struts=True,spherical_support_nodes_removed=True,
        rods=len(s['rods']),maximum_rods_per_adjacent_component=counts['maximum_rods_per_adjacent_component'],symmetry_exceptions=exceptions,
        physical_strength_verified=False,geometry_sha256=digest);put(B/'DELIVERY.json',delivery)
    print('NOTES G',mass,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--publish',action='store_true');ap.add_argument('--notes',action='store_true');a=ap.parse_args()
    if a.publish:publish()
    if a.notes:notes()
