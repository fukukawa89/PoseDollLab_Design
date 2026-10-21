"""Publish the checked I design separately from unfinished print-process trials."""
from finish_revo23_i import *

def publish_review():
    previous.HROOT=IROOT;previous.HREV=IREV;previous.GHISTORY=IHISTORY
    digest=previous.gates(False)
    for file in ('external_contours.json','harness/routing_plan.json'):
        r=read(IROOT/file);assert r['geometry_sha256']==digest
    assert read(IROOT/'external_contours.json')['passed']
    exports=read(IROOT/'export/repair.json')['rows'];assert len(exports)==32
    export_hash=hashlib.sha256(json.dumps({r['key']:r['stl_sha256']for r in exports},sort_keys=True).encode()).hexdigest()
    checks=('smooth_connections','continuous_walls','physical_rod_count','end_faces','fixed_interfaces','geometry_difference','wire_fixtures','daily_motion','edge_motion')
    for name in checks:
        r=read(IROOT/'export/verification'/(name+'.json'))
        assert r['passed']and r['geometry_sha256']==digest and r['export_set_sha256']==export_hash,name
    for r in exports:
        path=IROOT/r['staged_stl'];assert sha(path)==r['stl_sha256']
        m=trimesh.load(path,process=True);assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    assert sha(IROOT/'profiles/device_profile.json')==sha(IHISTORY/'profiles/device_profile.json')
    assert read(IROOT/'detail_scenes.json')['export_manifest_sha256']==sha(IROOT/'export/repair.json')
    previous.bind_review(digest)
    unified=summary(digest);detail_page(digest,unified)
    # Every selected native project must refer to the current STL and current guard.
    native={};trials=[]
    for e in exports:
        spec=read(IROOT/'print/candidates'/(e['id']+'.json'));assert spec['stl_sha256']==e['stl_sha256']
        valid=[]
        for file in (IROOT/'print/bambu'/e['id']).glob('*/checked_result.json'):
            r=read(file);input_path=IROOT/r['source_project']
            if not input_path.is_file() or not (IROOT/r['project']).is_file():continue
            if sha(input_path)!=r['source_sha256']or sha(IROOT/r['project'])!=r['project_sha256']:continue
            if read(input_path.parent/'input.json')['stl_sha256']!=e['stl_sha256']:continue
            if r['clearance']['guard_sha256']!=sha(IROOT/'print/guards_v5'/(e['id']+'.npz')):continue
            valid.append(r)
        good=[r for r in valid if r['passed']]
        if good:native[e['id']]=min(good,key=lambda r:r['support_g'])
        assert valid,e['id']
        best=native.get(e['id'])or min(valid,key=lambda r:(not r['clearance']['passed'],not r['caps']['passed'],len(r['islands']['external_new_islands'])))
        trials.append(best)
    pending=[r['id']for r in exports if r['id']not in native]
    put(IROOT/'print/results.json',dict(geometry_sha256=digest,rows=trials,passed=not pending,pending_ids=pending,verified_count=len(native)))
    target=B/'stl_O23I_review';target.mkdir(exist_ok=True);(target/'stl').mkdir(exist_ok=True)
    rows=[]
    for e in exports:
        dst=target/'stl'/Path(e['staged_stl']).name;shutil.copy2(IROOT/e['staged_stl'],dst)
        nr=native.get(e['id']);rows.append(dict(e,review_stl=dst.relative_to(B).as_posix(),
            review_3mf=(IROOT/nr['project']).relative_to(B).as_posix()if nr else None,
            native_print_verified=bool(nr),physical_tested=False))
    manifest=dict(revision=IREV,geometry_sha256=digest,export_set_sha256=export_hash,rows=rows,stl_failures=[],
        native_print_slicing_verified=not pending,print_verified_count=len(native),print_pending_ids=pending,physical_print_tested=False)
    put(target/'manifest.json',manifest)
    status=f'{len(native)}/32 件打印工程通过完整复核；待复核：'+', '.join(pending)
    (target/'README.zh-CN.md').write_text(f'''# O23I 设计评审 STL

32 件 STL 均为封闭、单一实体，已对实际导出模型重新检查连接端面、安装孔、布线和相邻动作。几何：`{digest}`。

{status}。

本目录是设计评审模型，不是已经完成验证的全套 A1 mini 打印发布包。待复核项涉及局部悬空起始路径、支撑进入孔槽或临时剥离片间距。不要把之前 H 版的支撑工程直接用于 I 版零件。H 版历史文件保留。

已通过项目的 3MF 草案可从网页单独打开；实际强度、拆支撑和重复运动均未完成实物试验。
''',encoding='utf8')
    trs=[]
    for r in rows:
        name=NAMES.get(r['key'].split('/',1)[1],r['key'])
        link=f'<a href="../{r["review_3mf"]}">已通过数字复核的 3MF 草案</a>'if r['native_print_verified']else'打印支撑待复核'
        trs.append(f'<tr><td>{r["id"]}</td><td>{html.escape(name)}</td><td><a href="stl/{Path(r["review_stl"]).name}">封闭 STL</a></td><td>{link}</td></tr>')
    page='<!doctype html><meta charset="utf-8"><link rel="icon" href="data:,"><title>O23I STL 与打印复核状态</title><style>body{max-width:1100px;margin:40px auto;padding:20px;font:16px/1.7 system-ui;color:#253b40;background:#f4f3ef}td,th{padding:10px;border-bottom:1px solid #ccc;text-align:left}table{width:100%;background:white}a{color:#087774}</style>'
    page+=f'<h1>O23I · STL 与打印复核状态</h1><p>32 件导出模型封闭，连接、孔槽、布线及动作检查通过。</p><p>{status}。</p><p>本页为设计评审交付。完整新版 3MF 打印包尚未发布；已通过数字复核的单件仍需实物试打。</p><p><a href="../preview/index.html">完整人偶</a> · <a href="../verification/user_review_I/index.html">修改前后对照</a> · <a href="../exports/O23I_STL_review.zip">32 件评审 STL 压缩包</a></p><table><tr><th>编号</th><th>部件</th><th>导出</th><th>打印状态</th></tr>'+''.join(trs)+'</table>'
    (target/'index.html').write_text(page,encoding='utf8')
    cfg=read(IROOT/'parameters.json');cfg['revision']=IREV;put(CFG,cfg)
    for name in ('assembly.npz','assembly.json'):shutil.copy2(IROOT/name,B/name)
    for p in (IROOT/'verification').glob('*.json'):shutil.copy2(p,B/'verification'/p.name)
    for name in ('external_contours','unified_contours'):shutil.copy2(IROOT/(name+'.json'),B/'verification'/(name+'.json'))
    shutil.copytree(IROOT/'harness',B/'harness',dirs_exist_ok=True)
    for name in checks:shutil.copy2(IROOT/'export/verification'/(name+'.json'),B/'verification'/('export_I_'+name+'.json'))
    put(B/'verification/export_formats.json',manifest);put(B/'verification/print_I_status.json',read(IROOT/'print/results.json'))
    delivery=read(B/'DELIVERY.json');delivery.update(revision=IREV,geometry_sha256=digest,current_print_package=None,
        previous_print_package='a1mini_pla_O23H',current_stl_package='stl_O23I_review',manufacturing_release=False,
        I_changes=dict(unified_mounts=25,structures_inspected=24,rods=42,wire_seats=33,wire_channels=8,daily_poses=408,transition_poses=114,
            stl_verified=32,native_print_verified=len(native),print_pending_ids=pending,physical_strength_verified=False))
    put(B/'DELIVERY.json',delivery)
    doc=f'''# O23I：固定底座的连续外形

前版多数固定连接已经是同一打印实体，但安装座、加厚头与杆根的外轮廓仍呈现层叠台阶。此次检查全身 24 个结构件，重点重整 25 处固定底座，并整理外壁连接脚和扎带座根部。髋端—腰部的安装座与杆根连成连续斜面和圆角过渡；没有新增独立打印件或五金。

保留 H 版承力核心、42 根连接杆，以及单一相邻模块最多 3 根杆的限制。安装孔、活动关节、可拆盖板和布线槽仍需保留。人体外壁与指部轮廓不变；偏置五金造成的局部内部差异保留。新增实体体积约 127.24 cm³，实际增重取决于切片壁层及填充；不是实心质量估算。

设计与实际导出 STL 均通过端面承接、原安装区保留、孔槽、布线与动作复查。47 个安装区的细颈筛查通过，最小几何截面指标为 22.52 mm²，此数值不是实测承载能力。33 个布线座、8 条通道、46 路五芯线的布线方案保留。408 个日常姿态与 114 个过渡姿态必检相邻干涉为零。身高约 706.26 mm，UE 比例、髋中心和设备配置不变。

32 件 STL 为封闭单实体。对数值重合面采用有界精度清理；腰部还移除了一个体积 0.0000203 mm³、距离主体不足 0.03 mm 的数值碎片，保存了独立记录；没有全局补洞或体素重建。其余几何偏差、连接、孔槽及动作均在实际导出模型上重新核对。

打印状态：{status}。尚未发布完整 I 版 A1 mini / PLA 3MF 打印包；这些待复核项主要涉及局部悬空路径、孔槽内支撑及剥离片间距。已通过的单件工程可在交付页查看。实物强度和拆支撑未验证。

- [完整人偶预览](preview/index.html)
- [修改前后与全身细节](verification/user_review_I/index.html)
- [STL 与打印复核状态](stl_O23I_review/index.html)
- [全身处理清单](verification/unified_contours.json)

几何 SHA-256：`{digest}`。
'''
    for name in ('UNIFIED_MOUNTS.zh-CN.md','DESIGN.zh-CN.md'):(B/name).write_text(doc,encoding='utf8')
    def page_status(path):
        s=path.read_text(encoding='utf8').replace('O23H','O23I').replace('端面坐实，<br>连接复查。','底座一体，<br>外形连贯。')
        a=s.index('<p class="intro">');b=s.index('</p>',a)+4
        s=s[:a]+'<p class="intro">检查全身 24 个结构件，整理固定底座与杆根的层叠外形。连接、布线、相邻动作和实际 STL 已复查。</p>'+s[b:]
        s=s.replace('32 件 STL 与切片验证通过 · 实物待试打',f'32 件 STL 封闭 · {len(native)}/32 件打印工程复核通过')
        s=s.replace('a1mini_pla_O23I','stl_O23I_review').replace('O23I STL、切片验证与下载','O23I STL 与打印复核状态')
        s=s.replace('user_review_H','user_review_I').replace('端面底座与全身连接细节','连续底座修改前后对照')
        s=s.replace('打开此部位的 3MF 评审几何','打开此部位已通过数字复核的 3MF 草案')
        path.write_text(s,encoding='utf8')
    page_status(H/'cad/revO23/web/index.html')
    import present_revo23 as view
    view.B=B;view.REV=IREV;view.main()
    detail=B/'verification/user_review_I/index.html';s=detail.read_text(encoding='utf8').replace('../../a1mini_pla_O23I/index.html','../../stl_O23I_review/index.html').replace('配套打印文件','STL 与打印复核状态')
    detail.write_text(s,encoding='utf8')
    archive=B/'exports/O23I_STL_review.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED)as z:
        for p in target.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(target.parent))
    with zipfile.ZipFile(archive)as z:assert z.testzip()is None
    put(IROOT/'WORK_IN_PROGRESS.json',dict(revision=IREV,status='design_review_published_print_validation_incomplete',geometry_sha256=digest,
        stl_verified=32,native_print_verified=len(native),print_pending_ids=pending,archive_sha256=sha(archive)))
    print('PUBLISHED DESIGN REVIEW',digest,'PRINT',len(native),'PENDING',pending,flush=True)

if __name__=='__main__':publish_review()
