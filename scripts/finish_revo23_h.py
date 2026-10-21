"""Publish H only after independent geometry, export and native print checks."""
from revo23_endfaces import *
from package_revo23 import NAMES,writecsv
import html,zipfile

PUBLIC=B/'a1mini_pla_O23H'
def gates(printing=False):
    digest=sha(HROOT/'assembly.npz');stage=read(HROOT/'staging.json');assert stage['geometry_sha256']==digest
    for key,value in stage['candidate_files'].items():assert sha(HROOT/(key.replace('/','__')+'.npz'))==value
    names=('daily_motion','edge_motion','fixed_interfaces','smooth_connections','continuous_walls','physical_rod_count','load_paths','candidate_end_faces','functional_voids')
    for name in names:
        r=read(HROOT/(name+'.json'));assert r['passed'] and r['geometry_sha256']==digest,name
    assert read(HROOT/'candidate_end_faces.json')['rods']==42
    assert min(r['conservative_cut_area_mm2'] for r in read(HROOT/'load_paths.json')['rows'])>=20
    g=read(HROOT/'geometry.json');assert g['geometry_sha256']==digest and not g['geometry']['invalid_parts'] and g['kinematics']['passed'] and g['geometry']['height_under_800mm']
    for name in ('smooth_connections','continuous_walls','physical_rod_count','end_faces','fixed_interfaces','geometry_difference','wire_fixtures')+ (('daily_motion','edge_motion') if printing else ()):
        r=read(HROOT/'export/verification'/(name+'.json'));assert r['passed'] and r['geometry_sha256']==digest,('export',name)
    access=read(HROOT/'verification/backpack_tool_access.json');assert access['geometry_sha256']==digest and access['slim_tool_plan_passed'] and access['pcb_removal']['passed']
    routes=read(HROOT/'harness/routing_plan.json');assert routes['capacity_passed'] and not routes['body_sections_missing_seats']
    if printing:
        r=read(HROOT/'print/results.json');assert r['geometry_sha256']==digest and r['passed'] and len(r['rows'])==32
        assert len({x['id'] for x in r['rows']})==32
        assert {x['id'] for x in r['rows']}=={x['id'] for x in read(HROOT/'export/repair.json')['rows']}
        for row in r['rows']:
            assert row['passed'] and sha(HROOT/row['project'])==row['project_sha256'],row['id']
            assert sha(HROOT/row['source_project'])==row['source_sha256'],row['id']
    return digest

def bind_review(digest):
    for src,dst in [('geometry','geometry'),('daily_motion','daily_motion'),('edge_motion','edge_paths'),('fixed_interfaces','fixed_interfaces'),
        ('smooth_connections','smooth_connections'),('continuous_walls','continuous_walls'),('physical_rod_count','physical_rod_count'),
        ('load_paths','load_paths'),('candidate_end_faces','connection_end_faces'),('functional_voids','functional_voids')]:
        shutil.copy2(HROOT/(src+'.json'),HROOT/'verification'/(dst+'.json'))
    assert sha(HROOT/'profiles/device_profile.json')==sha(GHISTORY/'profiles/device_profile.json')
    hip=read(GHISTORY/'verification/hip_centers.json');hip.update(geometry_sha256=digest,
        inherited_from='Identical device profile and fully retained native interfaces; kinematics and native retention separately rechecked.')
    put(HROOT/'verification/hip_centers.json',hip)
    routes=read(HROOT/'harness/routing_plan.json');routes.update(schema='POSEDOLL-O23H-HARNESS/1',geometry_sha256=digest,input_geometry_sha256=digest);put(HROOT/'harness/routing_plan.json',routes)
    wire=read(HROOT/'export/verification/wire_fixtures.json');put(HROOT/'harness/wire_fixture_verification.json',wire)
    (HROOT/'preview').mkdir(exist_ok=True)

