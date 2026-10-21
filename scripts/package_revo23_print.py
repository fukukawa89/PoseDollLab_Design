"""Publish only native projects that pass frozen-model, bead and clearance checks."""
from audit_revo23_print import *
from o22_support_gcode import export_preview
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw,ImageFont
import shutil,html
import copy

PUB=B/'a1mini_pla_optimized'
NAMES={'S01':'右前脚掌','S02':'右握拳手','S03':'左前脚掌','S04':'左握拳手','S05':'右后脚掌','S06':'右小腿',
 'S07':'左后脚掌','S08':'左小腿','S09':'右锁骨外段','S10':'左锁骨外段','S11':'头部','S12':'腰部',
 'S13':'骨盆','S14':'胸廓','S15':'左锁骨内段','S16':'左上臂','S17':'左肘下段','S18':'左前臂','S19':'左大腿',
 'S20':'右锁骨内段','S21':'右上臂','S22':'右肘下段','S23':'右前臂','S24':'右大腿','C01':'背部控制盒','C03':'控制盒盖',
 'W01':'右腕 C14','W02':'右腕 C15','W03':'右腕 C01 传感器卡匣','W04':'右腕 C02 传感器卡匣','W05':'右腕 C01 磁铁座','W06':'右腕 C02 磁铁座'}

def seconds(project):
    with zipfile.ZipFile(project) as z:code=z.read('Metadata/plate_1.gcode').decode()
    t=re.search(r'total estimated time\s*[:=]\s*([^\n]+)',code)
    assert t,project
    return int(sum(float(n)*dict(d=86400,h=3600,m=60,s=1)[u] for n,u in re.findall(r'(\d+(?:\.\d+)?)\s*([dhms])',t.group(1))))

def pick():
    rows=[];missing=[]
    for f in sorted((OUT/'candidates').glob('*.json')):
        s=read(f);rr=[]
        for p in (OUT/'bambu'/s['id']).glob('*/checked_result.json'):
            r=read(p)
            if r.get('passed') and r.get('caps',{}).get('count') and (r['caps'].get('method_version')!=2 or any(r[k].get('path_classification_version')!=3 for k in ('caps','clearance','islands'))):
                r['caps']=cap_audit(r);r['clearance']=void_audit(r);r['islands']=starting_islands(r)
                r['passed']=all(r[k]['passed'] for k in ('native','clearance','islands','caps'));put(p,r)
            rr.append(r)
        valid=[r for r in rr if r.get('passed') and r['clearance']['passed'] and r['islands']['passed'] and r['native']['passed']]
        for r in valid:
            r['automatic_support_g']=r['support_g'];r['manual_support_nominal_g']=r.get('caps',{}).get('nominal_solid_mass_g',0.)
            r['support_g']+=r['manual_support_nominal_g'];r['model_g']-=r['manual_support_nominal_g']
            r['estimated_s']=seconds(B/r['project'])
            r['selection_score']=r['support_g']+25*r['metrics']['rod_verticality']+r['estimated_s']/25000
        if not valid:missing.append(s['id']);continue
        r=min(valid,key=lambda r:r['selection_score']);r['title']=NAMES[r['id'].split('-')[1]];rows.append(r)
    out=dict(rows=rows,missing=missing,passed=len(rows)==32,total_support_g=sum(r['support_g'] for r in rows),total_s=sum(r['estimated_s'] for r in rows))
    put(OUT/'native_selection.json',out);print('SELECT',len(rows),'missing',missing,flush=True);return out

