"""Publish the unified I contours only after source, STL and native print gates."""
from revo23_unified import *
import finish_revo23_h as previous
from package_revo23 import NAMES
import html,zipfile

PUBLIC=B/'a1mini_pla_O23I'

def gates():
    previous.HROOT=IROOT;previous.HREV=IREV;previous.GHISTORY=IHISTORY
    digest=previous.gates(True)
    r=read(IROOT/'external_contours.json');assert r['passed'] and r['geometry_sha256']==digest
    r=read(IROOT/'harness/routing_plan.json');assert r['geometry_sha256']==digest
    assert sha(IROOT/'profiles/device_profile.json')==sha(IHISTORY/'profiles/device_profile.json')
    exported={r['id']:r for r in read(IROOT/'export/repair.json')['rows']}
    hashes={r['key']:r['stl_sha256'] for r in exported.values()}
    export_digest=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    for name in ('smooth_connections','continuous_walls','physical_rod_count','end_faces','fixed_interfaces','geometry_difference','wire_fixtures','daily_motion','edge_motion'):
        check=read(IROOT/'export/verification'/(name+'.json'))
        assert check['export_set_sha256']==export_digest,('stale STL verification',name)
    for row in read(IROOT/'print/results.json')['rows']:
        spec=read(IROOT/'print/candidates'/(row['id']+'.json'));guard=IROOT/'print/guards_v5'/(row['id']+'.npz')
        assert spec['stl_sha256']==exported[row['id']]['stl_sha256']
        assert row['clearance']['guard_sha256']==sha(guard)
        assert read(guard.with_suffix('.json'))['stl_sha256']==exported[row['id']]['stl_sha256']
    return digest

def summary(digest):
    rows=[];preservation={r['part']:r for r in read(IROOT/'functional_voids.json')['rows']}
    for key,item in load_i()[0].items():
        if item['role']!='structure':continue
        r=i_records(key);delta=preservation[key]['added_mm3']
        rows.append(dict(part=key,unified_mounts=r.get('unified_mounts',[]),auxiliary=r.get('unified_auxiliary',[]),net_added_mm3=delta))
    out=dict(revision=IREV,geometry_sha256=digest,baseline_geometry_sha256=HHASH,rows=rows,
        structures_inspected=len(rows),unified_mount_count=sum(x['status']=='unified_contour'for r in rows for x in r['unified_mounts']),
        rods=42,extra_printed_parts=0,extra_hardware=0,physical_strength_verified=False)
    put(IROOT/'unified_contours.json',out);return out