def update_html(path,complete):
    s=path.read_text(encoding='utf8').replace('POSEDOLL LAB · O23G','POSEDOLL LAB · O23H')
    s=s.replace('圆整连接，<br>稳固落脚。','端面坐实，<br>连接复查。')
    start=s.index('<p class="intro">');end=s.index('</p>',start)+4
    s=s[:start]+'<p class="intro">42 根连接杆逐一检查两端。髋端采用完整承接底座，薄安装座局部一体加厚。外壁继续保持左右对称，孔位、布线和相邻动作已复查；偏置五金的局部连接差异单独记录。</p>'+s[end:]
    s=s.replace('32 件 STL 与切片验证通过 · 实物待试打', '32 件 STL 与切片验证通过 · 实物待试打' if complete else '数字几何检查通过 · 打印工程复核中')
    s=s.replace('../verification/stl_export_review/index.html','../a1mini_pla_O23H/index.html').replace('STL 修复、切片验证与下载','O23H STL、切片验证与下载')
    s=s.replace('../verification/user_review_G/index.html','../verification/user_review_H/index.html').replace('大腿、小臂与骨盆细节对照','端面底座与全身连接细节')
    path.write_text(s,encoding='utf8')
    provenance=path.parent/'provenance.json'
    if provenance.exists():
        r=read(provenance);r['asset_hashes']['index.html']=sha(path);put(provenance,r)

def review():
    digest=gates(False);bind_review(digest)
    import present_revo23 as view
    view.B=HROOT;view.REV=HREV;view.main();update_html(HROOT/'preview/index.html',False)
    print('H REVIEW',digest,flush=True)

def package(digest):
    PUBLIC.mkdir(exist_ok=True);(PUBLIC/'projects').mkdir(exist_ok=True);(PUBLIC/'stl').mkdir(exist_ok=True)
    projects=read(HROOT/'print/results.json')['rows'];exports=read(HROOT/'export/repair.json')['rows'];bykey={r['key']:r for r in projects};rows=[]
    for row in exports:
        project=bykey[row['key']];dst=PUBLIC/'projects'/(row['id']+'_A1mini_PLA.3mf');shutil.copy2(HROOT/project['project'],dst)
        stl=PUBLIC/'stl'/Path(row['staged_stl']).name;shutil.copy2(HROOT/row['staged_stl'],stl)
        name=NAMES.get(row['key'].split('/',1)[1],row['key'].split('/',1)[1])
        rows.append(dict(id=row['id'],key=row['key'],name=name,project=dst.relative_to(PUBLIC).as_posix(),project_sha256=sha(dst),
            stl=stl.relative_to(PUBLIC).as_posix(),stl_sha256=sha(stl),estimated_hours=project['estimated_s']/3600,
            support_g=project['support_g'],total_g=project['total_deposited_g'],temporary_caps=project['caps']['count'],passed=True))
    manifest=dict(revision=HREV,geometry_sha256=digest,rows=rows,total_support_g=sum(r['support_g'] for r in rows),
        total_extruded_g=sum(r['total_g'] for r in rows),total_hours=sum(r['estimated_hours'] for r in rows),
        printer='Bambu Lab A1 mini, 0.4 mm nozzle, PLA',physical_tested=False,native_slicing_and_support_audits_passed=True)
    put(PUBLIC/'manifest.json',manifest)
    first='先试打左大腿 O23H-S19、左前臂 O23H-S18，再试左锁骨内段 S15 与外段 S10、骨盆 S13。与对应关节件试装，检查端面根部、螺丝进入、扎带穿入和摆动余量。'
    readme=f'''# O23H — A1 mini / PLA

本包替代 O23G 的 32 件打印工程，对应几何 `{digest}`。每件一盘，使用 **0.4 mm 喷嘴**。工程已保存摆放方向、PLA 参数、支撑避让及离线切片结果；请直接打开 3MF 保留这些设置。

{first}

主结构件使用 5 道壁、20% gyroid 填充；小附件按工程单独设置。临时剥离片属于支撑辅助，打印后拆除，不能留在零件上。各件数量见 manifest.json 的 temporary_caps。先从外侧支撑拆起，再处理局部接触点，避免用连接杆作撬杠。

全部 32 件通过原生网格保持、切片修补计数为零、底板范围、孔槽内支撑路径、悬空起始层和临时剥离片间距检查。模型实体闭合，连接杆两端和承力截面另有独立几何检查。实际层间强度、支撑拆除和反复摆动仍需首件确认。

预计全部挤出耗材 {manifest['total_extruded_g']:.1f} g，其中支撑 {manifest['total_support_g']:.1f} g；串行估时 {manifest['total_hours']:.1f} 小时。是切片估算，包含支撑与裙边/边缘，不代表整机净重。
'''
    (PUBLIC/'README.zh-CN.md').write_text(readme,encoding='utf8')
    trs=''.join(f'<tr><td>{r["id"]}</td><td>{html.escape(r["name"])}</td><td>{r["estimated_hours"]:.1f} h</td><td>{r["total_g"]:.1f} g</td><td>{r["temporary_caps"]}</td><td><a href="{r["project"]}">3MF</a> · <a href="{r["stl"]}">STL</a></td></tr>' for r in rows)
    page='<!doctype html><meta charset="utf-8"><title>O23H A1 mini 打印包</title><style>body{max-width:1050px;margin:40px auto;padding:20px;font:16px/1.65 system-ui;background:#f4f3ef;color:#253b40}table{width:100%;border-collapse:collapse;background:white}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left}a{color:#087774}.note{padding:18px;background:#e4ece7}</style>'
    page+=f'<h1>O23H · 端面连接修订</h1><p class="note">32 件 A1 mini / PLA 工程已完成离线切片复查；实物待试打。请使用本包替代 G 版。</p><p>{first}</p><table><tr><th>编号</th><th>零件</th><th>估时</th><th>耗材</th><th>待拆剥离片</th><th>文件</th></tr>{trs}</table><p><a href="README.zh-CN.md">打印说明</a> · <a href="../preview/index.html">完整人偶预览</a></p>'
    (PUBLIC/'index.html').write_text(page,encoding='utf8')
    return manifest

