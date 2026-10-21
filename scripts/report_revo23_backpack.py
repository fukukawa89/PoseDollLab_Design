"""Geometry-bound report for the user's retained, deeper backpack decision."""
from deepen_revo23_backpack import *
from package_revo23 import writecsv

def stats(hits,keys):
    hh=[h for h in hits if not h['same_rigid_owner']and any(k in keys for k in h['pair'])]
    trunk=[h for h in hh if h['pose'].startswith(('waist/','chest/'))]
    shoulder=[h for h in hh if h['pose'].startswith(('clavicle_','upperarm_'))]
    return dict(records=len(hh),poses=sorted({h['pose']for h in hh}),
        trunk_records=len(trunk),trunk_poses=sorted({h['pose']for h in trunk}),
        shoulder_records=len(shoulder),shoulder_poses=sorted({h['pose']for h in shoulder}),
        hits=hh)

def main():
    digest=sha(B/'assembly.npz');motion=read(B/'verification/motion_full.json');geo=read(B/'verification/geometry.json')
    tool=read(B/'verification/backpack_tool_access.json');mount=read(B/'verification/backpack_mount.json')
    assert all(r['geometry_sha256']==digest for r in(motion,geo,tool));assert mount['source_geometry_sha256']==digest
    keys={r['key']for r in read(B/'assembly.json')['items']if r['key'].startswith('o22/')}
    shell={k for k in keys if not k.startswith('o22/backpack_')};support=keys-shell
    old=read(HISTORY/'verification/motion_full.json');oldkeys={r['key']for r in read(HISTORY/'assembly.json')['items']if r['key'].startswith('o22/')}
    before=stats(old['new_or_increased_contacts'],oldkeys);after=stats(motion['new_or_increased_contacts'],keys)
    case=stats(motion['new_or_increased_contacts'],shell);stand=stats(motion['new_or_increased_contacts'],support)
    report=dict(geometry_sha256=digest,previous_geometry_sha256=INPUT_HASH,revision=REVISION,
        user_decision='继续保留背盒，允许增加后方厚度',translation_neutral_mm=mount['translation_neutral_mm'],
        before=before,after=after,box_and_electronics=case,support_and_mount_fasteners=stand,
        tool_access=tool,full_motion_proven=False,manufacturing_release=False)
    put(B/'verification/backpack_revision.json',report)
    mount['tool_access_verified']=tool['passed'];mount['tool_access_scope']=tool['scope']
    mount['sampled_backpack_motion_passed']=after['records']==0;put(B/'verification/backpack_mount.json',mount)
    lines=['# O23B2 背盒修订','',f'当前几何 SHA-256：`{digest}`。','',
        '已落实用户选择：继续保留背盒，允许增加后方厚度。当前为设计评审候选，不是制造放行。','',
        '## 已改变的实体','',
        '- 控制板、连接器、盖板与盒体作为整组后移 100 mm、上移 53 mm；电路板、接口和原固定螺钉不缩放。',
        '- 增加 O23B-C02 独立支撑架，保持胸廓本体尺寸可打印。盒体继续使用 O23B-C01 编号。',
        '- 胸廓—支架、支架—盒体各四组 M3×8 与 M3 螺母，共八组；全部螺钉头朝后。胸廓螺母侧向装入，支架螺母从前方装入后再装盒体。',
        '- 原盒体最后端在中立坐标约 X=-130 mm，新版约 X=-230 mm。后方突出明显增加，请通过侧视图评审。',
        '- 骨长、肘腕比例、46 路测量轴和身高约 68.4 cm 保持。其他骨段的源数组逐位保留。','',
        '## 同一组 343 个姿态的实际实体检查','',
        '| 对象 | 接触记录 | 涉及姿态 | 胸腰单轴记录 | 肩部单轴记录 |','|---|---:|---:|---:|---:|',
        f'| 旧 B 版整个背盒系统 | {before["records"]} | {len(before["poses"])} | {before["trunk_records"]} | {before["shoulder_records"]} |',
        f'| B2 盒体及电路、盖板 | {case["records"]} | {len(case["poses"])} | {case["trunk_records"]} | {case["shoulder_records"]} |',
        f'| B2 支架及安装紧固件 | {stand["records"]} | {len(stand["poses"])} | {stand["trunk_records"]} | {stand["shoulder_records"]} |',
        f'| B2 整个背盒系统 | {after["records"]} | {len(after["poses"])} | {after["trunk_records"]} | {after["shoulder_records"]} |','',
        '记录数是零件对乘姿态，不能解释为运动范围百分比。盒体避开某个姿态不代表支架避开；单轴采样通过也不代表组合或连续动作通过。',
        '此次重新计算所有改变零件与当前装配的接触；未改变零件对只有在顶点、索引、归属及运动学配置一致时复用旧结果。追踪记录见 `../verification/backpack_change_scope.json`。','',
        '## 工具、打印与五金','',
        f'八个螺钉位置 × 五个装配姿态，直径 6 mm、长度 80 mm 的直杆通道检查：**{"通过"if tool["passed"]else "未通过"}**。',
        '此结果只覆盖直杆，不包含手柄、手指和电线，也没有代替螺母装入及打印公差试验。',
        f'26 件主要结构和附件的源索引网格未通过项：`{geo["geometry"]["invalid_parts"]}`；170 mm 包围盒未通过项：`{geo["geometry"]["oversize_parts"]}`。',
        '具体五金缺口见 `../五金变化表.csv`。相对上一版 B 再增加四颗 M3×8 和四颗 M3 螺母；这些均沿用 O22F7 规格。','',
        '## 当前限制','',
        '背盒系统仍须解决上表保留的干涉。后移增加胸腰的负载力臂，需要按实际控制板、线束和打印质量做持姿及强度试验。线束必须留活动余量，尚未给出已验证的长度或走线。',
        '其他身体部位的干涉与主要结构 STL 焊接后拓扑问题仍在总报告中，当前不能整套打印。3MF 保留索引的写读检查也不能替代切片、无自接触和实物装配验证。','',
        '旧版快照及图片：`../history/O23B_before_deeper_backpack_20261020/`。新版实际几何侧视图：`../images/side.png`；背盒局部图：`../images/backpack_detail.png`。','']
    (B/'design/BACKPACK_REVISION.zh-CN.md').write_text('\n'.join(lines),encoding='utf8')
    print('BACKPACK BEFORE/AFTER',before['records'],after['records'],'BOX',case['records'],'SUPPORT',stand['records'],'TOOL',tool['passed'],flush=True)

if __name__=='__main__':main()
