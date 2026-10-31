"""Publish only checked E meshes, then bind engineering notes to those meshes."""
from build_revo23_wire_seats import *
from package_revo23 import NAMES,writecsv
from audit_revo23_load_paths import screen

REVISION='O23E-fingers-structure-harness-20261021'


def publish():
    digest=sha(EROOT/'assembly.npz');stage=read(EROOT/'staging.json')
    assert stage['geometry_sha256']==digest
    for key,h in stage['candidate_files'].items():
        assert sha(EROOT/(key.replace('/','__')+'.npz'))==h,('changed candidate',key)
    for file in ('daily_motion.json','edge_motion.json','fixed_interfaces.json'):
        r=read(EROOT/file)
        assert r['geometry_sha256']==digest and r['passed'],('failed or stale',file)
        if 'motion' in file:assert r['complete_policy'] and not r['trial']
    wire=read(EROOT/'wire_fixture_verification.json');assert wire['passed']
    for key,h in wire['candidate_mesh_hashes'].items():
        assert sha(EROOT/(key.replace('/','__')+'.npz'))==h,('stale wire audit',key)
    assert read(EROOT/'harness/routing_plan.json')['capacity_passed']
    assert sha(B/'profiles/device_profile.json')==sha(DHISTORY/'profiles/device_profile.json')
    shutil.copy2(EROOT/'assembly.npz',B/'assembly.npz')
    shutil.copy2(EROOT/'assembly.json',B/'assembly.json')
    cfg=read(CFG);cfg['revision']=REVISION
    cfg['notes']=[s for s in cfg['notes'] if not s.startswith('O23E:')]
    cfg['notes'].append('O23E: five fixed fingers, reinforced load paths and integral internal wire saddles; see current geometry-bound reports.')
    put(CFG,cfg)
    for source,dest in [('daily_motion.json','daily_motion.json'),('edge_motion.json','edge_paths.json')]:
        shutil.copy2(EROOT/source,B/'verification'/dest)
    out=B/'harness';out.mkdir(exist_ok=True)
    for source,dest in [(EROOT/'harness/routing_plan.json','routing_plan.json'),
                        (EROOT/'wire_seats.json','wire_seats.json'),
                        (EROOT/'wire_channels.json','wire_channels.json'),
                        (EROOT/'wire_fixture_verification.json','wire_fixture_verification.json')]:
        r=read(source);r['geometry_sha256']=digest;put(out/dest,r)
    shutil.copy2(EROOT/'harness/preliminary_cut_list.csv',out/'preliminary_cut_list.csv')
    print('PUBLISHED',digest,flush=True)