def detail_page(digest):
    dest=B/'verification/user_review_H';dest.mkdir(exist_ok=True)
    pictures=[('frame__thigh_l_hip_front','大腿髋端：完整底座','圆杆端面埋入完整承接部，平底座连接原安装座。'),
              ('frame__thigh_l_hip_back','大腿髋端背面','从另一侧检查底座接合与孔位避让。'),
              ('frame__thigh_l_actual','左大腿整体','保留外壁轮廓，连接杆数量未增加。'),
              ('frame__upperarm_l_actual','上臂','局部承接头与原关节安装区一体连接。'),
              ('frame__forearm_l_actual','前臂','检查杆端与完整承接面；保留内部布线位置。'),
              ('frame__clavicle_l_actual','锁骨外段','薄安装座局部加厚，保留五金避让。'),
              ('frame__clavicle_l.protract_frame_actual','锁骨内段','检查安装区承接截面与转动空间。'),
              ('frame__pelvis_actual','骨盆','移除两根冗余撑杆，外壁轮廓继续保持对称。')]
    cards=[]
    for name,title,caption in pictures:
        src=HROOT/'images'/(name+'.png');shutil.copy2(src,dest/src.name)
        cards.append(f'<figure><a href="{src.name}"><img src="{src.name}" alt="{title}"></a><figcaption><h2>{title}</h2>{caption}</figcaption></figure>')
    page='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O23H 连接端面复查</title><style>body{max-width:1200px;margin:40px auto;padding:20px;background:#f3f3ee;color:#253b40;font:16px/1.7 system-ui}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:24px}figure{margin:0;background:white}img{width:100%;display:block}figcaption{padding:16px}h2{font-size:19px;margin:0}a{color:#087774}code{overflow-wrap:anywhere}</style>'
    page+='<h1>O23H · 连接端面复查</h1><p>以下图片直接由本版 CAD 几何渲染。24 个结构件、42 根连接杆的两端均已检查完整端面承接，并复查孔位、布线与相邻动作。局部连接仍需适配原有偏置五金。</p>'
    page+='<p><a href="../../preview/index.html">旋转查看完整人偶</a> · <a href="../../CONNECTION_END_FACES.zh-CN.md">检查说明</a> · <a href="../../a1mini_pla_O23H/index.html">本版打印文件</a></p><main>'+''.join(cards)+'</main>'
    page+=f'<p>数字检查通过；实际 PLA 强度、拆支撑和试装待首件确认。</p><p>几何 SHA-256：<code>{digest}</code></p>'
    (dest/'index.html').write_text(page,encoding='utf8')

