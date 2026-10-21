"""Readable, geometry-bound acceptance report; do not turn sampled checks into a release."""
from package_revo23 import *

def main():
    g=read(B/'verification/geometry.json');m=read(B/'verification/motion_full.json')
    load=read(B/'verification/gravity_demand.json');parts=load_current();p=read(B/'profiles/device_profile.json')
    exported=read(B/'verification/export_formats.json') if (B/'verification/export_formats.json').exists()else None
    tool=read(B/'verification/backpack_tool_access.json') if (B/'verification/backpack_tool_access.json').exists()else None
    digest=sha(B/'assembly.npz')
    assert all(r['geometry_sha256']==digest for r in (g,m,load))
    hits=m['new_or_increased_contacts'];pose_count=Counter(x['pose']for x in hits)
    backpack=[x for x in hits if any(k.startswith('o22/')for k in x['pair'])and not x['same_rigid_owner']]
    trunk=[x for x in backpack if x['pose'].startswith(('waist/','chest/'))]
    adjacency={}
    joints={j['id']:j for j in p['joints']}
    for j in p['joints']:
        adjacency.setdefault(j['parent'],set()).add(j['child']);adjacency.setdefault(j['child'],set()).add(j['parent'])
    def bodies(key):
        t=parts[key]['token'].split(':')
        return {t[1]}if t[0]=='f'else {joints[t[1]]['parent'],joints[t[1]]['child']}
    def category(h):
        a,b=map(bodies,h['pair'])
        if a&b:return '同骨段或同一关节附近'
        if any(adjacency.get(k,set())&b for k in a):return '相邻骨段'
        return '非相邻身体部位'
    regions=Counter(category(h)for h in hits)
    pair_stats={}
    for h in hits:
        pair=tuple(sorted(h['pair']));s=pair_stats.setdefault(pair,dict(pair=list(pair),poses=set(),max_overlap_mm3=0.))
        s['poses'].add(h['pose']);s['max_overlap_mm3']=max(s['max_overlap_mm3'],h['overlap_mm3'])
    most=sorted(pair_stats.values(),key=lambda r:(-len(r['poses']),-r['max_overlap_mm3']))[:20]
    for r in most:r['poses']=sorted(r['poses'])
    summary=dict(geometry_sha256=digest,full_pose_count=m['pose_count'],
        poses_with_new_contacts=len(pose_count),new_contact_records=len(hits),
        basic_pose_counts={name:pose_count[name]for name in cases(p,'quick')},
        geometric_invalid=g['geometry']['invalid_parts'],oversize=g['geometry']['oversize_parts'],
        contact_regions=regions,frequent_pairs=most,
        backpack=dict(all_nonrigid_new_contact_records=len(backpack),
            affected_poses=sorted({x['pose']for x in backpack}),trunk_single_axis_records=len(trunk),
            trunk_single_axis_poses=sorted({x['pose']for x in trunk}),examples=sorted(backpack,key=lambda x:-x['overlap_mm3'])[:12],
            user_retention_condition_fully_proven=False),manufacturing_release=False)
    put(B/'verification/review_summary.json',summary)
    lines=['# O23C 数字评审结果','',f'本报告对应 `assembly.npz` SHA-256：`{digest}`。','',
      '**结论：实体设计候选，未制造放行。** 网格和运动学通过不等于实体运动范围通过。','',
      '| 项目 | 结果 |','|---|---|',
      f'| A 站姿装配高度 | {g["geometry"]["height_mm"]:.1f} mm，低于 800 mm |',
      f'| 主要结构件、背盒及盖板的源索引网格 | {len(g["geometry"]["rows"])} 件；未通过项 {g["geometry"]["invalid_parts"]}；不等于 STL 已通过 |',
      f'| 几何打印空间 | 超过 170 mm 包围盒项：{g["geometry"]["oversize_parts"]}；未证明切片支撑与层向 |',
      '| 运动学 | 34 组检查，骨段朝向一致；中立骨长与肩髋宽保留，两腕中心重做；锁骨运动时肩中心平移轨迹改变 |',
      f'| 扩展动作 | {m["pose_count"]} 个采样；{len(pose_count)} 个存在新增接触，共 {len(hits)} 条记录 |','',
      '## 五个基础姿态','',
      '| 姿态 | 新增／加重的接触记录 |','|---|---|']
    labels={'A_STAND_35':'A 站姿','N_NEUTRAL':'双臂贴身中立姿态','left_elbow':'左肘动作','asymmetric':'非对称动作','right_forearm':'右前臂扭转'}
    lines += [f'| {labels[k]} | {v} |'for k,v in summary['basic_pose_counts'].items()]
    lines += ['','数量是“零件对 × 姿态”的记录数，不是故障零件数，也不是运动损失百分比。中立姿态的腕／手与髋腿接触不能通过隐藏零件解决。',
      '', '## 背部控制盒','',
      f'检测到背盒系统与其他运动段之间的新增接触 {len(backpack)} 条，涉及 {len(summary["backpack"]["affected_poses"])} 个姿态。胸腰单轴采样中为 {len(trunk)} 条。',
      '用户已确认控制板尚未制作。O23C 使用 64 × 60 mm 双面板布局和直接固定在胸廓的短背盒，取消 B2 长支撑架。PCB 尚未布线；用户要求的“不影响躯体动作”尚未获得全范围证明。',
      '', '## 下一轮几何修改的重点','',
      '1. 头颈、胸腰及锁骨附近：按实际运动扫掠重做接口周围空间，避免继续用细小补筋换取连接而产生新的挡位。',
      '2. 腕部：保持已确认的 UE 肘腕比例，缩小腕部安装端和传感器包络；解决双臂贴身时与髋腿的接触。',
      '3. 背盒：根据接触记录调整安装位置或形式，验证螺丝刀直线进入路径、螺母装入及线束余量。',
      '4. 保持当前人体轮廓，修改完成后重新检查；不得把全部角限缩小来掩盖实体碰撞。',
      '', '## 重量与持姿','']
    mass=load['printed_geometry_solid_equivalent_g']
    lines += [f'在所有已建模打印材料均匀为 {load["density_g_cm3"]} g/cm³ 的比较假设下，O22F7 打印实体等效为 {mass["O22F7"]:.1f} g，O23C 为 {mass["O23C"]:.1f} g。',
      '这不是实际切片耗材，也不包含五金、电路和线束。逐轴静态重力需求见 `../打印材料重力力矩对照.csv`；未验证关节摩擦能力、筋板强度或持姿。',
      '', '## 可直接使用的交付','',
      '可以用三维预览、Blender 装配、保留索引的 3MF 几何、参数化脚本、比例表和五金差额表评审。当前不适合整套批量打印。',
      '现有 O22F7 发布输入文件保持不变。O23 运动学配置在本目录隔离保存，未替换 UE 正在使用的配置。','']
    if exported:
        assert exported['geometry_sha256']==digest
        lines += ['## 导出格式检查','',
            f'STL 经坐标量化和顶点焊接后，有 {len(exported["stl_failures"])} 件未通过封闭性检查。STL 只能作为参考，不可作为打印放行依据。',
            f'另已生成 {len(exported["rows"])} 件 3MF 评审几何，逐项读取后确认坐标与三角面索引完全保留。3MF 不包含支撑或打印机配置，仍需切片和制造验证。',
            '源索引拓扑、实际导出拓扑和切片结果是三个不同检查，不能相互代替。详细记录见 `export_formats.json`。','']
    if tool and tool['geometry_sha256']==digest:
        lines += ['## 背盒工具通道','',f'12 个螺丝位置统一使用 6 mm 直径、80 mm 长直杆的检查：{"通过"if tool["passed"]else "未通过"}。靠近 XIAO 的 PCB 0 号螺丝使用 3 mm 杆、其余保持 6 mm 的工具方案：{"通过"if tool.get("slim_tool_plan_passed")else "未通过"}。PCB 螺丝检查时先移除盖板；不包含真实刀头、手柄、手部、线束或实物公差。详细结果见 `backpack_tool_access.json`。','']
    (B/'verification/评审结果.zh-CN.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps({k:summary[k]for k in ('full_pose_count','poses_with_new_contacts','new_contact_records','basic_pose_counts','contact_regions')},ensure_ascii=False),flush=True)
    print('BACKPACK',len(backpack),'TRUNK',len(trunk),flush=True)

if __name__=='__main__':main()