def frozen_check(rows):
    lock=read(OUT/'source_lock.json')
    for file,digest in lock['files'].items():assert sha(CFG if file=='cad_parameters' else B/file)==digest,file
    regression=read(B/'verification/stl_regression.json');assert regression['passed']
    for name,r in regression['checks'].items():assert sha(B/r['report'])==r['sha256'] and read(B/r['report'])['passed'],name
    checks=[]
    for r in rows:
        spec=read(OUT/'candidates'/(r['id']+'.json'));stl=B/spec['source']['staged_stl']
        assert sha(stl)==lock['stls'][r['id']]==spec['stl_sha256']
        project=B/r['project'];assert sha(project)==r['project_sha256']==r['native']['project_sha256']==r['clearance']['project_sha256']==r['islands']['project_sha256']
        obj,s,rep=read_project(project);v,f=obj[r['id']];M=np.array(r['matrix']);local=(v-M[:3,3])@M[:3,:3]
        reference=trimesh.load(stl,process=True)
        err=max(cKDTree(reference.vertices).query(local)[0].max(),cKDTree(local).query(reference.vertices)[0].max())
        assert err<.0002 and len(f)==len(reference.faces),(r['id'],err)
        report,a=paths(project);half=a[:,8]/2+.02
        bad=(np.minimum(a[:,:2],a[:,3:5])-half[:,None]<0).any(1)|(np.maximum(a[:,:2],a[:,3:5])+half[:,None]>180).any(1)
        assert not bad.any(),r['id']
        assert s['printer_model']=='Bambu Lab A1 mini' and s['nozzle_diameter']==['0.4'] and s['filament_type']==['PLA']
        assert s['layer_height'] in ('0.16','0.12') and int(s['wall_loops'])>=4
        model=a[a[:,7]==0];assert abs(float(model[:,5].min())-float(s['initial_layer_print_height']))<.001
        assert abs(float(model[:,5].max())-float(v[:,2].max()))<.4
        rev=r.get('guard_revision',1);guarddir=OUT/(f'guards_v{rev}' if rev>1 else 'guards')
        assert sha(guarddir/(r['id']+'.npz'))==r['clearance']['guard_sha256']
        assert r.get('caps',{}).get('passed',True)
        if r.get('caps',{}).get('count'):
            assert all(r[k].get('path_classification_version')==3 for k in ('caps','clearance','islands'))
        checks.append(dict(id=r['id'],stl_sha256=sha(stl),project_sha256=sha(project),maximum_vertex_difference_from_stl_mm=float(err),
            print_bead_outside_bed=0,source_geometry_preserved=True,guard_revision=rev,source_guard_sha256=r['clearance']['guard_sha256'],
            external_starting_islands=0,functional_void_intrusion_layers=0,wire_intrusion_layers=0,native_repair_count=0,temporary_peel_caps=r.get('caps',{}),passed=True))
    return dict(source_lock=lock,source_motion_and_connection_checks=regression,rows=checks,passed=True,
        method='Exact frozen source hashes; native normal-part topology and rigid transform; STL vertex correspondence and triangle count; actual LINE_WIDTH including arc margin for bed, support/void and island checks. Physical print, removal and strength trials remain unperformed.')

def copy_one(r):
    rid=r['id'];source=B/r['project'];dst=PUB/'projects'/(rid+'_A1mini_PLA.3mf');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst)
    assert sha(dst)==r['project_sha256']
    previews=PUB/'paths';previews.mkdir(exist_ok=True)
    preview=previews/(rid+'.json')
    if not preview.exists() or read(preview)['gcode_sha256']!=r['gcode_sha256'] or (r.get('caps',{}).get('count') and read(preview).get('manual_caps',{}).get('classifier_version')!=3):
        if r.get('caps',{}).get('count'):export_caps_preview(B/r['project'],preview)
        else:export_preview(dst,preview)
    imagepath=PUB/'images'/(rid+'.png');imagepath.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(dst) as z:imagepath.write_bytes(z.read('Metadata/plate_1.png'))
    put(PUB/'verification'/(rid+'.json'),r)
    print('PACK',rid,flush=True)
    extra=f' 本盘另有{r["caps"]["count"]}片临时承托薄片，打印后随支撑取下。' if r.get('caps',{}).get('count') else ''
    return dict(id=rid,title=r['title'],note=note(rid)+extra,file=dst.relative_to(PUB).as_posix(),preview=preview.relative_to(PUB).as_posix(),
        support_g=r['support_g'],model_g=r['model_g'],brim_g=r['brim_g'],estimated_s=r['estimated_s'],image=imagepath.relative_to(PUB).as_posix(),project_sha256=r['project_sha256'],settings=r['settings'],temporary_peel_caps=r.get('caps',{}))

def export_caps_preview(project,dst):
    report,a=paths(project);report=copy.deepcopy(report);origin=np.floor(a[:,:6].reshape(-1,3).min(0));quantum=.01
    packed=np.c_[np.round((a[:,:6]-np.tile(origin,2))/quantum),a[:,6:8]].astype('<u2')
    binary=dst.with_suffix('.bin');binary.write_bytes(packed.tobytes())
    nominal=report['manual_caps']['nominal_solid_mass_g']
    for i,row in enumerate(report['classes']):
        lines=a[a[:,7]==i];row['segments']=len(lines);row['layers']=len(np.unique(lines[:,6])) if len(lines) else 0
        row['path_mm']=float(np.linalg.norm(lines[:,:3]-lines[:,3:6],axis=1).sum())
        if i in (0,1):
            delta=(-1 if i==0 else 1)*nominal;row['estimated_mass_g']+=delta
            row['filament_mm']+=delta/(1.24*math.pi*(1.75/2)**2/1000)
    report['segment_count']=len(a);report['binary']=dict(file=binary.name,record_bytes=16,dtype='8xuint16_le',fields=['x0','y0','z0','x1','y1','z1','layer','class'],origin_mm=origin,quantum_mm=quantum,bytes=binary.stat().st_size,sha256=sha(binary))
    report['description']='Actual extrusion paths. Geometrically identified temporary peel caps are colored as support. Their mass allocation uses nominal solid volume; G-code total mass is unchanged.'
    put(dst,report)