def engineering(candidate=False):
    root=EROOT if candidate else B
    parts,p,cfg=load_e();base,_,_=load_d();digest=sha(root/'assembly.npz')
    assert digest==sha(EROOT/'assembly.npz')
    kz=np.load(DHISTORY/'source/retained_interfaces.npz');walls=[];loads=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        s=item['s'];keep=solid(kz[key+'|v'],kz[key+'|f']);skin=local_skin(key,p,cfg)
        path=EROOT/(key.replace('/','__')+'.npz')
        cut=read(EROOT/'load_paths_candidate'/path.with_suffix('.json').name)
        assert cut['candidate_mesh_sha256']==sha(path),('stale load-path audit',key)
        assert cut['rows'] and all(r['connected_voxel_path'] for r in cut['rows']),('disconnected load path',key)
        before=read(EROOT/'load_paths_D'/path.with_suffix('.json').name)
        old={r['land']:r for r in before['rows']}
        for r in cut['rows']:
            previous=old.get(r['land'],{})
            loads.append(dict(part=key,body=item['body'],land=r['land'],
                land_volume_mm3=r['land_volume_mm3'],voxel_pitch_mm=r['voxel_pitch_mm'],
                D_cut_area_mm2=previous.get('conservative_cut_area_mm2'),
                E_cut_area_mm2=r['conservative_cut_area_mm2'],
                E_section_modulus_proxy_mm3=r['conservative_section_modulus_mm3'],
                connected_voxel_path=r['connected_voxel_path'],
                candidate_mesh_sha256=sha(path)))
        intentional=item['body'].startswith('hand_')
        loss=max(0.,(skin-s).volume()) if not intentional else None
        oldloss=max(0.,(skin-base[key]['s']).volume()) if not intentional else None
        row=dict(key=key,component_count=len([c for c in s.decompose() if c.volume()>.001]),
            source_watertight=trimesh.Trimesh(*vf(s),process=False).is_watertight,
            old_radial_skin_loss_mm3=oldloss,E_radial_skin_loss_mm3=loss,
            fingers_intentionally_reshaped=intentional,
            precision_land_missing_mm3=max(0.,(keep-s).volume()),
            D_precision_land_missing_mm3=max(0.,(keep-base[key]['s']).volume()))
        assert row['component_count']==1 and row['source_watertight']
        if not intentional:assert loss<=oldloss+.03,('new outer-wall removal',row)
        assert row['precision_land_missing_mm3']<=row['D_precision_land_missing_mm3']+.03,('precision land removed',row)
        walls.append(row)
    put(root/'verification/load_paths.json',dict(geometry_sha256=digest,rows=loads,
        structure_count=24,connected_paths=len(loads),passed=True,
        method='1 mm six-neighbour voxel max-flow/min-cut. Face area divided by sqrt(3); section modulus is a cut-point proxy. This is a geometric bottleneck screen, not FEA.',
        physical_strength_verified=False,manufacturing_release=False))
    put(root/'verification/continuous_walls.json',dict(geometry_sha256=digest,rows=walls,
        original_radial_skin_preserved_except_intentional_fists=True,
        independent_new_perforations_in_preserved_radial_skin=0,
        manufacturing_release=False))
    writecsv(root/'连接截面筛查.csv',['部位','安装面编号','安装面体积mm3','D截面筛查mm2','E截面筛查mm2','E截面模量代理mm3','说明'],
        [dict(zip(['部位','安装面编号','安装面体积mm3','D截面筛查mm2','E截面筛查mm2','E截面模量代理mm3','说明'],
            [NAMES.get(r['body'],r['body']),r['land'],round(r['land_volume_mm3'],2),
             round(r['D_cut_area_mm2'],2) if r['D_cut_area_mm2'] is not None else '',
             round(r['E_cut_area_mm2'],2),round(r['E_section_modulus_proxy_mm3'],2),'几何筛查，非许用承载力']))
         for r in loads])
    print('ENGINEERING',len(walls),'parts',len(loads),'connected load paths',flush=True)


