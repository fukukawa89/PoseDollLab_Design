"""Geometry-bound O23C handoff with explicit failed and unverified gates."""
from package_revo23 import *


def main():
    digest=sha(B/'assembly.npz');d=read(B/'DELIVERY.json');g=read(B/'verification/geometry.json')
    s=read(B/'verification/review_summary.json');m=read(B/'verification/motion_full.json')
    e=read(B/'electronics/carrier/placement.json');a=read(B/'verification/backpack_tool_access.json')
    config=read(B/'design/compact_revision.json');load=read(B/'verification/gravity_demand.json')
    assert d['source_geometry_sha256']==digest
    assert all(x['geometry_sha256']==digest for x in(g,s,m,a,load))
    assert e['pcb_sha256']==sha(B/'electronics/carrier/PoseDoll_O23C_SSI_Carrier.kicad_pcb')==config['pcb_sha256']
    cfg=read(CFG);assert cfg['user_controller_pcb_not_manufactured']
    ratios=read(B/'DELIVERY.json')['proportions'];parts=load_current();p=read(B/'profiles/device_profile.json')
    F=frames(p,p['neutral_raw_deg']);bb=np.array([move(v['s'],F[v['token']]).bounding_box() for k,v in parts.items() if k.startswith('o22/')])
    bmin=bb[:,:3].min(0);bmax=bb[:,3:].max(0)
    C=np.array(config['controller_frame_neutral_mm']);armspan=[]
    for side in ('l','r'):
        jj=[next(j for j in p['joints'] if j['id']=='clavicle_'+side+'.'+name) for name in ('protract','elevate')]
        centers=[(F['f:'+j['parent']]@np.array(j['parent_to_mount_mm']))[:3,3] for j in jj]
        armspan.append(dict(side=side,centres_mm=centers,spacing_mm=float(np.linalg.norm(centers[1]-centers[0]))))
    before=read(B/'history/O23B2_long_support_experiment_20261020/verification/backpack_revision.json')
    contacts=[h for h in m['new_or_increased_contacts'] if any(k.startswith('o22/') for k in h['pair']) and not h['same_rigid_owner']]
    wrist_limits={k:v for k,v in p['raw_limits_deg'].items() if k.startswith('hand_')}
    summary=dict(revision=REV,geometry_sha256=digest,pcb_sha256=e['pcb_sha256'],user_controller_pcb_not_manufactured=True,
        box_body_mm=config['case_body_mm'],whole_pack_world_bounds_mm=[bmin,bmax],
        old_B2_furthest_back_x_mm=-230,new_pack_furthest_back_x_mm=float(bmin[0]),
        pcb_area_reduction_percent=(1-64*60/(80*94))*100,clavicle_axes=armspan,
        backpack_contacts=len(contacts),backpack_affected_poses=sorted({h['pose'] for h in contacts}),
        kinematics=g['kinematics'],manufacturing_release=False,pcb_routed=False,
        unresolved_wrist_note='Ankle-family geometry supplies the intersecting wrist axes. Matching output orientation does not prove old hinge travel; inherited stops and sensor envelopes still require redesign/qualification.',wrist_raw_limits_deg=wrist_limits)
    put(B/'verification/compact_revision.json',summary)
    config['final_geometry_sha256']=digest;put(B/'design/compact_revision.json',config)
    counts=s['basic_pose_counts'];mass=load['printed_geometry_solid_equivalent_g']
    pose_names={'A_STAND_35':'A 站姿','N_NEUTRAL':'双臂贴身零位','left_elbow':'左肘动作','asymmetric':'非对称动作','right_forearm':'右前臂扭转'}
    counts_text='；'.join(f'{pose_names.get(k,k)} {v} 条' for k,v in counts.items())
    lines=['# O23C：短锁骨与紧凑背盒','',
      '用户已确认控制板尚未制作。本轮保留背盒，重新排布电路板，并缩短胸肩机构的连接距离。B2 长悬臂方案保存在 history，作为已放弃的避让试验。','',
      '| 项目 | 当前实体／检查 |','|---|---|',
      f'| 人偶 A 站姿高度 | {d["height_mm"]:.1f} mm |',
      '| 主体 | 24 个一体化人形承力结构件，握拳、简化头部，关节附近开放 |',
      '| 控制板 | 64 × 60 × 1.6 mm，双面元件，四层板；原板 80 × 94 mm |',
      '| 背盒主体 | 74 × 70 × 34.2 mm；左右安装耳另计，总外宽约 90 mm |',
      f'| 最后方位置（中立坐标） | X = {bmin[0]:.1f} mm；B2 为 −230 mm |',
      f'| 锁骨两轴间距 | {armspan[0]["spacing_mm"]:.1f} mm，旧版约 107.3 mm |',
      '| 固定与检修 | 四组 M3×8／M3 螺母固定在胸廓；四颗 M2×6 自攻固定 PCB，四颗同规格自攻固定盖板 |',
      f'| 基础姿态新增接触 | {counts_text} |',
      f'| 扩展检查 | {m["pose_count"]} 个离散姿态，{len(m["new_or_increased_contacts"])} 条新增／加重记录 |',
      f'| 背盒相关运动接触 | {len(contacts)} 条，涉及 {len(summary["backpack_affected_poses"])} 个姿态 |','',
      '## 控制板的实际完成度','',
      '原生 KiCad PCB 与原理图已生成，全部焊盘网络与原 O22 板一致，46 个 SH 5P 传感器接口编号和针序保留。A 组 14 个接口位于正面，B／C 两组共 32 个接口位于反面。板面积减少 48.9%。',
      f'原理图 ERC：{e["checks"]["erc"]["violations"]} 项；PCB 布局 DRC：{e["checks"]["drc"]["violations"]} 项，另有 {e["checks"]["drc"]["unconnected"]} 条未连接。**尚未布线，不可制板。** 原供电值与网络保留；XIAO J2.7 仍悬空，不与 J3 外部 5 V 相连。',
      '双面装配需要先卸盖、断开线束、松开四颗 PCB 螺丝，再向后取出板，才能维护内侧接口。反面接口与安装柱已按实际封装布局检查。插头、线束弯曲和手部操作空间仍需实物确认。','',
      '## 身材与映射','',
      '主要骨段长度以及中立肩髋宽维持上一轮 Quinn 比例；手腕中心继续按 UE 肘腕比例设置。34 组数值检查中，保留骨段朝向与原映射一致。锁骨轴位置改变后，耸肩、前伸时肩中心的平移路径也改变；不能把它描述成全部运动学完全不变。',
      '运动学配置仅保存在 O23 profiles 中，未替换软件当前配置。原始通道顺序、零值和角度表仍保留；角度表不等于实体全范围无碰撞证明。','',
      '## 不能忽略的未完成项','',
      '1. 完整运动检查仍存在干涉，见逐零件对报告；不能仅凭 A 站姿发布整机。',
      '2. 当前交叉轴腕部借用脚踝家族接口，其止挡和传感器体积不代表已满足原腕部铰链的全部行程；需要进一步重做并验证。',
      f'3. STL 量化并焊接后的封闭性失败件数为 {len(d["stl_topology_failed_ids"])}。3MF 逐顶点／索引读回一致，只适合几何评审，尚未切片放行。',
      '4. 控制板重新布线、供电压降与散热、线束、持姿、强度、疲劳和装配实测尚未完成。','',
      f'所有已建模打印材料的实心等效量为 {mass["O23C"]:.1f} g，O22F7 为 {mass["O22F7"]:.1f} g。这不是切片耗材或实测重量，也未包含五金、电路和线束。','',
      f'全部使用直径 6 mm 工具杆的检查：{"通过" if a["passed"] else "未通过"}；PCB 靠近 XIAO 的 0 号螺丝改用直径 3 mm 杆，其余保持 6 mm 的明确工具方案：{"通过" if a["slim_tool_plan_passed"] else "未通过"}。真实刀头还须与所购自攻螺丝匹配。带元件 PCB 的离散取出路径：{"通过" if a["pcb_removal"]["passed"] else "未通过"}。这些检查不包含真实手柄和柔性线束。','',
      f'当前模型 SHA-256：`{digest}`。所有本轮交付检查必须与该哈希一致。','',
      '[三维人偶预览](../preview/index.html) · [控制板布局](../electronics/carrier/index.html) · [评审结果](../verification/评审结果.zh-CN.md) · [五金变化表](../五金变化表.csv)','']
    (B/'design/COMPACT_REVISION.zh-CN.md').write_text('\n'.join(lines),encoding='utf8')
    (B/'design/BACKPACK_REVISION.zh-CN.md').write_text('# 背盒版本说明\n\n当前版本为 [O23C 短锁骨与紧凑背盒](COMPACT_REVISION.zh-CN.md)。B2 长支架试验保存在 `../history/O23B2_long_support_experiment_20261020/`，不作为最终外形方案。\n',encoding='utf8')
    entry=['# O23C 人形承力骨架：当前设计入口','',
      '**当前是实体设计与控制板布局评审稿，尚不能整套打印或制板。**','',
      f'人偶 A 站姿高 {d["height_mm"]:.1f} mm。胸、腰、骨盆、四肢和握拳采用承力外壁；胸肩重新布置，背盒直接固定在胸廓上。用户已确认控制板尚未制作，因此采用 64 × 60 mm 的新双面布局，原电气网络与 46 路接口保留。','',
      '- [打开完整三维预览](preview/index.html)：五个姿态、正侧背视图、剖切、单件 3MF 入口。',
      '- [查看本轮设计与限制](design/COMPACT_REVISION.zh-CN.md)：胸肩、背盒、PCB、检修和未完成项。',
      '- [查看控制板布局](electronics/carrier/index.html)：正反面封装、原生 KiCad 文件与检查记录。',
      '- [查看数字评审结果](verification/评审结果.zh-CN.md)、[五金变化表](五金变化表.csv)、[UE 比例对照](UE比例对照.csv)。',
      '- [Blender 实体装配](O23C_assembly.blend)、[结构件清单](结构件清单.csv)、[背盒附件](附件清单.csv)。','',
      f'当前五姿态新增／加重接触记录：{counts_text}。扩展检查 {m["pose_count"]} 姿态仍有 {len(m["new_or_increased_contacts"])} 条记录；数量是零件对与姿态组合，不代表运动损失比例。','',
      '腕部贴身空间、腕部借用机构的实际行程、部分胸肩及复合极限动作仍需改进。主要结构 STL 的拓扑问题尚未全部解决。3MF 仅验证几何序列化一致，不等于打印项目。控制板还没有布线。','',
      'O22F7 输入与软件当前配置均未修改。旧 B2 长支架试验以及其导出件位于 history/O23B2_long_support_experiment_20261020。重建过程见 ../../cad/revO23/README_O23C.md。','',
      f'本轮交付几何哈希：`{digest}`。','']
    (B/'DESIGN.zh-CN.md').write_text('\n'.join(entry),encoding='utf8')
    nextsteps=['# O23C 后续工程交接','',
      '用户已确认：人体比例优先，允许重做腕部；保留背盒，允许增加后方厚度；控制板尚未制作。无需重复询问这些条件。','',
      '本轮已完成可评审的短胸肩结构、紧凑双面 PCB 布局、直接背盒及检修路径模型。当前源装配与检查哈希见上级 DESIGN。B2 长支架作为已放弃试验保留。','',
      '后续重点按实际失败记录推进：','',
      '1. 重做腕部体积与止挡。现腕部的脚踝家族几何不能凭朝向一致就宣称继承旧铰链行程；检查已禁止用越界的脚踝基线来豁免接触。',
      '2. 按逐对报告处理双臂贴身、锁骨及极限组合动作；原角限表不等于已有无碰撞工作空间。',
      '3. 继续去除四肢外侧继承的非功能曲折跨度，将承力路径收进人体外壁；保留轴座、预紧和磁测关系。',
      '4. 从精确参数或精确功能几何重建剩余网格缝合问题；不要让自动修复改坏轴承、螺母和传感器配合面。',
      '5. 完成新板布线、铺铜、压降/热与信号检查，再导出制造资料。保留 46 路 SSI 针序和 XIAO USB 供电隔离关系。',
      '6. 选定与已购自攻螺丝相配的细杆刀头，结合实际插头/线束检查背盒；再进行代表件切片、装配和持姿测试。','',
      '不要将当前设计标为制造放行；不要用隐藏碰撞件、缩小全部角限或删除断开的功能区来获得通过。','']
    (B/'design/NEXT_STEPS.zh-CN.md').write_text('\n'.join(nextsteps),encoding='utf8')
    d['compact_revision_report']='design/COMPACT_REVISION.zh-CN.md';d['pcb_layout_only']=True;d['user_controller_pcb_not_manufactured']=True;put(B/'DELIVERY.json',d)
    print('COMPACT REPORT',digest,'backpack contacts',len(contacts),flush=True)


if __name__=='__main__':main()
