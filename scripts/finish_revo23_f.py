"""Publish a single verified F assembly and bind its review notes to it."""
from revo23_clean import *
from package_revo23 import writecsv,NAMES


def engineering():
    parts,p,cfg=load_f();digest=sha(FROOT/'assembly.npz');rows=[];walls=[]
    kz=np.load(EHISTORY/'source/retained_interfaces.npz')
    for key,item in parts.items():
        if item['role']!='structure':continue
        path=FROOT/(key.replace('/','__')+'.npz');r=read(FROOT/'load_paths'/(path.stem+'.json'))
        assert r['candidate_sha256']==sha(path),('Stale section screen',key)
        assert r['rows'] and all(x['connected_voxel_path'] for x in r['rows'])
        for x in r['rows']:
            rows.append(dict(part=key,body=item['body'],**x,candidate_sha256=sha(path)))
        z=np.load(path.with_name(path.stem+'_skin.npz'));skin=solid(z['v'],z['f'])
        keep=solid(kz[key+'|v'],kz[key+'|f']);s=item['s'];m=trimesh.Trimesh(*vf(s),process=False)
        loss=max(0.,(skin-s).volume())
        assert loss<.05,('Anatomical skin was perforated',key,loss)
        cc=len([c for c in s.decompose() if c.volume()>1e-4])
        assert cc==1 and m.is_watertight
        keep_loss=max(0.,(keep-s).volume())
        assert keep_loss<.05,(key,'retained interface loss',keep_loss)
        walls.append(dict(part=key,components=cc,indexed_watertight=True,
            planned_clean_skin_missing_mm3=loss,retained_interface_missing_mm3=keep_loss))
    put(FROOT/'load_paths.json',dict(geometry_sha256=digest,rows=rows,structure_count=24,
        connected_paths=len(rows),passed=True,
        method='1 mm six-neighbour voxel min-cut; grid area divided by sqrt(3). Geometric bottleneck screen, not FEA or an allowable load.',
        physical_strength_verified=False,manufacturing_release=False))
    put(FROOT/'continuous_walls.json',dict(geometry_sha256=digest,rows=walls,
        analytic_clean_skins_preserved=True,independent_skin_perforations=0,
        original_E_skins_intentionally_replaced=True,manufacturing_release=False))


def publish():
    digest=sha(FROOT/'assembly.npz');s=read(FROOT/'staging.json')
    assert digest==s['geometry_sha256']
    for key,h in s['candidate_files'].items():
        assert sha(FROOT/(key.replace('/','__')+'.npz'))==h
    for name in ('daily_motion.json','edge_motion.json','fixed_interfaces.json','clean_design.json','physical_rod_count.json'):
        r=read(FROOT/name);assert r['geometry_sha256']==digest and r['passed'],(name,'failed/stale')
        if 'motion' in name:assert r['complete_policy'] and not r['trial']
    g=read(FROOT/'geometry.json')
    assert g['geometry_sha256']==digest
    assert not g['geometry']['invalid_parts'] and g['kinematics']['passed'] and g['geometry']['height_under_800mm']
    wire=read(FROOT/'wire_fixture_verification.json');assert wire['passed']
    for key,h in wire['candidate_mesh_hashes'].items():
        assert sha(FROOT/(key.replace('/','__')+'.npz'))==h
    h=read(FROOT/'harness/routing_plan.json')
    assert h['capacity_passed'] and not h['body_sections_missing_seats']
    engineering()
    shutil.copy2(FROOT/'assembly.npz',B/'assembly.npz')
    shutil.copy2(FROOT/'assembly.json',B/'assembly.json')
    cfg=read(CFG);cfg['revision']=FREV
    cfg['maximum_rods_per_shell_adjacent_component']=3
    cfg['notes']=[x for x in cfg['notes'] if not x.startswith(('O23E:','O23F:'))]
    cfg['notes'].append('O23F: symmetric analytic skins, small complete patches where coverage is limited, at most three explicitly counted rods per adjacent module; original hardware and body frames retained.')
    put(CFG,cfg)
    for src,dst in [('geometry.json','geometry.json'),('daily_motion.json','daily_motion.json'),
                    ('edge_motion.json','edge_paths.json'),('load_paths.json','load_paths.json'),
                    ('continuous_walls.json','continuous_walls.json'),('clean_design.json','clean_design.json'),
                    ('physical_rod_count.json','physical_rod_count.json')]:
        shutil.copy2(FROOT/src,B/'verification'/dst)
    for src,dst in [('harness/routing_plan.json','routing_plan.json'),('wire_seats.json','wire_seats.json'),
                    ('wire_channels.json','wire_channels.json'),('wire_fixture_verification.json','wire_fixture_verification.json')]:
        r=read(FROOT/src);r['geometry_sha256']=digest
        if dst=='routing_plan.json':r['schema']='POSEDOLL-O23F-HARNESS/1'
        put(B/'harness'/dst,r)
    put(B/'design/clean_revision.json',dict(revision=FREV,source_geometry_sha256=EHASH,
        geometry_sha256=digest,profile_sha256=sha(B/'profiles/device_profile.json'),
        maximum_rods_per_adjacent_component=3,manufacturing_release=False))
    shutil.copy2(FROOT/'harness/preliminary_cut_list.csv',B/'harness/preliminary_cut_list.csv')
    print('PUBLISHED F',digest,flush=True)


