"""Human-readable entry, blank measurement records, exact-file manifest and ZIP."""
from kit import *
import html,re,zipfile,shutil

STYLE='''body{max-width:1040px;margin:40px auto;padding:0 26px 70px;color:#243f36;background:#fafbf6;font:16px/1.8 "Segoe UI","Microsoft YaHei",sans-serif}h1{font-size:36px;line-height:1.3}h2{margin-top:42px;border-bottom:1px solid #d6dfd5;padding-bottom:8px}h3{margin-top:28px}a{color:#226d57}table{width:100%;border-collapse:collapse;font-size:14px;margin:20px 0}th,td{border:1px solid #d6dfd5;padding:9px 12px;text-align:left}th{background:#e8eee4}img{max-width:100%;border:1px solid #dbe4d8;border-radius:8px}code{background:#eaf0e7;padding:2px 5px}nav{display:flex;flex-wrap:wrap;gap:15px}small,.muted{color:#647567}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{background:#edf3e8;padding:18px;border-radius:10px}.card b{font-size:30px;display:block}.button{display:inline-block;background:#2b715a;color:white;text-decoration:none;padding:9px 17px;border-radius:7px;margin:6px 8px 6px 0}.note{border-left:4px solid #c09b5f;padding:12px 18px;background:#f3efdf}.hero{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:center}.hero img{border:0}.eyebrow{font-size:12px;letter-spacing:2px}@media(max-width:700px){.cards,.hero{grid-template-columns:1fr}body{padding:0 16px}h1{font-size:28px}table{display:block;overflow:auto}}@media print{body{margin:0;max-width:none;font-size:11pt;background:white}nav,.button{display:none}h2{break-after:avoid}img{max-height:140mm;object-fit:contain}tr{break-inside:avoid}}'''