def notes():
    digest=sha(B/'assembly.npz');g=read(B/'verification/geometry.json')['geometry']
    d=read(B/'DELIVERY.json');load=read(B/'verification/load_paths.json')
    h=read(B/'harness/routing_plan.json');wire=read(B/'harness/wire_fixture_verification.json')
    channels=read(B/'harness/wire_channels.json')['rows'];exports=read(B/'verification/export_formats.json')
    mass=read(B/'verification/gravity_demand.json')['printed_geometry_solid_equivalent_g']
    oldmass=read(DHISTORY/'verification/gravity_demand.json')['printed_geometry_solid_equivalent_g']['O23D']
    daily=read(B/'verification/daily_motion.json');edge=read(B/'verification/edge_paths.json')
    seats=len(h['seats']);minimums=[]
    d['O23E_changes']=dict(fixed_fingers_per_hand=5,integral_wire_seats=seats,
        fixed_internal_channels=len(channels),independent_five_core_sensor_routes=46,
        load_path_screened_landings=len(load['rows']),
        total_printed_solid_equivalent_g=mass['O23E'],
        physical_strength_and_wire_fatigue_verified=False)
    put(B/'DELIVERY.json',d)
    writecsv(B/'harness/辅料清单.csv',['项目','规格','初步用量','建议备料','备注'],
        [dict(项目=label+'导线',规格='AWG30细多股，含绝缘外径≤0.7mm',
              初步用量=f"{h['preliminary_active_m_each_color']:.2f}m",建议备料='35m',
              备注='先采购样线试装；五种颜色独立，非整束总量')
         for label in ('黑','红','蓝','绿','黄')]+[
         dict(项目='扎带',规格='宽2.5mm，穿带段厚度≤1.2mm',初步用量=f'{seats}条',
              建议备料='40条',备注='不得过紧压坏绝缘')])
    for key,land,title in [('frame/thigh_l',1,'左大腿近髋连接'),('frame/thigh_r',1,'右大腿近髋连接'),
                           ('frame/elbow_r',1,'右肘原薄弱连接')]:
        r=next(x for x in load['rows'] if x['part']==key and x['land']==land)
        minimums.append(f"| {title} | {r['D_cut_area_mm2']:.2f} | {r['E_cut_area_mm2']:.2f} |")
    text=f"""# O23E 五指握拳、连接加强与内部布线

本版在已接受的 O23D 外形上优化结构，实际高度 {g['height_mm']:.2f} mm。身体参考点、实际双髋中心、关节轴与角限均沿用已校核的 D 版。本轮没有再改变 D 版的五金配置；新增耗材是软导线和扎带。

按仓库 O22F7 装配修订版“含备件”采购清单核算，整个 O23 方案仍需补 M1.6 螺母 4 个、M1.6 × 6 螺钉 4 个、M2 × 6 自攻螺钉 2 个。完整数量见 [五金变化表](五金变化表.csv)，请按实际已购数量核对。

## 双手

左右手各有四根弯曲手指和一根横扣的拇指，左右拇指方向相反。手指与掌部连成一个打印实体，不增加活动手指或测量通道。掌部采用空腔，腕部精密安装面保留。

![五指握拳的实际 CAD](images/fist_detail.png)

## 全部连接与相邻干涉

24 个身体结构件均为单个封闭实体。原细连接处增加宽连接台、圆角过渡和多条内筋；大腿近髋、肘部及胸肩连接分别进行了截面筛查。加强后按最终实际零件重新修整抬臂避让，避免新材料侵入相邻机构。

胸肩连接的加厚在外观上较明显，尤其是锁骨区域。这里的“原外壁保留”指原人体外壁未被新增孔洞破坏，不表示加强后的胸肩外包络与 D 版完全相同。请以当前整机和单件视图评审外观。

以下数值使用相同的 1 mm 体素最小割方法，表示几何连接的截面筛查结果：

| 连接位置 | O23D / mm² | O23E / mm² |
|---|---:|---:|
{chr(10).join(minimums)}

完整结果见 [全部连接截面表](连接截面筛查.csv)。总计 {len(load['rows'])} 处保留安装面到外壁或另一安装面的路径均连通。体素结果不能直接换算成许用载荷；打印层方向、层间结合、螺钉预紧和材料强度尚需实测。

- {daily['pose_count']} 个日常姿态与 {edge['pose_count']} 个加密过渡姿态：必须处理的相邻穿透记录均为 0，报告容差 0.05 mm³。
- 逐一核对同一刚体内的新结构与五金、磁铁座、PCB 的装配。保留有明确体积上限的自攻螺钉咬合；它们不作为意外穿模。
- 背盒细杆工具方案和 22 步控制板取出检查通过。靠近 XIAO 的螺钉仍需要直径 3 mm 的工具杆，粗杆失败结果保留。
- 非相邻接触保留为提示。离散检查不代表所有任意组合与连续路径都已经验证，也未证明全程 2 mm 间隙。

## 内部线材固定

实际打印几何包含 **{seats} 个扎带固定座**，其中 30 个在身体结构件上，2 个在背盒侧缘入口处。覆盖腕部线路沿前臂、肘、上臂、锁骨、胸部到背盒的路径，以及头部和双腿回路。另有 **{len(channels)} 条连续内部通道**连接长骨段上的两个固定座。身体固定座与内壁连成一体，扎带从座下的贯通槽穿过，不在人体外壁上增加碎孔。

全部固定座的扎带孔、承压顶面及记录的线束包络已按最终保存的模型复查；线束固定空间经过 {wire['pose_count']} 个姿态检查。关节两侧分开固定，中间留松弛弧形线圈，不能用一根绷紧的线跨越关节。柔性线圈的真实形状、挤压与寿命仍需试装。

预览中的“布线固定座与通道”显示真实固定点与内部通道。它不绘制未经验证的柔性线形。

详见 [布线与试装说明](harness/布线与试装说明.zh-CN.md) 和 [46 路初步裁线表](harness/preliminary_cut_list.csv)。

## 重量与制造状态

按建模实体体积及统一 PLA 密度换算，全部打印几何为 **{mass['O23E']:.1f} g**，O23D 对照为 {oldmass:.1f} g，增加 {mass['O23E']-oldmass:.1f} g。这不含五金、PCB 和线材，也不是切片耗材预测。加强件增加的质量会提高摩擦持姿负担，应在首件试装时检查肩、髋和腰的持姿，不能由几何通过直接认定已满足承载。

输出 {len(exports['rows'])} 个保留索引的 3MF 审查件。STL 回读拓扑未通过的件数为 {len(exports['stl_failures'])}，见导出报告；优先使用 3MF 进行受控切片审查。尚未完成切片、实物装配、静载与疲劳验证。

背部 64 × 60 mm 控制板目前仍为布局稿，未布线，不能直接投板。较长传感器线的通信信号完整性也需样线测试。现阶段为数字工程候选，非制造放行包。

几何 SHA-256：`{digest}`。
"""
    (B/'FINGERS_STRUCTURE_HARNESS.zh-CN.md').write_text(text,encoding='utf8')
    guide=f"""# O23E 布线与试装说明

## 导线及辅料

- 每块传感器板 5 根独立导线，共 46 路、230 根回线。接口顺序沿用电路设计：GND 黑、SENSOR_3V45 红、CLK 蓝、DO 绿、CSN 黄；焊接前按连接器编号核对，不能仅凭颜色认针脚。
- 暂定 AWG30 细多股软铜线，**含绝缘外径不超过 0.7 mm**。电阻验收目标不高于 0.4 Ω/m；供应商需要明确反复弯曲适用性。AWG 本身不说明外径或耐弯寿命。
- 设计弯曲半径为 10 mm。所选线材允许的动态弯曲半径必须适合实际线圈；若厂家要求更大半径，先调整线圈位置和长度再装配。
- 2.5 mm 宽小扎带，穿带部分厚度不超过 1.2 mm。{seats} 个固定座，建议备 40 条。缓和收紧，只限制滑动，不压扁绝缘；剪口朝离线束方向。
- 初步裁线合计每色 {h['preliminary_active_m_each_color']:.2f} m，五色共 {h['preliminary_active_m_each_color']*5:.2f} m。按约 20% 试装余量，每色备 35 m；最终以样线实测修订。最长单根初留 {h['maximum_preliminary_length_mm']} mm。

尺寸与绞线结构可参考 Cooner NUF30-4046 / NUF30-2544：厂家目录列为 AWG30 细绞铜线、薄壁 PVC，绝缘外径标称 0.022 英寸，约 0.559 mm，落在本设计 0.7 mm 上限内。目录未给本机构 R10 线圈的寿命结论；采购前仍需确认外径公差、供货与弯曲要求。来源：[Cooner 官方目录，第 10 页](https://www.coonerwire.com/wp-content/uploads/2024/04/cooner_catalog_rev9-8.pdf)。

## 固定及关节余量

1. 从传感小板焊点引出，先留短软线，避免把焊盘当作受力固定点。连接器和焊接端分别编号，与裁线表的传感轴、背板接口和位号一一对应。
2. 手腕的两块传感器板共 10 根线，沿前臂内侧固定座汇入；经过肘和上臂时加入对应传感器支路。肩根固定座按最多 45 根细线核算，不能把所有躯干线塞进一个小座。
3. 长骨段的两个固定点之间走模型给出的通道。转弯处顺着宽圆角走，避开螺钉头、摩擦面、轴孔、磁铁和传感器间隙。
4. 每个活动连接处，在两端固定点之间留自由的 U 形或 S 形余量。初步长度按 522 个姿态中的最大端点距离，再加半圈 R10 弧长及 20 mm 余量估算；这不是已验证的最终线形。
5. 先单独试装一条完整手臂及一条腿，用实线验证屈伸、轴向旋转和联动姿态。全过程不得拉紧焊点、卷入轴座或越过摩擦面；必要时移动松弛圈、增加长度，再定其余线束。
6. 胸部两路分别汇入背盒两侧固定座，再由原有侧面大开口进盒，接对应背板接口。不要把线束夹在后盖接缝中。固定座到背板的连线也是长度估算，不表示线材直穿盒壁；试装时沿侧窗弯入。控制板取出前断开线束；保留插拔操作余量，盖板不得压线。

## 模型中已经检查的内容

- {seats} 个实心连接的固定座、座下贯通扎带孔及其承压顶面。
- {len(channels)} 条内部通道在最终打印实体中保持开放。
- 固定点规定的线束空间与相邻运动件在 522 个姿态中的接触。
- 每个固定点所经过的导线数量不超过其设计容量。

## 试装中仍需确认

柔性线圈、扎带穿入操作、连续弯曲疲劳和最长线路通信尚未完成实测。裁线表标为“试装后裁线”，不要按表直接批量裁齐。优先用最长线路及完整手臂验证，记录实际长度和最紧姿态，再修订所有支路。

数据：[辅料清单](辅料清单.csv)、[固定座及路由](routing_plan.json)、[通道](wire_channels.json)、[实际几何复查](wire_fixture_verification.json)。

本说明与几何 `{digest}` 绑定。
"""
    (B/'harness/布线与试装说明.zh-CN.md').write_text(guide,encoding='utf8')
    overview=f"""# O23E 人形承力骨架

O23E 在已接受的 D 版外形上，增加五指握拳、加强结构连接，并加入实际打印的内部布线固定座。高度 {g['height_mm']:.2f} mm；身体运动学、实际髋中心与 UE 比例沿用 D 版。

![O23E 实际 CAD](images/three_quarter.png)

| 项目 | 当前结果 |
|---|---|
| 身体结构件 | 24 件，全部为单个封闭实体 |
| 手部 | 左右各 5 根固定握拳手指 |
| 日常 / 加密过渡姿态 | {daily['pose_count']} / {edge['pose_count']}，相邻穿透记录为 0 |
| 打印固定座 / 内部通道 | {seats} / {len(channels)} |
| 传感器 / 机械轴 / 模块 | 46 / 46 / {d['joint_modules']} |
| 3MF 审查件 | {len(exports['rows'])} 件 |
| 制造状态 | 数字候选；实物强度、持姿、布线与切片未放行 |

- [本轮五指、连接与布线优化说明](FINGERS_STRUCTURE_HARNESS.zh-CN.md)
- [布线规格及试装顺序](harness/布线与试装说明.zh-CN.md)
- [全部连接截面筛查](连接截面筛查.csv)
- [结构件](结构件清单.csv)、[附件](附件清单.csv)、[五金变化](五金变化表.csv)、[UE 比例](UE比例对照.csv)
- [当前检查入口](verification/README.zh-CN.md)
- [D 版外壁与髋中心设计背景](history/O23D_before_fingers_strength_harness_20261020/CONTINUOUS_WALLS.zh-CN.md)

预览 `preview/index.html` 可切换姿态、选择零件及剖切，勾选“布线固定座与通道”查看真实预留位置。

当前打印几何的 PLA 实体等效为 {mass['O23E']:.1f} g，不含五金、电子和线材。新增质量需要实物持姿验证。控制板仍是未布线布局稿；STL 格式问题以当前导出报告为准，优先用 3MF 审查。

胸肩连接比 D 版明显加厚，是当前加强方案的外观与重量代价；人体参考点和四肢比例没有因此变化。

O22F7 原打印文件未改动。D 版保存在 `history/O23D_before_fingers_strength_harness_20261020/`。E 版候选与脚本位于 `design/reinforced_candidate/` 及设计根目录 `scripts/`，不能用旧 D 版构建命令覆盖当前结果。

几何 SHA-256：`{digest}`。
"""
    (B/'DESIGN.zh-CN.md').write_text(overview,encoding='utf8')
    (B/'CONTINUOUS_WALLS.zh-CN.md').write_text(f"""# O23E 外壁与髋中心

E 版继承 D 版的人体比例和实际髋中心。除有意重塑的左右握拳外，原径向外壁在最终几何差集检查中保持完整，内部固定座没有新增穿过人体外壁的孔。

详见 [当前优化说明](FINGERS_STRUCTURE_HARNESS.zh-CN.md) 和 [外壁实际差集检查](verification/continuous_walls.json)。
前一版的完整设计依据保存在 [O23D 外壁与髋位置说明](history/O23D_before_fingers_strength_harness_20261020/CONTINUOUS_WALLS.zh-CN.md)。

当前几何 `{digest}`。
""",encoding='utf8')
    (B/'先读我.txt').write_text('O23E 五指、连接加强与内部布线数字候选。\n先阅读 DESIGN.zh-CN.md 和 FINGERS_STRUCTURE_HARNESS.zh-CN.md。\n打开 preview/index.html 查看实际几何。\n尚未制造放行；控制板未布线。\n',encoding='utf8')
    (B/'verification/README.zh-CN.md').write_text(f"""# 当前 O23E 检查

当前几何：`{digest}`。

| 文件 | 检查内容 |
|---|---|
| geometry.json | 尺寸、封闭性、连通块、打印包络与身体运动学 |
| daily_motion.json | 408 个日常姿态的全部运动相邻实体 |
| edge_paths.json | 114 个加密过渡姿态 |
| fixed_interfaces.json / fixed_all_interfaces.json | 固定装配配合及原有自攻咬合 |
| magnet_seat_restoration.json | 磁铁托座空腔 |
| load_paths.json | 24 个结构件的几何连接截面筛查；非 FEA |
| continuous_walls.json | 最终实体保留原径向外壁及精密安装面的实际差集 |
| backpack_tool_access.json | 细杆工具与控制板取出 |
| export_formats.json | 3MF 索引保留及 STL 回读 |
| gravity_demand.json | 打印实体体积及静态重力估算 |
| delivery_audit.json | 当前模型、预览、渲染、导出的哈希一致性 |

线束几何报告在 `../harness/wire_fixture_verification.json`。髋中心、锁骨机构和右腕商业板报告按其运动学与源模块哈希绑定；其相关模块未在 E 版重新设计。

中间 trial、partial、progress 文件及旧版本报告不能代替当前报告。重新构建时先执行最终候选检查和 `finish_revo23_e.py --publish`，然后进行公开装配校核、`--engineering`、导出、`--notes`、预览渲染及交付审计。不得只修改报告中的几何哈希。
""",encoding='utf8')
    for source,dest in [('fists_detail.png','fist_detail.png'),('fists_front.png','fist_front.png')]:
        shutil.copy2(EROOT/source,B/'images'/dest)
    print('E NOTES',digest,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--publish',action='store_true')
    ap.add_argument('--engineering',action='store_true')
    ap.add_argument('--candidate',action='store_true')
    ap.add_argument('--notes',action='store_true')
    args=ap.parse_args()
    if args.publish:publish()
    if args.engineering:engineering(args.candidate)
    if args.notes:notes()
