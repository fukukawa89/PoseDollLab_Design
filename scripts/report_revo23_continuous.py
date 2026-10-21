"""Generate review notes from the delivered O23D geometry and actual checks."""
from build_revo23_continuous import *


def main():
    p=read(B/'profiles/device_profile.json');g=read(B/'verification/geometry.json')['geometry']
    motion=read(B/'verification/daily_motion.json');hip=read(B/'verification/hip_centers.json')
    edge=read(B/'verification/edge_paths.json')
    digest=sha(B/'assembly.npz')
    assert motion['geometry_sha256']==digest and not motion['trial'] and motion['complete_policy'] and motion['passed']
    assert edge['geometry_sha256']==digest and edge['passed']
    rows=[read(f) for f in DROOT.glob('frame__*.json')]
    assert len(rows)==24 and all(r.get('validated_profile_sha256',r['construction_profile_sha256'])==profile_signature(p) for r in rows)
    rise=p['o23_design']['upper_torso_raise_mm']
    centers='\n'.join(f"| {'左' if r['joint'].endswith('_l') else '右'}髋 | "
        f"{r['old_physical_center_mm'][1]:.3f} | {r['actual_center_mm'][1]:.3f} | {r['error_mm']:.9f} |"
        for r in hip['hip_centers'])
    required=len(motion['blocking_contacts']);warnings=len(motion['nonadjacent_advisory'])
    text=f"""# O23D 连续外壁与髋关节对齐

这是可审查的数字设计候选，尚未完成实物试装、承载和打印验证。

## 本次实际改变

- 骨盆内两套髋关节各向内移动 22.4 mm。实际旋转中心与按 UE Quinn 比例放置的股骨起点重合，双髋中心距从 {hip['old_center_spacing_mm']:.3f} mm 改为 {hip['physical_center_spacing_mm']:.3f} mm。
- 腿长、膝踝参考点及各关节测量轴方向保留；不再只靠软件参考点掩盖实际髋位置偏移。
- 胸部和其上方所有部件整体抬高 {rise:g} mm，为躯干关节及传感器留空间。四肢骨长、肩宽不变；躯干长度有明确偏离，不声称全身严格等比例。
- 本版 A 站姿实体高度为 {g['height_mm']:.2f} mm，低于 800 mm。
- 24 个承力骨段重建连续外壁。每处避让沿对应关节连到外壁端部，外壁不再由许多独立障碍物打孔。内部安装座、螺孔、检修空间仍有必要的开口。
- 保留背部控制盒，背盒与胸部一起抬高；背盒下方安装座增加短连接筋。
- 修正右腕打印件的左右方向。原商业传感器板采用刚体翻转安装；不要求制造镜像电路板。
- 前臂旋转模块向肘侧沿原轴移 8 mm，右侧安装朝向转过 180°；通过两端相反变换保持身体参考点、骨长及运动关系。背盒安装座缩短前伸部分，保留螺母口袋与承压面。
- 两侧锁骨前伸模块各绕原轴换向 90°，使传感器板避开抬臂路径；安装座一并重做，模块位置和身体运动学保持不变。跨模块静态装配也单独校核。
- 安装座边角、右肘内部连接筋和右前臂安装座尾部增加局部避让。这些修整没有削穿径向外壁，主轴座与完整腕部安装面保留；最终壁厚及连接筋强度仍需切片与实物检查。
- 左右肘与胸部的磁铁托座按原 F7 对应坐标恢复安装空腔，只移除侵入原空腔的新材料；磁铁、螺钉和传感器的几何与位置不变。

坐标单位为 mm，Y 为左右方向；误差为三维距离：

| 部位 | 旧实际中心 Y | 新实际中心 Y | 相对 UE 比例目标误差 |
|---|---:|---:|---:|
{centers}

## 检查规则及结果

按用户确定的标准，日常动作中的相邻身体部位碰撞必须处理；非相邻部位的接触作为摆姿提示。极端原始轴角组合保留历史报告，不作为日常使用合格的判断依据。

- 日常姿态：{motion['pose_count']} 个，包括坐姿、前伸、抱持、浅蹲、跨步与单关节分段扫描。
- 必须处理的相邻碰撞记录：**{required}**，涉及 {motion['blocking_pose_count']} 个姿态。
- 非相邻部位提示：{warnings} 条，涉及 {motion['advisory_pose_count']} 个姿态。
- 实际双髋与腰部模块装配检查：{hip['pose_count']} 个姿态，跨模块碰撞 {len(hip['cross_module_contacts'])} 条。
- 易接触区域另加 {edge['pose_count']} 个过渡姿态，原始轴间隔不超过 1°；全部运动相邻实体检查发现 {len(edge['blocking_contacts'])} 条需处理记录。
- 独立外壁断孔：构造上为 0；这指新生成的径向外壁，不包括必要的螺孔和旧安装面。
- 有效承力骨段：{sum(r['component_count']==1 and r['source_watertight'] for r in rows)} / 24。

肩部部分日常姿态包含小幅锁骨联动，仍达到指定的上臂朝向；没有把原始关节极限缩小以绕过碰撞。检查覆盖定义好的离散姿态，不能替代所有中间姿态、所有组合和真实线束的验证。

实体相交采用 0.05 mm³ 的报告容差。尚未证明任意运动路径都具有 2 mm 的最小间隙。

## 文件与制造状态

- `assembly.npz`、`profiles/device_profile.json` 是本版实际几何与运动学。
- `verification/daily_motion.json` 是实际相邻实体检查，`verification/hip_centers.json` 是实际髋位置与装配检查。
- `design/continuous_candidate/` 保存每个骨段的边界、避让来源和功能面保留记录。
- `review_3mf/` 用于审查打印件；STL 与 3MF 的重新导入检查应以当前导出报告为准。
- 64 × 60 mm 控制板目前完成布局，尚未布线，不能直接投板。
- 重量数据为建模实体体积换算值，不是切片耗材或实测重量。保持姿态、强度、线束弯曲、工具操作及传感器零位/方向仍需实物验证。
- O22F7 和 O23C 原稿保持可追溯，旧 C 版在 `history/O23C_before_continuous_walls_20261020/`。

几何 SHA-256：`{digest}`。
"""
    (B/'CONTINUOUS_WALLS.zh-CN.md').write_text(text,encoding='utf8')
    delivery=read(B/'DELIVERY.json')
    tools=read(B/'verification/backpack_tool_access.json')
    board=read(B/'verification/right_wrist_boards.json')
    exports=read(B/'verification/export_formats.json')
    main=f"""# O23D 人形承力骨架

O23D 是在 O22F7 关节与测量系统基础上重做的数字设计候选。外壁承担结构作用；关节、工具和维修开口保留。实际尺寸、检查结果和三维预览使用同一份装配几何。

![实际 CAD 三维视图](images/three_quarter.png)

## 当前结果

| 项目 | 本版结果 |
|---|---|
| A 站姿实体高度 | {g['height_mm']:.2f} mm |
| 主要承力结构件 | 24 件，{sum(r['component_count']==1 and r['source_watertight'] for r in rows)} 件为单个封闭实体 |
| 原始机械轴 / 关节模块 | {delivery['raw_channels']} / {delivery['joint_modules']} |
| 实际髋中心距 | {hip['physical_center_spacing_mm']:.3f} mm，与 UE Quinn 等比例骨骼坐标一致 |
| 相对旧版每侧髋内移 | 22.4 mm |
| 上半身整体抬高 | {rise:g} mm；四肢骨长与肩宽不变 |
| 日常姿态检查 | {motion['pose_count']} 个，必须处理的相邻碰撞 {required} 条 |
| 额外过渡姿态检查 | {edge['pose_count']} 个，相邻碰撞 {len(edge['blocking_contacts'])} 条 |
| 非相邻接触 | {warnings} 条提示，允许通过调整摆姿避开 |
| 背盒工具与板件取出 | 细杆工具方案 {'通过' if tools['slim_tool_plan_passed'] else '未通过'}；板件取出 {'通过' if tools['pcb_removal']['passed'] else '未通过'} |
| 右腕商业传感器板 | {'通过' if board['passed'] else '未通过'}所检角度下的实体装配检查 |
| 3MF 几何审查文件 | {len(exports['rows'])} 件；逐项保存源顶点索引 |
| STL 焊接后拓扑未通过 | {len(exports['stl_failures'])} 件，具体件号见导出报告 |
| 制造状态 | 尚未切片验证、实物试装或强度放行 |

腰部的实际轴心比身体参考点高 8 mm，为居中的两套髋机构让位。前臂旋转模块沿各自轴线向肘侧移 8 mm，右侧座绕轴转 180°；这些前臂改动不改变身体参考点和骨长。原测量通道顺序、原始角限和身体旋转关系通过独立数值核对。

两侧锁骨前伸模块绕原轴换向 90°，胸部和锁骨连接件按新安装方向重建。此改动避开抬臂过程中的传感器板接触；原肩关节位置、肩宽及身体姿态映射保持不变。

## 使用与审查

- 打开 `preview/index.html` 查看实际可旋转模型；可切换坐姿、前伸、托举、浅蹲、迈步，以及单个结构件。
- [本轮外壁与髋位置说明](CONTINUOUS_WALLS.zh-CN.md)
- [UE 比例与实际髋中心对照](UE比例对照.csv)
- [结构件清单](结构件清单.csv) / [附件与右腕打印件](附件清单.csv)
- [与已购 O22F7 五金对照](五金变化表.csv)
- [日常动作逐零件检查](verification/daily_motion.json)
- [易接触区域的加密过渡检查](verification/edge_paths.json)
- [真实髋中心与跨模块装配检查](verification/hip_centers.json)
- [锁骨模块静态装配检查](verification/collar_static_packing.json)
- [新连接件与固定零件配合检查](verification/fixed_interfaces.json)
- [全部新结构件与 F7 固定配合总核对](verification/fixed_all_interfaces.json)
- [尺寸、网格与运动学检查](verification/geometry.json)
- [STL 与 3MF 导出检查](verification/export_formats.json)

## 外形与装配

头部保留简单头颅轮廓，手部为握拳。各骨段的径向外壁没有独立碎孔：避让口延伸至相应关节端部，剩余外壁为连续面。螺孔、传感器座和螺母装入口属于必要功能细节。胸肩和腰部仍有较大的机构开口，上臂、前臂的外壁也保留关节侧缺口；本版尚未形成完整包覆的人体外形，实际形状以三维预览为准。

背部保留 74 × 70 × 34.2 mm 控制盒及四颗 M3 × 8 固定螺钉。缩短安装座向前伸出的多余材料，保留螺母口袋和承压面。控制板拆出前需要打开后盖、卸下板件螺钉并断开线束。靠近 XIAO 排针的一颗板件螺钉需要所检直径 3 mm 的细杆工具；直径 6 mm 的失败结果仍保留。工具检查不含手柄和人手。

商业传感器板不做镜像制造，右腕通过刚体翻转安装。组装后需校准传感器零位和方向。

## 尚未完成的制造验证

本版完成的是记录中的离散实体检查，并未证明所有中间姿态和任意关节组合。真实线束、摩擦持姿、静载、疲劳、壁厚切片、支撑拆除与实物公差仍需验证。建模体积换算的 PLA 重量不能作为切片耗材或实测重量。

64 × 60 mm 控制电路板已布局，尚未布线，不能直接投板。3MF 是带候选摆放方向的几何文件，不含打印机、材料、支撑或切片参数。STL 的顶点量化问题按实际回读结果列出，不作为已可打印文件。

O22F7 原打印包没有修改。旧 O23C 与失败的中间试验保留在 `history/` 和带版本名的验证文件中；只有本页及 `DELIVERY.json` 所绑定的几何代表当前交付。

几何 SHA-256：`{digest}`。
"""
    (B/'DESIGN.zh-CN.md').write_text(main,encoding='utf8')
    (B/'先读我.txt').write_text('O23D 连续外壁与居中髋关节数字设计候选。\n先阅读 DESIGN.zh-CN.md，再打开 preview/index.html 查看实际 CAD。\n实际相邻碰撞、文件格式和制造状态以当前 verification 与 DELIVERY.json 为准。\nO22F7 原打印包保持不变。\n',encoding='utf8')
    (B/'verification/README.zh-CN.md').write_text(f"""# 当前 O23D 检查入口

当前装配几何 SHA-256：`{digest}`。

| 文件 | 用途 |
|---|---|
| geometry.json | 当前尺寸、连通性、网格及运动学 |
| daily_motion.json | {motion['pose_count']} 个既定日常姿态，检查全部运动相邻实体 |
| edge_paths.json | {edge['pose_count']} 个过渡姿态，检查全部运动相邻实体 |
| hip_centers.json | 与原始 UE Quinn 数据比较实际髋中心，并检查双髋及腰模块 |
| collar_static_packing.json | 换向后的锁骨与其它固定模块之间的装配空间 |
| fixed_interfaces.json | 五个重建胸肩结构件与固定零件的配合，原有配合重叠逐项保留 |
| fixed_all_interfaces.json | 全部新结构件、右腕与背盒相对原 F7 固定配合的总核对 |
| right_wrist_boards.json | 原商业传感器板的实体配合 |
| backpack_tool_access.json | 背盒工具和板件取出通路；保留粗工具失败结果 |
| export_formats.json | 3MF 序列化及 STL 回读结果 |
| gravity_demand.json | 打印材料实体体积模型的静态重力估算 |

其余带版本名、trial、partial、progress 或旧 motion_full/quick 的文件是中间诊断，
不能替代上述当前报告。几何相关结果必须与当前 assembly.npz 的 SHA-256 相同。
运动学与单独机构检查同时核对各自记录的 profile 和模块来源。

几何候选保存在 design/continuous_candidate/*.npz，输入在其 source/ 子目录。
从 design/ 项目根目录运行 scripts/build_revo23_continuous.py --apply 可重新组装已保存候选；
修改输入或生成新几何后，必须重新运行 verify_revo23.py --geometry-only、
verify_revo23_daily.py 和 check_revo23_edge_paths.py，再更新导出、预览和说明。
重建脚本可能重新生成连接筋；没有重新检查的几何不能继承旧报告。

本轮仅完成数字设计评审，交付状态 manufacturing_release 保持 false。
""",encoding='utf8')
    put(B/'verification/continuous_walls.json',dict(geometry_sha256=digest,
        rows=[{k:r[k] for k in ('key','builder_id','component_count','source_watertight',
            'angular_segments_remaining','isolated_holes_in_radial_wall','retained_interface_loss_mm3')} for r in rows],
        radial_skin_punctures=0,daily_required_contact_records=required,
        transition_pose_count=edge['pose_count'],transition_required_contact_records=len(edge['blocking_contacts']),
        physical_hip_center_maximum_error_mm=max(r['error_mm'] for r in hip['hip_centers']),
        manufacturing_release=False))
    print('O23D NOTES',len(rows),required,flush=True)


if __name__=='__main__':main()