def inline(t):
    t=html.escape(t)
    t=re.sub(r'!\[([^]]*)\]\(([^)]+)\)',r'<img alt="\1" src="\2">',t)
    t=re.sub(r'\[([^]]*)\]\(([^)]+)\)',lambda m:'<a href="'+m[2].replace('ASSEMBLY.zh-CN.md','ASSEMBLY.html').replace('TEST_PLAN.zh-CN.md','TEST_PLAN.html')+'">'+m[1]+'</a>',t)
    t=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',t);t=re.sub(r'`([^`]+)`',r'<code>\1</code>',t);return t
def mdhtml(text):
    lines=text.splitlines();out=[];i=0
    while i<len(lines):
        s=lines[i].strip();i+=1
        if not s:continue
        if s.startswith('#'):
            lev=len(s)-len(s.lstrip('#'));out.append(f'<h{lev}>'+inline(s[lev:].strip())+f'</h{lev}>')
        elif s.startswith('|'):
            rows=[s]
            while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i].strip());i+=1
            out.append('<table>')
            for j,r in enumerate(rows):
                if j==1 and re.fullmatch(r'[| :\-]+',r):continue
                tag='th' if j==0 else 'td';out.append('<tr>'+''.join(f'<{tag}>'+inline(c.strip())+f'</{tag}>' for c in r.strip('|').split('|'))+'</tr>')
            out.append('</table>')
        elif re.match(r'^(?:- |\d+\. )',s):
            ordered=bool(re.match(r'^\d',s));tag='ol' if ordered else 'ul';items=[s]
            while i<len(lines) and re.match(r'^(?:- |\d+\. )',lines[i].strip()):items.append(lines[i].strip());i+=1
            out.append('<'+tag+'>'+''.join('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',x))+'</li>' for x in items)+'</'+tag+'>')
        else:out.append('<p>'+inline(s)+'</p>')
    return '\n'.join(out)
def page(title,body):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><link rel="icon" href="data:,"><style>'+STYLE+'</style><body><nav><a href="START_HERE.html">打印入口</a><a href="tutorial/index.html">逐件动画教程</a><a href="preview/index.html">三维装配</a><a href="ASSEMBLY.html">装配手册</a><a href="TEST_PLAN.html">测试计划</a><a href="BOM.csv">采购清单</a><a href="PURCHASE_DELTA_O22.html">O22补购对照</a></nav>'+body+'</body></html>'
def writecsv(name,columns,rows):
    p=OUT/'test_records'/name;p.parent.mkdir(exist_ok=True)
    # Never overwrite physical observations added by the user on a future run.
    if p.exists():return
    with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.writer(f);w.writerow(columns);w.writerows(rows)

def reprint_pack():
    """Small, self-contained repair bundle; no obsolete STL included."""
    plan=next(p for p in json.loads((OUT/'printing/plates.json').read_text('utf8'))['plates'] if p['id']=='REPRINT_S2_1')
    check=json.loads((OUT/'verification/connections.json').read_text('utf8'))
    slices=json.loads((OUT/'verification/slicing.json').read_text('utf8'))
    sliced=next(p for p in slices['plates'] if p['id']==plan['id'])
    assert check['passed'] and check['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert sliced['passed'] and sliced['input_sha256']==sha(OUT/plan['file'])
    assert {p['id'] for p in plan['items']}=={'H04','H05','R04','R05'}
    names=[p['stl'] for p in plan['items']]+[plan['file'],'printing/REPRINT_S2_1.svg','images/S2_H04_comparison.png']
    blobs={n:(OUT/n).read_bytes() for n in names}
    readme='''O24C-T1-S2 四件重印包 / 2026-10-22

只重印 H04、H05、R04、R05，每件1个。
已排好的四件工程：printing/REPRINT_S2_1.3mf。
单件STL：stl_print/ 下同名文件。所有尺寸单位为mm。
A1 mini / 0.4mm喷嘴 / PLA / 0.12mm层高 / 5圈墙 / 100%填充 / 自动支撑。

H04/R04：原0.2mm高的薄边连接改为连续腹板。
四件均加宽锁轴螺母座，侧槽按六角螺母角部宽度开放。
其余22件基础打印件、12件备选件与全部五金沿用S1，不用整套重印。
清支撑后检查腹板、锁轴座和孔边，无独立晃动、裂纹或分层再组装。
原装配次序与预紧方式继续使用，不能用加大预紧掩盖支架晃动。

已检查名义连接几何、装配路径、活动干涉及离线切片；S2实物刚度、持姿和磨损仍待验证。
完整装配与测试文档在配套的 PoseDoll_O24C_T1_Print_Test_Kit.zip 中。
'''
    blobs['README.zh-CN.txt']=readme.encode('utf-8-sig')
    manifest={n:hashlib.sha256(blob).hexdigest() for n,blob in blobs.items()}
    blobs['MANIFEST.sha256.json']=json.dumps(dict(revision='O24C-T1-S2',files=manifest),indent=2).encode()
    target=OUT/'PoseDoll_O24C_T1_S2_Reprint_4_Parts.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for n,blob in blobs.items():z.writestr(n,blob)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in manifest.items())

def s3_reprint_pack():
    names=['stl_print/W06.stl','stl_print/W07.stl','printing/REPRINT_S3_1.3mf','printing/REPRINT_S3_1.svg','verification/S3_changes.json']
    blobs={n:(OUT/n).read_bytes() for n in names}
    blobs['README.zh-CN.txt']=('O24C-T1-S3 / 2026-10-23\n\n已采用 S2：只重印 W06、W07，各 1 件。使用 printing/REPRINT_S3_1.3mf。\nA1 mini / PLA / 0.4mm 喷嘴 / 0.12mm 层高 / 5圈墙 / 100%填充。\n修复衬片固定耳无法平直进入球窝的问题；入口朝球心开放，保留外侧螺母座和承压底。\nW04/W05 衬片、其余24件基础打印件和所有五金不变。H04/H05/R04/R05 仍须用此前 S2 版本。\n完整动画：完整套件 tutorial/index.html；先单独装好衬片与球窝，再包球，最后装导向肩螺钉。\n清除支撑后轻推试配，不掰弯固定耳，不用螺钉强拉。实际持姿和磨损仍待测试。\n').encode('utf-8-sig')
    manifest={n:hashlib.sha256(blob).hexdigest() for n,blob in blobs.items()}
    blobs['MANIFEST.sha256.json']=json.dumps(dict(revision=REVISION,files=manifest),indent=2).encode()
    target=OUT/'PoseDoll_O24C_T1_S3_Reprint_2_Parts.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for n,blob in blobs.items():z.writestr(n,blob)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in manifest.items())

def main():
    data=json.loads((OUT/'assembly.json').read_text('utf8'));plates=json.loads((OUT/'printing/plates.json').read_text('utf8'))['plates']
    for src,dest in [('ASSEMBLY.zh-CN.md','ASSEMBLY.html'),('TEST_PLAN.zh-CN.md','TEST_PLAN.html'),('PURCHASE_DELTA_O22.zh-CN.md','PURCHASE_DELTA_O22.html'),('HARDWARE_ALTERNATIVES.zh-CN.md','HARDWARE_ALTERNATIVES.html'),('REPRINT_S2.zh-CN.md','REPRINT_S2.html'),('REPRINT_S3.zh-CN.md','REPRINT_S3.html'),('TUTORIAL.zh-CN.md','TUTORIAL.html')]:
        (OUT/dest).write_text(page(dest.split('.')[0],mdhtml((OUT/src).read_text('utf-8-sig'))),encoding='utf8')
    reports={name:json.loads((OUT/'verification'/file).read_text('utf8')) for name,file in [('geometry','geometry.json'),('collisions','collisions.json'),('fasteners','fastener_stacks.json'),('assembly','assembly_checks.json'),('slicing','slicing.json'),('extrusion','extrusion_by_part.json'),('browser','browser.json'),('delivery','delivery.json'),('connections','connections.json')]}
    ext=json.loads((OUT/'verification/extrusion_by_part.json').read_text('utf8'))['plates'];ex={r['plate']:r for r in ext}
    tables=[]
    for category in ['replacement','basic','optional']:
        table='<h2>'+dict(replacement='重印盘：已有 S2 只选 S3 两件盘；S1 支架另选 S2 四件盘',basic='基础打印盘：首次制作完整套件',optional='备选配合件：按需要替换')[category]+'</h2><table><tr><th>打印盘</th><th>内容</th><th>预估耗时 / PLA</th><th>文件</th></tr>'
        for p in plates:
            group='replacement' if p.get('replacement',False) else ('optional' if p['optional'] else 'basic')
            if group!=category:continue
            t=ex[p['id']]['time_header'].split('total estimated time: ')[1];mat=ex[p['id']]['material_header'][0].split('=')[1].strip()
            table+='<tr><td>'+p['id']+'</td><td>'+', '.join(i['id'] for i in p['items'])+'</td><td>'+t+' / '+mat+' g</td><td><a href="'+p['file']+'">3MF 工程</a> · <a href="printing/'+p['id']+'.svg">编号盘位图</a></td></tr>'
        tables.append(table+'</table>')
    hero='''<p class="eyebrow">POSEDOLL LAB / O24C-T1 / 2026-10-23</p><div class="hero"><div><h1>关节试制，<br>从可装配开始。</h1><p>把预紧、锁固与拆检落实到三类独立样件。先用小样确认配合，再测持姿、活动范围与磨损。</p><a class="button" href="tutorial/index.html">打开逐件动画 · 188 步</a><a class="button" href="ASSEMBLY.html">查看装配手册</a></div><img src="images/kit.png" alt="H、R、W三套台架样件实际CAD"></div><div class="cards"><div class="card"><b>26 件</b>基础打印件 · 6 盘</div><div class="card"><b>981 姿态</b>名义几何干涉检查通过</div><div class="card"><b>待实测</b>持姿、磨损、PLA松弛</div></div><p class="note">这是可打印的台架试制套件。夹具为扳手和测量留了空间，不是完整 O24C 手臂的最终关节外形。使用 PLA / A1 mini 0.4 mm 配置，先做 P0 试配；备选件只替换对应编号。</p>'''
    other='''<h2>先做这三步</h2><ol><li>打印 P0，选轴承孔档位，检查球与衬片能平顺相对运动。</li><li>按采购清单备齐五金，再打印其余基础件；按装配手册装入金属螺母，最后微调预紧。</li><li>按测试计划先磨合、测力矩，再做 100 / 500 / 1000 次检查。填写空白记录表，不把数字验证当作实测值。</li></ol><p>离线切片使用 OrcaSlicer 2.4.2，已核对 11 盘（6 基础、3 备选、2 重印）、全部基础与备选件的实际挤出路径、摆放与零网格修复。估时和耗材为切片结果，含支撑；实际打印会受材料和机器设置影响。3MF 包含模型与可编辑配置；本包不提供发机 G-code。</p><h2>测试与核对文件</h2><ul><li><a href="TEST_PLAN.html">测试方法与判定目标</a> · <a href="test_records/specimens.csv">试件信息</a> · <a href="test_records/rom.csv">活动范围</a> · <a href="test_records/torque_wear.csv">持姿与磨损</a> · <a href="test_records/preload.csv">预紧调整</a></li><li><a href="BOM.csv">完整采购清单</a> · <a href="printing/scale_labels_A4.svg">1:1 刻度标签</a></li><li><a href="O24C_T1_kit.blend">可编辑 Blender 装配</a> · <a href="O24C_T1_kit.glb">GLB</a> · <a href="PRINT_PARTS.csv">打印零件索引</a></li><li><a href="verification/collisions.json">活动干涉结果</a> · <a href="verification/assembly_checks.json">插入方向与预紧行程</a> · <a href="verification/fastener_stacks.json">螺钉长度核对</a> · <a href="verification/slicing.json">切片检查</a></li></ul>'''
    stock='<p class="note"><strong>腕部继续采用 S1 现货接口。</strong>腕部使用 Ø2.5×6 / M2 肩螺钉；W01、W02、W04、W05、W06、W07 必须采用本包新版，不与旧D3版混装。M2垫圈净用量8片，导向座两片必须厚0.5。<a href="HARDWARE_ALTERNATIVES.html">查看变更与采购参数</a>。</p>'
    repair='<p class="note"><strong>此前 S2：支架结构修复。</strong>已打印过 S1 的，只重印 H04、H05、R04、R05，各 1 件。其余 22 件基础件、12 件备选件及五金不变。<a href="REPRINT_S2.html">查看修复细节与逐件检查</a>。</p><a class="button" href="printing/REPRINT_S2_1.3mf">四件重印工程 · A1 mini / PLA</a><a class="button" href="PoseDoll_O24C_T1_S2_Reprint_4_Parts.zip">四件重印包</a>'
    s3='<p class="note"><strong>当前版本 O24C-T1-S3：装配教程与腕部入口修正。</strong>已使用 S2 的，这次只需重印 W06、W07，各 1 件。H、R 与全部五金沿用；旧 S2 球窝不要强压衬片装入。<a href="REPRINT_S3.html">修复与重印说明</a> · <a href="printing/REPRINT_S3_1.3mf">两件重印工程</a> · <a href="PoseDoll_O24C_T1_S3_Reprint_2_Parts.zip">两件重印包</a>。</p>'
    face_update='<p class="note"><strong>教程更新：五金朝向版，无需重印。</strong>188 步已区分普通螺母与尼龙锁紧螺母；蓝色标尼龙圈，绿色标垫圈光滑面，新增端面箭头与翻面放大。<a href="tutorial/index.html#H-15">从 H 第 15 步继续</a> · <a href="TUTORIAL.html">查看使用说明</a>。</p>'
    (OUT/'START_HERE.html').write_text(page(REVISION+' · 打印与测试入口',face_update+s3+hero+stock+repair+''.join(tables)+other),encoding='utf8')
    reprint_pack()
    s3_reprint_pack()
    if '--prepare' in sys.argv:
        print('PREPARED PAGES; release checks still required',flush=True);return
    assert all(r['passed'] for r in reports.values()),[(k,v['passed']) for k,v in reports.items()]
    alternate=json.loads((OUT/'verification/hardware_alternatives.json').read_text('utf8'))
    assert alternate['passed'] and alternate['baseline_geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert alternate['verification_source_sha256']==sha(HERE/'hardware_alternatives.py')
    guide=json.loads((OUT/'verification/stock_guide_checks.json').read_text('utf8'))
    assert guide['passed'] and guide['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert guide['verification_source_sha256']==sha(HERE/'stock_guide_checks.py')
    assert reports['collisions']['geometry_sha256']==reports['geometry']['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert reports['browser']['geometry_sha256']==reports['delivery']['browser_geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    slice_lookup={r['id']:r for r in reports['slicing']['plates']}
    for p in plates:
        assert slice_lookup[p['id']]['input_sha256']==sha(OUT/p['file']),p['id']
        for item in p['items']:assert item['stl_sha256']==sha(OUT/item['stl']),item['id']
    assert reports['connections']['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert reports['connections']['verification_source_sha256']==sha(HERE/'connection_checks.py')
    with (OUT/'PRINT_PARTS.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['编号','名称','数量','STL','打印盘','说明'])
        for p in data['parts']:
            if p['printable']:w.writerow([p['id'],p['label'],1,p['stl'],next(plate['id'] for plate in plates if not plate['optional'] and p['id'] in [i['id'] for i in plate['items']]),p['note']])
    cases=[('H肩',.13),('H肘',.04),('R',.02),('W屈伸',.006),('W偏转',.006)]
    writecsv('specimens.csv',['试件ID','站位','打印日期','PLA品牌批次','层高mm','孔档位mm','衬片内Rmm','球径Xmm','球径Ymm','球径Zmm','轴承凹入负Ymm','轴承凹入正Ymm','室温C','转动件质量g','重心力臂mm','实际加载孔距mm','后处理','照片'],[["",c]+['']*16 for c,_ in cases])
    writecsv('torque_wear.csv',['试件ID','工况','累计循环','目标Nm','正向起动1Nm','正向起动2Nm','正向起动3Nm','反向起动1Nm','反向起动2Nm','反向起动3Nm','持续力矩Nm','持姿净载荷Nm','初始角deg','1min角deg','5min角deg','10min角deg','死区deg','非目标滚转deg','左闭合量mm','右闭合量mm','螺母记号变化','粉末划痕','裂纹分层','是否补偿预紧','补偿圈数','测量方法及自重修正','结论','照片'],[['',c,n,t]+['']*24 for c,t in cases for n in ['磨合后0',100,500,1000,'静置24h']])
    rom=[('H肩',x,0) for x in [-45,0,45,90,135,165]]+[('H肘',x,0) for x in [0,45,90,120,145]]+[('R',x,0) for x in [-85,-45,0,45,80]]+[('W',x,y) for x,y in [(-65,0),(0,0),(70,0),(0,-20),(0,30),(-65,-20),(-65,30),(70,-20),(70,30)]]
    writecsv('rom.csv',['试件ID','站位','目标主轴deg','目标腕偏转deg','预紧状态','实际主轴deg','实际腕偏转deg','达到','接触件或卡点','照片'],[['',s,x,y,condition,'','','','',''] for s,x,y in rom for condition in ['极小预紧','目标预紧']])
    writecsv('preload.csv',['试件ID','站位','时间','累计循环','螺母A相对初始圈数','螺母B相对初始圈数','左闭合量mm','右闭合量mm','调前起动力矩Nm','调后起动力矩Nm','紧固记号变化','原因','照片'],[['',c]+['']*11 for c,_ in cases])
    for p,dest in [(HERE,OUT/'source'),(H/'cad/revO24/arm.py',OUT/'source_dependencies/arm.py'),(ROOT/'scripts/verify_revo22_a1mini.py',OUT/'source_dependencies/verify_revo22_a1mini.py')]:
        if p.is_dir():
            dest.mkdir(exist_ok=True)
            for f in p.iterdir():
                if f.is_file():shutil.copyfile(f,dest/f.name)
        else:dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
    tutorial=json.loads((OUT/'verification/tutorial_coverage.json').read_text('utf8'))
    paths=json.loads((OUT/'verification/tutorial_paths.json').read_text('utf8'))
    s3report=json.loads((OUT/'verification/S3_changes.json').read_text('utf8'))
    browser_tutorial=json.loads((OUT/'verification/tutorial_browser.json').read_text('utf8'))
    stockpaths=json.loads((OUT/'verification/tutorial_paths_stock.json').read_text('utf8'))
    for r in [tutorial,paths,s3report,browser_tutorial,stockpaths]:assert r['passed'] and r['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert paths['steps_sha256']==sha(OUT/'tutorial/steps.json')
    assert stockpaths['steps_sha256']==sha(OUT/'tutorial/steps.json')
    assert browser_tutorial['steps_sha256']==sha(OUT/'tutorial/steps.json') and browser_tutorial['ui_source_sha256']==sha(OUT/'tutorial/tutorial.js')
    orientation=json.loads((OUT/'verification/tutorial_orientation.json').read_text('utf8'))
    assert orientation['passed'] and orientation['steps_sha256']==sha(OUT/'tutorial/steps.json')
    assert orientation['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    assert all(sha(OUT/'tutorial'/name)==digest for name,digest in browser_tutorial['ui_assets_sha256'].items())
    status=dict(revision=REVISION,stage='PRINTABLE_BENCH_PROTOTYPE_UNTESTED',printed_parts=26,optional_fit_parts=12,assembly_components=len(data['parts']),basic_plates=6,optional_plates=3,reprint_plates=2,reprint_parts=['W06','W07'],prior_S2_reprint_parts=['H04','H05','R04','R05'],tutorial_steps=188,tutorial_components=133,prior_revision_feedback='S1 H04 fixed plate wobbled during user printing; S2 physical verification pending.',nominal_poses=reports['collisions']['pose_count'],digital_checks_passed=True,physical_printed=False,physical_rom_verified=False,holding_torque_verified=False,wear_verified=False,compact_arm_manufacturing_release=False,source_reference_height_mm=560,geometry_sha256=sha(OUT/'assembly_meshes.npz'))
    status.update(tutorial_edition=tutorial['orientation']['edition'],tutorial_oriented_hardware=73,tutorial_update_requires_reprint=False)
    put(OUT/'STATUS.json',status)
    # Do not include Blender autosaves or Python caches in the delivered archive.
    files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.suffix not in ['.blend1','.pyc'] and (p.suffix!='.zip' or p.name in ['PoseDoll_O24C_T1_S2_Reprint_4_Parts.zip','PoseDoll_O24C_T1_S3_Reprint_2_Parts.zip']) and p.name!='MANIFEST.sha256.json' and '__pycache__' not in p.parts)
    put(OUT/'MANIFEST.sha256.json',dict(files={p.relative_to(OUT).as_posix():sha(p) for p in files}))
    target=OUT/'PoseDoll_O24C_T1_Print_Test_Kit.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files+[OUT/'MANIFEST.sha256.json']:z.write(p,p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('MANIFEST.sha256.json'))['files']
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in manifest.items())
    print(json.dumps(dict(zip=str(target),bytes=target.stat().st_size,files=len(files)+1,status=status),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