def notes():
    digest=sha(B/'assembly.npz');g=read(B/'verification/geometry.json')['geometry']
    counts=read(B/'verification/physical_rod_count.json');skin=read(B/'verification/clean_design.json')
    loads=read(B/'verification/load_paths.json');h=read(B/'harness/routing_plan.json')
    channels=read(B/'harness/wire_channels.json')['rows'];ex=read(B/'verification/export_formats.json')
    daily=read(B/'verification/daily_motion.json');edge=read(B/'verification/edge_paths.json')
    mass=read(B/'verification/gravity_demand.json')['printed_geometry_solid_equivalent_g']['O23F']
    previous=read(EHISTORY/'verification/gravity_demand.json')['printed_geometry_solid_equivalent_g']['O23E']
    writecsv(B/'连接杆数量表.csv',['部位','连接对象','连接杆数','上限'],
        [dict(部位=NAMES.get(r['part'].split('/',1)[1],r['part']),连接对象=k,连接杆数=v,上限=3)
         for r in counts['rows'] for k,v in r['counts'].items()])
    writecsv(B/'连接截面筛查.csv',['部位','安装面编号','截面筛查mm2','截面模量代理mm3','说明'],
        [dict(部位=NAMES.get(r['body'],r['body']),安装面编号=r['land'],
              截面筛查mm2=round(r['conservative_cut_area_mm2'],2),
              截面模量代理mm3=round(r['conservative_section_modulus_mm3'],2),
              说明='几何筛查，不能直接当作许用载荷') for r in loads['rows']])
    text=f"""# O23F 对称外壁与少量连接

本版按最新要求重建外壁，并删去 O23E 的密集支撑。当前实际高度 **{g['height_mm']:.2f} mm**，沿用原有 UE 人体参考点、双髋中心、骨段长度和关节映射。本轮沿用 O23E 的五金配置，不增加或更换五金件。相对 O22F7 原购清单的既有差异仍见 [五金变化表](五金变化表.csv)。

## 外形

- 大腿和小腿保留人体曲线；关节开口使用一条平顺的大曲线。
- 胸部改为完整圆角护片；腰和骨盆改为对称的后侧护片，前部运动空间保持开放。
- 肩部取消覆盖效率很低的大块镂空壳，保留紧凑的安装端与少量承力连接。
- 手臂用小型圆角护片。双手保留四指弯曲、拇指前扣的握拳形态，并统一两侧拳壳轮廓。
- 人体外壁按左右镜像检查；内部安装孔、传感板接口和走线座仍适配实际机构。它们不是整件几何完全镜像的承诺。

外壁由完整筒壁或单块圆角曲面生成，不再按障碍物逐个切出小豁口。最终模型中这些设计外壁均完整保留；关节大开口、检修空间和精密安装孔继续保留。

![O23F 实际装配](images/three_quarter.png)

## 连接数量与结构

以**同一个外壁结构件与相邻单个关节模块或完整背盒**为一组，最多 **{counts['maximum_rods_per_adjacent_component']} 根**连接杆，满足三根上限。直接连接两个安装端的杆会同时计入两端。详细记录见 [连接杆数量表](连接杆数量表.csv) 和 [几何计数报告](verification/physical_rod_count.json)。

采用少量明确的杆体和局部加宽安装台，替代 O23E 的多条细筋。布线固定座直接融合到内壁或杆体，没有另加一套支杆。薄弱部位按实际截面调整连接落点和承力路径；大腿近髋、上臂、前臂与背盒均单独检查。

{len(loads['rows'])} 处安装面到外壁或其他安装面的几何路径连通；完整数值见 [连接截面筛查](连接截面筛查.csv)。这是 1 mm 体素最小割筛查，不是有限元分析或承载认证。打印层方向、材料、螺钉预紧与持姿仍需首件验证。

## 日常动作与布线

- {daily['pose_count']} 个日常姿态及 {edge['pose_count']} 个加密过渡姿态：相邻部位必须处理的穿透记录为零，体积报告容差 0.05 mm³。
- 非相邻部位接触按已确定的规则作为提示；极限姿态不作为本次硬性条件。
- 24 个结构件为单个闭合实体；运动轴、原始角限、传感器配置和五金接口保持原方案。
- 实际打印件有 **{len(h['seats'])} 个布线固定座**、**{len(channels)} 条内部固定通道**。46 路五芯线束已按新固定点重算长度和容量。
- 仍按 AWG30 细多股软线、含绝缘外径不超过 0.7 mm 设计。关节间保留松弛线圈，不能拉紧。柔性线实际挤压和疲劳需试装验证。

详见 [布线与试装说明](harness/布线与试装说明.zh-CN.md) 和 [初步裁线表](harness/preliminary_cut_list.csv)。

## 文件与制造状态

按全部打印几何的建模实体体积及 PLA 密度换算，本版为 **{mass:.1f} g**，O23E 对照为 **{previous:.1f} g**，减少 **{previous-mass:.1f} g**。这不含五金、电子件和线材，也不是切片耗材预测。

提供 {len(ex['rows'])} 个索引网格 3MF 评审件。STL 回读拓扑未通过的件数为 {len(ex['stl_failures'])}，详见导出报告；优先使用 3MF 做切片审查。本版仍是数字工程评审稿，尚未完成切片、实物装配、静载与疲劳验证。背部控制板仍为未布线的布局稿。

O23E 原模型和报告保存在 [历史快照](history/O23E_before_clean_symmetric_walls_20261021/DESIGN.zh-CN.md)。

几何 SHA-256：`{digest}`。
"""
    (B/'CLEAN_SYMMETRIC_WALLS.zh-CN.md').write_text(text,encoding='utf8')
    (B/'DESIGN.zh-CN.md').write_text(text,encoding='utf8')
    (B/'CONTINUOUS_WALLS.zh-CN.md').write_text('# 当前版本 O23F\n\n最新外壁、连接数量与验证结果见 [O23F 设计说明](CLEAN_SYMMETRIC_WALLS.zh-CN.md)。\n',encoding='utf8')
    (B/'FINGERS_STRUCTURE_HARNESS.zh-CN.md').write_text('# 当前版本 O23F\n\n握拳与布线要求继续保留；结构和外壁已按最新要求重新设计。请阅读 [O23F 设计说明](CLEAN_SYMMETRIC_WALLS.zh-CN.md)。\n\n原 O23E 说明见 [历史版本](history/O23E_before_clean_symmetric_walls_20261021/FINGERS_STRUCTURE_HARNESS.zh-CN.md)。\n',encoding='utf8')
    stock=int(np.ceil(h['preliminary_active_m_each_color']*1.2/5)*5)
    writecsv(B/'harness/辅料清单.csv',['项目','规格','初步用量','建议备料','备注'],
        [dict(项目=c+'导线',规格='AWG30细多股软线，含绝缘外径≤0.7mm',
              初步用量=f"{h['preliminary_active_m_each_color']:.2f}m",建议备料=f'{stock}m',
              备注='每种颜色独立计算；先用样线试装，再裁剪') for c in ('黑','红','蓝','绿','黄')]+[
         dict(项目='扎带',规格='宽2.5mm，穿带段厚度≤1.2mm',
              初步用量=f"{len(h['seats'])}条",建议备料='40条',备注='轻扣固定，不压坏绝缘')])
    (B/'harness/布线与试装说明.zh-CN.md').write_text(f"""# O23F 布线与试装

当前模型包含 {len(h['seats'])} 个一体式固定座和 {len(channels)} 条固定通道。固定座直接融合到现有结构，没有独立的细支杆。预览中青色标记对应真实固定座，橙色对应已检查的内部通道。

46 块传感器板各用 5 根独立回线，共 230 根导体；不串接传感器。颜色依次为黑色 GND、红色 SENSOR_3V45、蓝色 CLK、绿色 DO、黄色 CSN。按 AWG30 细多股铜软线、含绝缘外径不超过 0.7 mm 预留；线材需要实际弯折等级，不能仅凭 AWG 判断寿命。

腕部线路依次经过前臂、肘、上臂、锁骨、胸部，到背盒侧面入口。腿部通过小腿、大腿、骨盆、腰、胸部回到背盒。左右躯干束线分开，背盒两个入口各承担约半数线束。实际逐轴路径、固定点坐标、通道容量和长度见 [routing_plan.json](routing_plan.json)。

每个活动关节两侧各自固定，关节中间留松弛弧形线圈。长度按 522 个已声明姿态的两端距离计算，并加入 R10 弯曲弧长、20 mm 活动余量和端接余量；R10 是设计预留，并不是线材厂家认证。固定通道只保证记录的几何空间，不代表任意柔性走线不会被挤压。

本轮初步每种颜色需 {h['preliminary_active_m_each_color']:.2f} m，最长单根预留 {h['maximum_preliminary_length_mm']} mm，详见 [46 路裁线表](preliminary_cut_list.csv)。建议每种颜色备 {stock} m。先买少量样线，通过最大束径、穿带、插拔、关节摆动与通信测试后再成批裁线。

扎带宽 2.5 mm，穿带段厚度不超过 1.2 mm。只需轻扣使线束不滑移；不得紧压线材，不得把活动余量绑死。试装时依次检查正反弯、扭转、肩部前伸、屈肘、屈髋和浅蹲，观察线束是否夹入摩擦面或接触磁铁/传感器板。

控制板仍是未布线的布局稿，不能直接投板。真实线束的疲劳、挤压和长线信号完整性尚待样件验证。
""",encoding='utf8')
    delivery=read(B/'DELIVERY.json')
    delivery['O23F_changes']=dict(maximum_rods_per_adjacent_component=counts['maximum_rods_per_adjacent_component'],
        symmetrical_external_skins=True,wire_seats=len(h['seats']),internal_channels=len(channels),
        source_geometry_sha256=digest,physical_strength_verified=False)
    put(B/'DELIVERY.json',delivery)
    print('NOTES F',mass,'g',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--publish',action='store_true')
    ap.add_argument('--notes',action='store_true');a=ap.parse_args()
    if a.publish:publish()
    if a.notes:notes()