def note(rid):
    short=rid.split('-')[1]
    if short in ('S19','S24'):return '保留圆杆与宽底座；先剪开外侧支撑，再沿壳体开口分段取出，勿以髋端连接杆作撬点。优先验证连接根部层间强度。'
    if short in ('S18','S23','S17','S22'):return '重点检查腕端/肘端孔和内侧扎带槽；支撑分段从内侧开口拆出。装线后保留关节活动余量。'
    if short in ('S02','S04'):return '五指固定握拳；沿掌侧和腕部开口剪开支撑，避免拉拽指尖。核对拇指和掌背朝向。'
    if short.startswith('W'):return '先试孔轴、螺母、磁铁及传感器卡匣配合；薄夹臂附近用剪钳分段切除支撑，勿硬撬。'
    if short in ('S09','S10','S15','S20','S12','S13','S14'):return '从大开口逐段剪除支撑。先清理扎带入口和安装面，再试装原五金；不要沿连接杆方向掰折。'
    if short=='C01':return '控制盒开口朝向由工程固定；清理耳座附近支撑后试装盖板和线束入口。'
    if short=='C03':return '平放盒盖，无需自动支撑；冷却后取下并清理裙边，先试盒盖孔位。'
    return '保持工程中的方向和禁区。冷却后从外侧支撑根部逐段剪除，保留安装孔、扎带槽及连接杆根部。'

def duration(s):return f'{s//3600} 时 {(s%3600)//60} 分'