def package(digest):
    PUBLIC.mkdir(exist_ok=True);(PUBLIC/'projects').mkdir(exist_ok=True);(PUBLIC/'stl').mkdir(exist_ok=True)
    projects={r['key']:r for r in read(IROOT/'print/results.json')['rows']};rows=[]
    for e in read(IROOT/'export/repair.json')['rows']:
        p=projects[e['key']];dst=PUBLIC/'projects'/(e['id']+'_A1mini_PLA.3mf');shutil.copy2(IROOT/p['project'],dst)
        stl=PUBLIC/'stl'/Path(e['staged_stl']).name;shutil.copy2(IROOT/e['staged_stl'],stl)
        name=NAMES.get(e['key'].split('/',1)[1],e['key'].split('/',1)[1])
        rows.append(dict(id=e['id'],key=e['key'],name=name,project=dst.relative_to(PUBLIC).as_posix(),project_sha256=sha(dst),
            stl=stl.relative_to(PUBLIC).as_posix(),stl_sha256=sha(stl),estimated_hours=p['estimated_s']/3600,support_g=p['support_g'],
            total_g=p['total_deposited_g'],temporary_caps=p['caps']['count'],passed=True))
    m=dict(revision=IREV,geometry_sha256=digest,rows=rows,total_support_g=sum(r['support_g']for r in rows),
        total_extruded_g=sum(r['total_g']for r in rows),total_hours=sum(r['estimated_hours']for r in rows),
        printer='Bambu Lab A1 mini, 0.4 mm nozzle, PLA',physical_tested=False,native_slicing_and_support_audits_passed=True)
    put(PUBLIC/'manifest.json',m)
    first='本轮先试打骨盆 S13，检查髋端—腰部的连续底座；再试左前臂 S18、左大腿 S19，以及左锁骨内外段 S15 / S10。与对应五金试装，确认工具、线槽及活动间隙。'
    (PUBLIC/'README.zh-CN.md').write_text(f'''# O23I · A1 mini / PLA

本包与 O23I 连续连接底座模型配套，几何 `{digest}`。32 件，每件一盘；使用 0.4 mm 喷嘴，直接打开 3MF 保留摆放方向与支撑设置。

{first}

主结构件至少 5 道壁、20% gyroid 填充；局部采用 6 道壁，小附件按工程单独设置。先拆外侧支撑，再拆局部支撑及临时剥离片，避免以连接杆作撬杠。manifest.json 记录每件剥离片数量。

全部工程完成原生切片、封闭网格、悬空起始层、安装孔与布线槽内支撑路径、临时剥离片间距检查。实际层间强度、拆支撑及重复摆动仍待首件试验。

切片估计合计 {m['total_hours']:.1f} 小时、{m['total_extruded_g']:.1f} g 挤出耗材，其中支撑 {m['total_support_g']:.1f} g。这不是整机净重。

H 版文件保留用于历史对照；I 版模型请配套使用本包。
''',encoding='utf8')
    trs=''.join(f'<tr><td>{r["id"]}</td><td>{html.escape(r["name"])}</td><td>{r["estimated_hours"]:.1f} h</td><td>{r["total_g"]:.1f} g</td><td>{r["temporary_caps"]}</td><td><a href="{r["project"]}">3MF</a> · <a href="{r["stl"]}">STL</a></td></tr>'for r in rows)
    (PUBLIC/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>O23I A1 mini 打印包</title><style>body{max-width:1050px;margin:40px auto;padding:20px;font:16px/1.65 system-ui;background:#f4f3ef;color:#253b40}table{width:100%;border-collapse:collapse;background:white}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left}a{color:#087774}</style>'+f'<h1>O23I · 连续连接底座</h1><p>32 件 A1 mini / PLA 工程通过离线切片复查；实物待试打。</p><p>{first}</p><table><tr><th>编号</th><th>零件</th><th>估时</th><th>耗材</th><th>待拆剥离片</th><th>文件</th></tr>{trs}</table><p><a href="README.zh-CN.md">打印说明</a> · <a href="../preview/index.html">完整人偶</a></p>',encoding='utf8')
    return m

def detail_page(digest,report):
    dest=B/'verification/user_review_I';dest.mkdir(exist_ok=True)
    comparisons=[('frame__pelvis_actual','骨盆：髋端到腰部','把原底座、承接头和杆根整理成连续过渡，保留轴孔和扎带入口。'),
                 ('frame__waist_actual','腰部','合并固定连接处的叠层；活动叉口及安装平面保留。'),
                 ('frame__forearm_l_actual','左前臂','关节安装座与杆根整合，布线槽继续贯通。'),
                 ('frame__thigh_l_hip_front','大腿髋端','平底座与杆根连续相接，周围运动件保持独立。')]
    cards=[]
    for name,title,caption in comparisons:
        for folder,label in ((HROOT,'H'),(IROOT,'I')):
            src=folder/'images'/(name+'.png');shutil.copy2(src,dest/(label+'_'+src.name))
        cards.append(f'<section><h2>{title}</h2><div class="pair"><figure><img src="H_{name}.png"><figcaption>H · 修改前</figcaption></figure><figure><img src="I_{name}.png"><figcaption>I · 修改后</figcaption></figure></div><p>{caption}</p></section>')
    gallery=[]
    for r in report['rows']:
        stem=r['part'].replace('/','__')+'_actual.png';shutil.copy2(IROOT/'images'/stem,dest/stem)
        title=NAMES.get(r['part'].split('/',1)[1],r['part'])
        gallery.append(f'<figure><a href="{stem}"><img src="{stem}"></a><figcaption>{html.escape(title)}</figcaption></figure>')
    page='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O23I 连续连接底座</title><style>body{max-width:1200px;margin:40px auto;padding:20px;background:#f3f3ee;color:#253b40;font:16px/1.7 system-ui}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}figure{margin:0;background:white}img{width:100%;display:block}figcaption{padding:10px}h2{font-size:21px}a{color:#087774}code{overflow-wrap:anywhere}</style>'
    page+=f'<h1>O23I · 连续连接底座</h1><p>检查全身 {report["structures_inspected"]} 个结构件，把同一固定件上的叠层底座、承接头与杆根整合。活动关节、可拆盖板、安装孔及线槽保留。连接杆仍为 42 根，没有新增独立打印件或五金。</p><p><a href="../../preview/index.html">完整人偶预览</a> · <a href="../../UNIFIED_MOUNTS.zh-CN.md">检查说明</a> · <a href="../../a1mini_pla_O23I/index.html">配套打印文件</a></p>'+''.join(cards)+'<h2>全身结构件检查图</h2><div class="gallery">'+''.join(gallery)+'</div>'
    page+=f'<p>I 图直接使用通过检查的实际 STL 网格；H 对照采用前版 CAD 渲染。原偏置五金导致部分内部安装结构不同，人体外壁保持镜像。数字检查不替代实物强度和拆支撑试验。</p><p>模型版本：<code>{digest}</code></p>'
    (dest/'index.html').write_text(page,encoding='utf8')

def update_html(path):
    s=path.read_text(encoding='utf8').replace('O23H','O23I').replace('端面坐实，<br>连接复查。','底座一体，<br>外形连贯。')
    start=s.index('<p class="intro">');end=s.index('</p>',start)+4
    s=s[:start]+'<p class="intro">整理全身固定连接处的叠层底座，形成连续过渡。保留 42 根连接杆、安装孔及布线通道；相邻动作与配套打印工程已重新检查。</p>'+s[end:]
    s=s.replace('user_review_H','user_review_I').replace('端面底座与全身连接细节','连续底座修改前后对照')
    path.write_text(s,encoding='utf8')
    q=path.parent/'provenance.json'
    if q.exists():r=read(q);r['asset_hashes']['index.html']=sha(path);put(q,r)

def publish():
    digest=gates();previous.bind_review(digest)
    r=read(IROOT/'harness/routing_plan.json');r['schema']='POSEDOLL-O23I-HARNESS/1';put(IROOT/'harness/routing_plan.json',r)
    report=summary(digest);manifest=package(digest);detail_page(digest,report)
    cfg=read(IROOT/'parameters.json');cfg['revision']=IREV
    cfg['notes']=[s for s in cfg.get('notes',[])if not s.startswith('O23I:')]+['O23I: unify fixed mounting contours and wall landings while preserving H core, original interfaces, wire voids, 42 rods and motion policy. Physical tests pending.']
    put(CFG,cfg)
    for name in ('assembly.npz','assembly.json'):shutil.copy2(IROOT/name,B/name)
    for path in (IROOT/'verification').glob('*.json'):shutil.copy2(path,B/'verification'/path.name)
    for name in ('external_contours','unified_contours'):shutil.copy2(IROOT/(name+'.json'),B/'verification'/(name+'.json'))
    shutil.copytree(IROOT/'harness',B/'harness',dirs_exist_ok=True)
    for name in ('end_faces','geometry_difference','wire_fixtures','daily_motion','edge_motion','fixed_interfaces'):
        shutil.copy2(IROOT/'export/verification'/(name+'.json'),B/'verification'/('export_I_'+name+'.json'))
    entries={r['id']:r for r in manifest['rows']};rows=[]
    for r in read(IROOT/'export/repair.json')['rows']:
        e=entries[r['id']];rows.append(dict(r,review_3mf=(PUBLIC/e['project']).relative_to(B).as_posix(),review_stl=(PUBLIC/e['stl']).relative_to(B).as_posix()))
    put(B/'verification/export_formats.json',dict(revision=IREV,geometry_sha256=digest,rows=rows,stl_failures=[],native_print_slicing_verified=True,physical_print_tested=False))
    delivery=read(B/'DELIVERY.json');delivery.update(revision=IREV,geometry_sha256=digest,current_print_package=PUBLIC.relative_to(B).as_posix(),manufacturing_release=False,
        I_changes=dict(unified_mounts=report['unified_mount_count'],structures_inspected=24,rods=42,wire_seats=33,wire_channels=8,daily_poses=408,transition_poses=114,physical_strength_verified=False))
    put(B/'DELIVERY.json',delivery)
    mincut=min(r['conservative_cut_area_mm2']for r in read(IROOT/'load_paths.json')['rows'])
    doc=f'''# O23I：固定连接底座的连续外形

用户指出的叠层外形确实存在。前版多数位置已经属于同一打印实体，但外轮廓仍呈现原安装座、加厚头和连接杆底座相互叠加的台阶。本轮检查全身 24 个结构件，将同一固定件上的这些过渡整理成整体；同时整理外壁连接脚和扎带座根部。没有增加独立打印件和五金。

髋端到腰部的连接是重点：原先的叠层承接部改成连续斜面和圆角边缘。其余结构按相同原则处理。活动关节之间、可拆盖板之间不能固结；轴孔、安装平面、工具通道、运动间隙和扎带口仍是必要功能结构。

保留 H 版承力核心，全部 42 根杆的两端承接检查通过，单一相邻模块不超过 3 根。47 个原安装区重新进行细颈筛查，最小几何指标 {mincut:.2f} mm²；这不是实测承载能力。人体外壁轮廓与指部保持原设计；偏置五金造成的局部内部差异保留。

408 个日常姿态、114 个过渡姿态必检相邻干涉为零。原安装孔、33 个布线座、8 条布线通道、46 路五芯线容量及预留长度复查通过。背板拆出与工具进入通过，XIAO 旁一颗螺钉仍需直径 3 mm 的细工具。身高约 706.26 mm，UE 比例、髋中心及设备配置不变。

32 个 STL 均为单实体、封闭且朝向一致。布尔运算的数值重合面采用有界精度清理，并对实际导出模型重新检查端面、孔槽、布线和动作；无全局补洞或体素重建。32 个 A1 mini / PLA 3MF 重新切片，检查支撑不堵孔槽、悬空起始层及剥离片间距。

先试骨盆 S13，再试左前臂 S18、左大腿 S19、左锁骨 S15 / S10。实际 PLA 强度、反复运动和支撑拆除待试打确认。

- [修改前后与全身细节](verification/user_review_I/index.html)
- [完整装配预览](preview/index.html)
- [I 版打印文件](a1mini_pla_O23I/index.html)
- [全身处理清单](verification/unified_contours.json)

几何 SHA-256：`{digest}`。
'''
    for name in ('UNIFIED_MOUNTS.zh-CN.md','DESIGN.zh-CN.md'):(B/name).write_text(doc,encoding='utf8')
    import present_revo23 as view
    view.B=B;view.REV=IREV
    view.main();update_html(B/'preview/index.html')
    prov=read(B/'preview/provenance.json');prov['render_source']='Actual verified STL for the 32 exported printed parts; original CAD for retained hardware and electronics.';prov['stl_sha256']={r['key']:r['stl_sha256']for r in rows};put(B/'preview/provenance.json',prov)
    update_html(H/'cad/revO23/web/index.html')
    archive=B/'exports/O23I_A1mini_PLA_3MF.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED)as z:
        for path in PUBLIC.rglob('*'):
            if path.is_file():z.write(path,path.relative_to(PUBLIC.parent))
    with zipfile.ZipFile(archive)as z:assert z.testzip()is None
    put(IROOT/'WORK_IN_PROGRESS.json',dict(revision=IREV,status='published',geometry_sha256=digest,archive_sha256=sha(archive)))
    print('PUBLISHED I',digest,manifest['total_hours'],manifest['total_extruded_g'],flush=True)

if __name__=='__main__':publish()