def publish():
    digest=gates(True);bind_review(digest);manifest=package(digest)
    detail_page(digest)
    cfg=read(HROOT/'parameters.json');cfg['revision']=HREV
    cfg['notes']=[x for x in cfg.get('notes',[]) if not x.startswith(('O23F:','O23G:','O23H:'))]
    cfg['notes'].append('O23H: every round connector checked at both end faces; full flat adapters and local integrated carrier heads; 42 rods total, at most three per neighbouring module. Named-feature recomposition removes obsolete subtraction membranes. Physical tests pending.')
    put(CFG,cfg)
    shutil.copy2(HROOT/'assembly.npz',B/'assembly.npz');shutil.copy2(HROOT/'assembly.json',B/'assembly.json')
    for path in (HROOT/'verification').glob('*.json'):shutil.copy2(path,B/'verification'/path.name)
    shutil.copytree(HROOT/'harness',B/'harness',dirs_exist_ok=True)
    for path in (B/'harness').glob('*.md'):
        path.write_text(path.read_text(encoding='utf8').replace('O23G','O23H').replace(GHASH,digest),encoding='utf8')
    for name in ('end_faces','geometry_difference','wire_fixtures','daily_motion','edge_motion','fixed_interfaces'):
        shutil.copy2(HROOT/'export/verification'/(name+'.json'),B/'verification'/('export_H_'+name+'.json'))
    exports=read(HROOT/'export/repair.json');export_rows=[]
    for r in exports['rows']:
        entry=next(x for x in manifest['rows'] if x['id']==r['id'])
        export_rows.append(dict(r,review_3mf=(PUBLIC/entry['project']).relative_to(B).as_posix(),review_stl=(PUBLIC/entry['stl']).relative_to(B).as_posix()))
    put(B/'verification/export_formats.json',dict(revision=HREV,geometry_sha256=digest,rows=export_rows,stl_failures=[],native_print_slicing_verified=True,physical_print_tested=False))
    put(B/'design/end_face_revision.json',dict(revision=HREV,geometry_sha256=digest,baseline_geometry_sha256=GHASH,
        source_directory=HROOT.relative_to(B).as_posix(),manufacturing_release=False))
    summary=read(B/'DELIVERY.json');summary.update(revision=HREV,geometry_sha256=digest,manufacturing_release=False,
        connection_end_face_review=dict(status='digital_checks_passed',rods=42,printed_structures=24),
        current_print_package=PUBLIC.relative_to(B).as_posix(),old_G_print_package_superseded=True,
        H_changes=dict(end_faces_passed=True,functional_apertures_passed=True,wire_seats=33,wire_channels=8,daily_poses=408,transition_poses=114,physical_strength_verified=False))
    put(B/'DELIVERY.json',summary)
    writecsv(B/'连接杆数量表.csv',['部位','连接对象','连接杆数','上限'],[dict(部位=NAMES.get(r['part'].split('/',1)[1],r['part']),连接对象=k,连接杆数=v,上限=3) for r in read(HROOT/'physical_rod_count.json')['rows'] for k,v in r['counts'].items()])
    writecsv(B/'连接截面筛查.csv',['部位','安装面编号','截面筛查mm2','说明'],[dict(部位=NAMES.get(r['body'],r['body']),安装面编号=r['land'],截面筛查mm2=round(r['conservative_cut_area_mm2'],2),说明='几何细颈筛查；不是实测承载能力') for r in read(HROOT/'load_paths.json')['rows']])
    text=f'''# O23H：连接杆端面与安装座复查

用户指出的大腿髋端侧向搭接问题成立。原检查验证了实体连通、外壁端覆盖和连接截面，却没有把关节端的完整端面贴合作为必过条件。本轮已补上该检查，并检查全身 24 个结构件、42 根连接杆。

大腿髋端改为完整平面底座与圆形承接部，杆端埋入承接部。其他薄安装座采用完整底座或局部一体加厚的承接头；保留安装孔，并对五金和转动件设置功能避让。杆身不再靠削缺来避让。骨盆移除两根冗余支撑，总杆数 44 → 42；单个相邻模块仍不超过 3 根。

全部杆两端使用独立承接实体检查端面及前后截面覆盖（最低 98%）。全部原安装区完成细颈筛查，最小指标 {min(r['conservative_cut_area_mm2'] for r in read(HROOT/'load_paths.json')['rows']):.2f} mm²。外壁保持连续、左右对称；深部安装连接仍有适配原偏置五金的局部差异，详见对称性报告，不宣称整件内部完全镜像。

408 个日常姿态和 114 个过渡姿态的必检相邻干涉为零。原安装孔、33 个布线固定座、8 条通道及 46 路五芯布线规划复查通过；保持原 UE 比例、髋中心和 706.26 mm 高度。背板拆出与细工具进入检查通过，靠近 XIAO 的一颗螺钉继续需要直径 3 mm 的细工具。

32 个 STL 全部单实体、封闭、面朝向一致。32 个 A1 mini / PLA 3MF 已重新切片并完成支撑与孔槽净空检查。导出数值清理不进行全局补洞或体素重建；实际导出网格也重新检查连接、布线和动作。

这是数字验证结果。PLA 层间强度、持姿、反复摆动及支撑拆除仍需实物试打确认。

- [完整装配预览](preview/index.html)
- [本轮 A1 mini 打印包](a1mini_pla_O23H/index.html)
- [端面检查](verification/connection_end_faces.json)
- [截面筛查](连接截面筛查.csv)
- [支撑、切片与文件清单](a1mini_pla_O23H/manifest.json)

先试打左大腿 S19、左前臂 S18，再试左锁骨内外段 S15/S10 和骨盆 S13。O23G 的旧打印包已被本版替代。

几何 SHA-256：`{digest}`。
'''
    for name in ('DESIGN.zh-CN.md','CONNECTION_END_FACES.zh-CN.md'):(B/name).write_text(text,encoding='utf8')
    (B/'SMOOTH_CONNECTIONS.zh-CN.md').write_text('# 当前版本 O23H\n\n已完成连接两端及安装座复查，见 [O23H 说明](CONNECTION_END_FACES.zh-CN.md)。旧 O23G 说明保存在历史快照中。\n',encoding='utf8')
    for name in ('index.html','README.zh-CN.md'):
        path=B/'a1mini_pla_optimized'/name
        if path.exists():
            old='结构复查进行中：G 版有部分连接端面未坐实，暂缓使用此包开始新的打印。正在修订连接及对应打印文件。'
            path.write_text(path.read_text(encoding='utf8').replace(old,'此 G 版已被 O23H 替代，请使用同级 a1mini_pla_O23H 目录中的新打印包。'),encoding='utf8')
    import present_revo23 as view
    view.B=B;view.REV=HREV;view.main();update_html(B/'preview/index.html',True)
    # Preserve the source template's version so later regeneration stays current.
    source=H/'cad/revO23/web/index.html';update_html(source,True)
    archive=B/'exports/O23H_A1mini_PLA_3MF.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in PUBLIC.rglob('*'):
            if path.is_file():z.write(path,path.relative_to(PUBLIC).as_posix())
    put(B/'verification/O23H_release.json',dict(revision=HREV,geometry_sha256=digest,archive=archive.relative_to(B).as_posix(),archive_sha256=sha(archive),
        digitally_verified=True,manufacturing_release=False,physical_tested=False))
    put(HROOT/'WORK_IN_PROGRESS.json',dict(status='digitally_verified_and_published',revision=HREV,geometry_sha256=digest,physical_tested=False))
    print('PUBLISHED O23H',digest,archive,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['review','publish']);a=ap.parse_args()
    review() if a.mode=='review' else publish()