def write_site(sel,plates):
    template=H/'bench/revO22/a1mini_supports'
    for name in ('viewer.js','style.css'):shutil.copy2(template/name,PUB/name)
    baseline=read(OUT/'baseline.json');old=baseline['total_support_g'];new=sel['total_support_g'];reduction=(1-new/old)*100
    table=''.join(f'<tr><td><a href="?plate={p["id"]}">{p["id"]}</a></td><td>{p["title"]}</td><td>{duration(p["estimated_s"])}</td><td>{p["model_g"]+p["support_g"]+p["brim_g"]:.1f} g</td><td>{p["support_g"]:.2f} g</td><td><a href="{p["file"]}" download>3MF</a></td></tr>' for p in plates)
    index=f'''<section class="notes"><p><a class="button" href="../exports/O23G_A1mini_PLA_optimized_3MF.zip" download>下载32件3MF工程包</a>　<a href="README.zh-CN.md">打印与拆除说明</a>　<a href="orientation_atlas.jpg">全部摆放方向</a></p><p>32个单件盘 · 原模型保持不变 · 支撑由原验证配置的 {old:.1f} g 降至 {new:.1f} g（减少 {reduction:.1f}%）。支撑质量按实际路径估算，原方案与新方案切片引擎/壁层设置不同，属于整套方案比较。</p><p><strong>先试打：</strong>右腕 W01–W06 → 右肘 S22、右前臂 S23 → 左大腿 S19。试件通过后再打剩余结构件。</p><details><summary>全部32件：用时、耗材和工程</summary><div class="table-wrap"><table><thead><tr><th>编号</th><th>零件</th><th>预计用时</th><th>模型+支撑+裙边</th><th>支撑</th><th>工程</th></tr></thead><tbody>{table}</tbody></table></div></details></section>'''
    page=(template/'index.html').read_text('utf8');start=page.index('<!-- SUPPORT_PROJECT_INDEX_START -->');end=page.index('<!-- SUPPORT_PROJECT_INDEX_END -->')+len('<!-- SUPPORT_PROJECT_INDEX_END -->')
    page=page[:start]+index+page[end:];page=page.replace('O22','O23G').replace('../a1mini/index.html','../preview/index.html').replace('← 打印盘零件索引','← 返回人偶装配').replace('0.20 mm','0.16 mm')
    page=page.replace('先看清支撑，再打印','O23G · PLA 打印与支撑').replace('O23G · A1 mini 易拆支撑','O23G · A1 mini PLA 打印工程').replace('零件高度 ÷ 0.16 mm','零件高度 ÷ 常规层高')
    (PUB/'index.html').write_text(page,'utf8')
    rows={r['id']:r for r in sel['rows']}
    total_grams=sum(p['model_g']+p['support_g']+p['brim_g'] for p in plates)
    md=['# O23G · A1 mini PLA 打印工程','',f'本包含 **32 个单件盘3MF工程**，由 Bambu Studio02.08.02.61 实际切片并回读检查。本轮只优化打印方向、壁层与临时支撑，保留已验证的 O23G STL、装配、连接杆和布线几何。其余沿用的 O22F7 关节件继续使用原打印文件。','',
        f'与上一轮切片验证方案相比，支撑估算总量从 **{old:.1f} g** 降至 **{new:.1f} g**，减少 **{reduction:.1f}%**。新方案本体采用更多壁层；此处比较的是32件整套方案，不是只改变一种参数的实验。质量为打印层路径估算，开机清线/校准另计；用时来自切片器估算。','',
        f'这32件的模型、支撑与裙边合计约 **{total_grams:.1f} g**，预计打印 **{duration(sel["total_s"])}**。需另外预留清线、试打和重打耗材；这些数字不包含沿用的O22F7关节件。','',
        '## 打开方式与设置','',
        '将 projects/ 中所需的3MF在 Bambu Studio 中“作为项目打开”。保留打印方向、非打印支撑禁区和局部支撑区域，不要使用自动重新摆放。工程已包含实际切片路径；重新切片后应检查预览是否与本包一致。不同版本的支撑生成算法可能产生差异。','',
        '- 机型：Bambu Lab A1 mini；喷嘴0.4 mm；普通PLA；纹理PEI板。',
        '- 常规层高0.16 mm，部分细节件0.12 mm；首层0.20或0.24 mm，以逐件工程为准。主要结构5道壁，小腕件及盒盖4道壁；20% Gyroid填充；上下各5层。',
        '- 喷嘴220°C，纹理PEI板65°C，来自工程内 Generic PLA @BBL A1M 配置。结合实际PLA厂商建议与首件表现微调温度。',
        '- 外壁40 mm/s，内壁65 mm/s，首层20 mm/s；采用逐件选择的支撑方式与间隙，以各3MF保存值为准。',
        '- 支撑是打印后的临时废料，不是人偶新增的连接杆。外壳与相邻部件最多3根连接杆的设计限制保持不变。','',
        '## 先试打的顺序','',
        '| 顺序 | 试件 | 检查重点 |','|---|---|---|',
        '| 1 | W01–W06：右腕环件、传感器卡匣、磁铁座 | 原五金孔轴配合、卡匣插拔、磁铁座、支撑是否容易取出。使用实际传感器板/磁铁核对后再粘接。 |',
        '| 2 | S22右肘下段 + S23右前臂 | 肘/腕连接根部、安装面、33个布线座中的代表性扎带槽；接入线束并逐步转动，确认无绷紧和夹线。 |',
        '| 3 | S19左大腿 | 髋端连接圆杆及宽底座的层间强度、拆支撑时根部是否受损；再与沿用的髋部/膝部机构试装。 |',
        '| 4 | S09/S10锁骨外段、S14胸廓、C01/C03背盒 | 胸肩和背盒装配通道、螺丝工具空间、躯干活动与线束余量。 |','',
        '首件应检查断层、裂纹、明显翘曲、堵孔和槽内残料；用手逐步施加正常摆姿所需的力并复查连接根部。不要一次打印整套后才验证装配。数字层向筛选与增加壁层不能替代实物承载、摩擦保持和疲劳测试。','',
        '## 支撑拆除','',
        '待零件与热床冷却后，先去裙边，再从壳体大开口或外侧剪开支撑根部，把接触层分成小段取出。不要用连接圆杆、薄夹臂、孔壁或布线座作撬点。手部从掌侧和腕部开口处理，避免直接拉扯指尖。','',
        '小安装孔、扎带孔和布线槽设有非打印禁区；大开口装配腔内仍可能保留必要的可剪支撑。拆除后逐一检查入口和深处，确认没有残留再装五金或穿线。线材方案为5芯细多股软线，初选AWG30、单线外径≤0.7 mm；以现有布线计划为准，关节处保留活动回环。','',
        '若工程对象列表出现 `Temporary peel caps - REMOVE after printing`，这些是为细小倒角设置的临时承托薄片，打印后须随支撑一起去除。薄片与本体保持间隙，单独验证了起始支撑、孔槽避让和本体间隔。网页将薄片归入支撑颜色；其质量按实体体积估算，其他支撑按实际路径估算。','',
        '工程对象列表中的辅助项：`Keep holes and wiring clear` 是非打印的支撑禁区；`Local support contacts` 是非打印的局部支撑提示；`Temporary peel caps` 是要打印并在最后拆除的临时薄片。请保留这些设置再切片。','',
        '## 检查范围','',
        '32个工程均要求原STL哈希不变、正常打印部件单实体且封闭、切片器修复计数为0、床面范围合格；检查实际支撑线宽与受保护孔槽、实际模型新起始区域是否有前层或支撑承接。孔槽几何扫描与逐层路径检查有采样精度限制，不能代替实物通孔与拆除检查。局部支撑禁区和强制支撑都是非打印辅助对象，不更改正常打印部件。','',
        '原连接、布线和动作验证通过源文件哈希及STL刚体一致性继承：44条连接、33个布线座、8条线槽，408个日常姿态和114个过渡姿态。未做实物打印、静载/疲劳或线束反复弯折验证。','',
        '## 逐件清单','', '| 编号 | 名称 | 用时 | 本体g | 支撑g | 裙边g | 层高/首层/支撑顶隙mm | 拆除注意 |','|---|---|---|---:|---:|---:|---|---|']
    for p in plates:
        setting=p['settings'];md.append(f'| [{p["id"]}]({p["file"]}) | {p["title"]} | {duration(p["estimated_s"])} | {p["model_g"]:.2f} | {p["support_g"]:.2f} | {p["brim_g"]:.2f} | {setting["layer_height"]}/{setting["initial_layer_print_height"]}/{setting["support_top_z_distance"]} | {p["note"]} |')
    md+=['','## 文件与预览','', '`projects/`为可打开的原生3MF；`images/`为切片器保存的摆放缩略图；`paths/`为对应G-code的交互预览数据；`verification/`为源文件、网格、路径和孔槽核查记录。','', '双击3MF即可在Bambu Studio查看。网页预览需HTTP服务；例如在本目录运行 `python -m http.server 8240` 后打开 `http://127.0.0.1:8240/`。网页线条为挤出中心线，3MF中的切片路径为准。','']
    (PUB/'README.zh-CN.md').write_text('\n'.join(md),'utf8')
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
    atlas=Image.new('RGB',(1600,8*310),'#f4f5f2');draw=ImageDraw.Draw(atlas)
    for i,p in enumerate(plates):
        x=(i%4)*400;y=(i//4)*310;im=Image.open(PUB/p['image']).convert('RGBA');im.thumbnail((390,250));atlas.paste(im,(x+(400-im.width)//2,y),im)
        draw.text((x+12,y+250),p['id']+' '+p['title'],font=font,fill='#263b38');draw.text((x+12,y+280),f'支撑 {p["support_g"]:.1f}g · {duration(p["estimated_s"])}',font=small,fill='#52615c')
    atlas.save(PUB/'orientation_atlas.jpg',quality=92)
    dest=B/'exports/O23G_A1mini_PLA_optimized_3MF.zip'
    files=[p for p in PUB.rglob('*') if p.is_file() and p.name!='SHA256.json']
    put(PUB/'SHA256.json',{p.relative_to(PUB).as_posix():sha(p) for p in files})
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in sorted(PUB.rglob('*')):
            if p.is_file():z.write(p,'O23G_A1mini_PLA/'+p.relative_to(PUB).as_posix())
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    put(OUT/'package.json',dict(zip=dest.relative_to(B).as_posix(),sha256=sha(dest),projects=len(plates),total_support_g=new,baseline_support_g=old,support_reduction_percent=reduction,total_estimated_s=sel['total_s'],physical_print_tested=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--select',action='store_true');ap.add_argument('--publish',action='store_true');a=ap.parse_args()
    sel=pick()
    if a.publish:
        assert sel['passed'],sel['missing'];PUB.mkdir(exist_ok=True)
        verify=frozen_check(sel['rows']);put(PUB/'verification/release.json',verify)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:plates=list(pool.map(copy_one,sel['rows']))
        put(PUB/'manifest.json',dict(revision='O23G A1 mini PLA optimized',plates=plates,
            notes=['本包仅含本轮新增/修改的32件；其余O22F7关节件沿用原文件。','数字切片检查通过，实际拆支撑、孔轴配合和强度仍须首件验证。','每个3MF为单零件工程；作为项目打开，保留方向、支撑禁区和局部支撑。不要使用自动重新摆放。']))
        write_site(sel,plates)
        print('PUBLISHED CORE',len(plates),flush=True)
