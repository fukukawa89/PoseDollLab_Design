"""Build the O22F7 assembly tutorial from the released 14 native projects.
All manufacturing geometry is read-only. Historical assembly instructions supply
hardware and wiring; current instance addresses and body meshes supply the guide.
"""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import copy,hashlib,html,itertools,json,re,shutil,sys,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import build_revo22_assembly_guide as base

R=Path(__file__).resolve().parents[1]
B=R/'Hardware/PoseDoll44/bench/revO22'
F=B/'O22F7_PLA_Final'
G=F/'assembly/tutorials/assembly-o22'
WORK=B/'diagnostics/O22F7_20261016/assembly_update'
REV='O22F7-assembly-r2-20261016'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8')
def put(p,d):write(p,json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def H(r,t):a=np.eye(4);a[:3,:3]=r;a[:3,3]=t;return a
E=html.escape


def inventory():
    release=read(F/'manifest.json')
    old={f"{p['id']}-{i['number']:02}":i for p in read(B/'a1mini/manifest.json')['plates'] for i in p['items']}
    instances=[];plates=[];parts={}
    for p in release['plates']:
        plate={'id':p['id'],'project':p['project'],'items':[],'preview':f"images/plates/{p['id']}.png"}
        with zipfile.ZipFile(F/p['project']) as z:
            root=ET.fromstring(z.read('Metadata/model_settings.config'))
            native={o.find("metadata[@key='name']").get('value') for o in root.findall('object')}
        assert native=={i['object_name'] for i in p['items']},p['id']
        for i in p['items']:
            address=f"{p['id']}-{i['number']:02}";original=i['original_object_name'].split()[0]
            q=copy.deepcopy(i);q.update(address=address,plate=p['id'],project=p['project'],optional=i['optional_sample'],original_address=original)
            if not q['optional']:
                assert original in old and old[original]['id']==q['id']
                assert old[original]['part']==q['part'],(address,old[original]['part'],q['part'])
                assert q['part'] not in parts
                parts[q['part']]=q
            q['name_zh']=base.zh(q['part']);plate['items'].append(q);instances.append(q)
        plate['count']=len(plate['items']);plate['optional_count']=sum(x['optional'] for x in plate['items']);plates.append(plate)
    assert len(instances)==193 and len(parts)==186 and len(plates)==14
    assert len({x['address'] for x in instances})==193
    assert set(parts)==set(base.FIRST)
    steps=copy.deepcopy(base.STEPS)
    for s in steps:s['plates']=sorted({parts[k]['plate'] for k in s['parts']})
    for q in instances:q['first_use']=None if q['optional'] else base.FIRST[q['part']]
    base.PARTS=parts;base.STEPS=steps;base.OUT=G
    return release,plates,parts,instances,steps


class CurrentDoc(base.Doc):
    def img(self,url,caption,cls='diagram'):
        super().img(url,caption,cls)
        match=re.fullmatch(r'images/(S\d{2})\.png',url)
        if not match:return
        s=next(s for s in base.STEPS if s['step']==match[1])
        rows=[]
        for k in s['new_parts']:
            q=base.PARTS[k];pid=q['id']
            if pid in CHANGED:
                text=f"[{q['address']} / {pid} 转角与拆撑定位](../../../elbows/{pid}/index.html)：圆接头属于永久本体，保留。"
                if pid=='P095':text+='支撑 S01+S03 同步向下取出；S06 斜向外下方退出。先剪新增细齿，清理 H2/H4 的 T202、T203 孔内齿。'
                elif pid=='P073':text+='先剪新增细齿，S03 按绿色箭头斜向退出。'
                elif pid=='P051':text+='先剪新增两根细齿，S05 向下退出。'
                elif pid=='P002':text+='一处圆接头上的小避让面用于胸架运动空间，保持该形状。'
                rows.append(text)
            elif pid in EXCEPTIONS:rows.append(f"[{q['address']} / {pid} 拆撑图](../../../index.html?id={pid})：本件保留孔位可拆承托，先清理孔道、沉孔及螺母位，再装五金。")
        if rows:self.listing(rows)


def intro(plates,instances):
    d=base.D
    d.heading(1,'O22F7 人偶拼装教程','start')
    d.p('对应本包 **D01–D14 · PLA 最终版**。按 **打印盘 → 盘内编号 → 装配步骤 → 电路端口** 找件。左右按人偶自身区分。','lead')
    d.raw('<div class="hero-actions"><a class="button" href="#plates">查看当前 14 盘</a><a href="#find-parts">搜索零件与盘位</a><a href="../../../打印与拆撑.html">打印与拆撑</a><a href="ASSEMBLY.zh-CN.md">文字清单</a><button class="outline" onclick="window.print()">打印 / 保存 PDF</button></div>')
    d.p('教程修订：2026-10-16 · r2。盘图、盘位和三维打印件均取自 O22F7 最终文件。共 193 件：185 件装机件 + 1 件焊接量规 + 7 件可选小样。7 件小样已混排在 D 系列盘内，标有“小样”，不再额外装到人偶上。','note')
    d.p('打印盘号使用 D01–D14；S01–S26 是拼装步骤；A01–A14、B01–B16、C01–C16 是传感器电路端口。例如打印盘 D01 与电路端口 A01 没有盘号对应关系。','note')
    d.heading(2,'00 · 开始前先分袋、准备五金与电路','prepare')
    d.listing([
      '冷却取件后，按本页当前盘图装袋。完整标签示例：D01-01 / P095 / 左髋大腿下环。N003、N004、P013、P130 等型号会重复，使用完整 Dxx-nn 定位，再核对所属关节。',
      '先按本包拆撑图剪除黄色连接齿、取下橙色支撑鳍，保留蓝色永久本体。16 类零件仍有孔内或孔口承托；先清理螺钉通道、沉孔和螺母位，再安装五金。不扩大精配合孔来迁就错规格五金。',
      'P095、P073、P051 的新增细齿和退出方向见对应步骤的链接。转角圆接头是 O22F7 补强后的本体，不能当成支撑剪掉。',
      '工具：匹配螺钉头的内六角批头（轴肩螺钉为 3 mm）、卡尺、镊子、小尖嘴钳、剪钳、万用表、标签笔和软垫。磁铁防转胶与线束固线胶按材料说明完全固化。',
      '准备 48 块已焊五线并完成导通检查的传感板（46 使用 + 2 完整备件）、1 块中央成品板、1 块 XIAO，以及逐路标号的线束。供应方完成贴片、板端焊接和端子压接；装配时按端口插接。',
      '机械按 S01–S25，中央板按 S26。传感板可随关节安装，先不接电。推荐先完成左臂线束样段；在软垫上托住骨架，先装内部螺母和反力垫、调整摩擦，再关闭环或半壳。'],True)
    d.p('[本版拆撑说明与 16 类孔位承托清单](../../../打印与拆撑.html) · [逐件彩色拆撑视图](../../../index.html)。')
    d.heading(2,'01 · 从当前打印盘找到装配步骤','plates')
    d.p('盘图为最终零件、支撑鳍和细齿的俯视投影，位置与 3MF 一致；打印平台前沿在图下方。蓝色是本体，橙色是可拆支撑，黄色是连接齿。虚线框标出可选小样。点盘图可放大，点“打开 3MF”可打开该盘工程。')
    d.raw('<div class="step-jump">'+''.join(f'<a href="#plate-{p["id"]}">{p["id"]}</a>' for p in plates)+'</div>')
    d.raw('<div class="plate-grid">')
    for p in plates:
        d.raw('<article class="plate-card">')
        d.heading(3,f"{p['id']} · {p['count']} 件"+(f"（含 {p['optional_count']} 件小样）" if p['optional_count'] else ''),'plate-'+p['id'])
        d.img(p['preview'],f"{p['id']} · O22F7 实际盘位与形状；编号对应本盘清单",'plate-preview')
        d.p(f"[打开 {p['id']} PLA 3MF](../../../{p['project']})")
        d.raw('<details><summary>展开本盘取件清单与首次领用步骤</summary>')
        rows=[]
        for q in p['items']:
            use='可选小样 · 不装机' if q['optional'] else f"[{q['first_use']}](#{q['first_use']})"
            follow=[s['step'] for s in base.STEPS if q['part'] in s['parts'] and s['step']!=q['first_use']]
            if follow and not q['optional']:use+='；后续 '+ '、'.join(f'[{x}](#{x})' for x in follow)
            rows.append([f"[{q['address']} / {q['id']}](../../../index.html?id={q['id']})",q['name_zh'],use])
        d.table(['盘内编号 / 型号','零件','首次领用 / 后续连接'],rows)
        d.raw('</details></article>')
    d.raw('</div>')
    d.heading(3,'快速查找零件','find-parts')
    d.raw('<label class="search-label">零件、盘位或身体部位 <input id="part-search" type="search" placeholder="例如 P095、D01-01、左肩、S18"></label><p id="part-filter-state" role="status">显示 193 / 193 件</p><div class="part-search-results">')
    d.table(['盘位 / 型号','零件 / 原始键','领用步骤'],[[f"[{q['address']} / {q['id']}](#plate-{q['plate']})",q['name_zh']+' / `'+q['part']+'`','可选小样 · 不装机' if q['optional'] else f"[{q['first_use']}](#{q['first_use']})"] for q in instances])
    d.raw('</div>')
    d.p('XIAO 焊接间距量规在 S26 使用后取出，不装在人偶内。7 件可选小样：'+ '；'.join(q['address']+' / '+q['id'] for q in instances if q['optional'])+'。')
    base.hardware_and_recipes()


def plate_images(plates):
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
    head=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',27)
    small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
    scale=5;offset=44;size=180*scale
    cache={};proof=[]
    for p in plates:
        im=Image.new('RGB',(988,1030),'#f7f5ef');draw=ImageDraw.Draw(im)
        draw.text((44,13),f"{p['id']}   O22F7 PLA   /   {p['count']} 件",font=head,fill='#253f3d')
        draw.rectangle((offset,62,offset+size,62+size),fill='#e8eeea',outline='#819b95',width=2)
        for a in range(0,181,10):
            draw.line((offset+a*scale,62,offset+a*scale,62+size),fill='#d4e0d8')
            draw.line((offset,62+a*scale,offset+size,62+a*scale),fill='#d4e0d8')
        records=[]
        for q in p['items']:
            pid=q['id']
            if pid not in cache:cache[pid]=dict(np.load(F/f'parts/{pid}.npz'))
            n=cache[pid];rot=np.array(q['rotation_matrix']);trans=np.array(q['translation_mm'])
            tris=[];colors=[]
            for vk,fk,color in [('v','f',[67,129,166]),('fin_v','fin_f',[217,135,63]),('teeth_v','teeth_f',[240,200,77])]:
                t=(n[vk]@rot.T+trans)[n[fk]]
                if not len(t):continue
                normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm=np.maximum(np.linalg.norm(normal,axis=1),1e-20);light=.68+.32*np.abs(normal[:,2]/norm)
                tris.append(t);colors.append((light[:,None]*np.array(color)).astype(np.uint8))
            t=np.concatenate(tris);c=np.concatenate(colors)
            px=np.stack([offset+t[:,:,0]*scale,62+(180-t[:,:,1])*scale],axis=2)
            for ix in np.argsort(t[:,:,2].mean(axis=1)):
                draw.polygon([tuple(v) for v in px[ix]],fill=tuple(c[ix]))
            records.append({'address':q['address'],'id':pid,'npz_sha256':sha(F/f'parts/{pid}.npz'),'rotation_matrix':q['rotation_matrix'],'translation_mm':q['translation_mm'],'optional':q['optional']})
        # Number labels are added after all geometry so every address stays readable.
        for q in p['items']:
            b=q['bounds_mm'];x=offset+(b[0]+b[3])*.5*scale;y=62+(180-b[4])*scale
            if q['optional']:
                x0,x1=offset+b[0]*scale,offset+b[3]*scale;y0,y1=62+(180-b[4])*scale,62+(180-b[1])*scale
                for xx in np.arange(x0,x1,14):
                    draw.line((xx,y0,min(xx+8,x1),y0),fill='#b77940',width=2);draw.line((xx,y1,min(xx+8,x1),y1),fill='#b77940',width=2)
                for yy in np.arange(y0,y1,14):
                    draw.line((x0,yy,x0,min(yy+8,y1)),fill='#b77940',width=2);draw.line((x1,yy,x1,min(yy+8,y1)),fill='#b77940',width=2)
            label=f"{q['address']} {q['id']}"+(' 小样' if q['optional'] else '')
            tw=draw.textbbox((0,0),label,font=font)[2];x=max(offset,min(x-tw/2,offset+size-tw-4));y=max(64,min(y,940))
            draw.rounded_rectangle((x-3,y-2,x+tw+4,y+19),radius=3,fill='#ffffff',outline='#b77940' if q['optional'] else '#849c9c')
            draw.text((x,y),label,font=font,fill='#5f351a' if q['optional'] else '#183a48')
        draw.text((44,978),'平台前沿 / Y=0　　蓝：永久本体　橙：支撑鳍　黄：连接齿　虚线框：可选小样',font=small,fill='#344f4f')
        path=G/p['preview'];path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
        proof.append({'plate':p['id'],'image_sha256':sha(path),'projection':'orthographic top, +Y up; same rigid placement as final native project','items':records})
        print('PLATE_IMAGE',p['id'],flush=True)
    put(G/'evidence/plate_images.json',{'revision':REV,'plates':proof})


def scene(parts):
    old=read(base.H/'tutorials/assembly-o22/scene.json')
    raw=np.fromfile(base.H/'tutorials/full-doll-o22/geometry_universal.bin',dtype='<f4').reshape(-1,6)
    exports={x['id']:x for x in read(B/'print_batch/manifest.json')['rows']}
    meta=read(B/'mechanical/assembly_metadata.json')['meta']
    out=copy.deepcopy(old);out.pop('f5_note',None);out['meshes']={};chunks=[];first=0;seen={};proof=[]
    for o in out['objects']:
        key=o['label'];prev=old['meshes'][o['mesh']]
        if key in parts:
            q=parts[key];pid=q['id'];n=np.load(F/f'parts/{pid}.npz');d=read(F/f'design/{pid}.json');bed=exports[pid]['bed'];basis=np.eye(4)
            if pid=='N003':
                i=0 if '/C01_' in key else 1;z=np.eye(3)[i];x=np.array([0.,0.,-1 if i==0 else 1]);basis=H(np.c_[x,np.cross(z,x),z],z*16)
            basis[:3,1]*=1 if np.linalg.det(np.array(meta[key]['transform'])[:3,:3])>0 else -1
            transform=basis@np.linalg.inv(H(d['orientation']['matrix'],d['orientation']['source_translation_mm'])@H(bed['rotation'],bed['translation_mm']))
            v=n['v']@transform[:3,:3].T+transform[:3,3];f=n['f'].copy()
            if np.linalg.det(transform[:3,:3])<0:f=f[:,::-1]
            triangles=v[f];norm=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-25)
            arr=np.concatenate([triangles,np.repeat(norm[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4')
            bounds_delta=float(np.max(abs(np.array([v.min(0),v.max(0)])-np.array([prev['min'],prev['max']]))))
            assert bounds_delta<.02,(key,bounds_delta)
            # Verify the displayed triangles invert to the exact final print body, within float32 storage error.
            iv=np.linalg.inv(transform);back=arr[:,:3].astype(float)@iv[:3,:3].T+iv[:3,3];roundtrip=float(np.max(np.linalg.norm(back-n['v'][f].reshape(-1,3),axis=1)))
            assert roundtrip<.0001,(key,roundtrip)
            o.update(address=q['address'],name_zh=q['name_zh'],print_id=pid,project='../../../'+q['project'],body_revision='O22F7',part_url='../../../index.html?id='+pid)
            o.pop('original_address',None)
            proof.append({'part':key,'id':pid,'address':q['address'],'npz_sha256':sha(F/f'parts/{pid}.npz'),'print_to_owner':transform.tolist(),'triangle_count':len(f),'float32_roundtrip_max_mm':roundtrip,'old_preview_bounds_delta_mm':bounds_delta})
        else:arr=raw[prev['first']:prev['first']+prev['count']]
        stamp=hashlib.sha256(arr.tobytes()).hexdigest()[:24]
        if stamp not in seen:
            seen[stamp]=True;out['meshes'][stamp]={'first':first,'count':len(arr),'min':arr[:,:3].min(0).tolist(),'max':arr[:,:3].max(0).tolist()};first+=len(arr);chunks.append(arr)
        o['mesh']=stamp;m=out['meshes'][stamp];M=np.array(o['matrix']).reshape(4,4)
        corners=np.array(list(itertools.product(*zip(m['min'],m['max']))));world=corners@M[:3,:3].T+M[:3,3]
        o['bounds']=[world.min(0).tolist(),world.max(0).tolist()]
    assert len(proof)==185
    path=G/'geometry-o22f7.bin';path.write_bytes(np.concatenate(chunks).astype('<f4').tobytes())
    out.update(geometry_url='geometry-o22f7.bin',geometry_sha256=sha(path),revision=REV,scope='All 185 installed printed instances use the final O22F7 permanent body mesh. Hardware, electronics and assembly pose retain O22. No supports shown in the assembly scene; gauge is not installed.')
    put(G/'scene.json',out);put(G/'evidence/current_body_meshes.json',{'revision':REV,'installed_instances':185,'all_current_body_triangles':True,'rows':proof})
    print('SCENE',len(proof),'current printed bodies',path.stat().st_size,flush=True)


def html_page():
    template=(base.H/'tutorials/assembly-o22/index.html').read_text('utf8')
    before=template.split('<main>',1)[0];after=template.split('</main>',1)[1]
    before=before.replace('O22 · 按打印盘拼装人偶','O22F7 人偶拼装教程').replace('O22 / ASSEMBLY','O22F7 / ASSEMBLY r2').replace('../../bench/revO22/a1mini/index.html','#plates')
    after=after.replace('原始 O22 CAD · 装配位置识别','O22F7 当前打印本体 · 装配位置识别').replace('O22 · A1 mini · 2026-10-02 / 按已保存设计编写，保留首件实测状态。','O22F7 · 14 盘 PLA · 教程 r2 / 2026-10-16').replace('<script src="app.js">','<script src="app.js?v='+REV+'">')
    after=after.replace('<p id="view-part-info"></p>','<p id="view-part-info"></p><p><a id="view-part-print" hidden target="_blank">查看本件拆撑与打印形状 ↗</a></p>')
    body='\n'.join(base.D.h)
    replacements={
      '../../bench/revO22/a1mini/index.html':'#plates',
      '../full-doll-o22/index.html':'../../../index.html',
      '../../bench/revO22/PoseDoll_O22_Engineering_Package.zip':'engineering-files.html',
      '原 10 盘 3MF、编号图和打印说明':'本版 D01–D14 工程、实际盘图和取件清单',
      '整机 CAD、原有验收与工程资料':'O22F7 当前零件、支撑与转角修订',
      '版本：O22 / A1 mini 10 盘，2026-10-02。图示只展开零件帮助识别，不模拟真实插入轨迹；实际预装和穿装次序按文字步骤。教程包不重复包含全部打印模型和 KiCad 制造资料，请与已保存的两个原包一起使用。':'版本：O22F7 / PLA / D01–D14，教程 r2，2026-10-16。185 个装机打印件的三维形状取自当前最终本体网格，26 张位置图同步更新。展开视图用于识别，不代表真实插入轨迹；预装和穿装按文字。五金、电路端口与机械功能保持。实物装配、电子首件和标定仍按验收表记录。',
      '查看本步可旋转 CAD / 单件识别 ↗':'查看本步三维装配 / 单件识别 ↗',
    }
    md='\n'.join(base.D.m)
    for a,b in replacements.items():body=body.replace(a,b);md=md.replace(a,b)
    write(G/'index.html',before+'<main>'+body+'</main>'+after)
    write(G/'ASSEMBLY.zh-CN.md',md)
    css=(base.H/'tutorials/assembly-o22/style.css').read_text('utf8')
    css+='\n.plate-preview{max-width:100%}.part-search-results{max-height:460px;overflow:auto}.part-search-results .table-wrap{margin-top:0}.part-search-results th{position:sticky;top:0}#view-part-print{font-size:12px}.plate-card table{min-width:390px}@media print{.part-search-results{max-height:none;overflow:visible}.plate-preview{max-width:400px}#part-search,#part-filter-state{display:none}}\n'
    write(G/'style.css',css)
    js=(base.H/'tutorials/assembly-o22/app.js').read_text('utf8')
    js=js.replace("json('guide-data.json'),json('scene.json')",f"json('guide-data.json?v={REV}'),json('scene.json?v={REV}')")
    js=js.replace('原始 CAD 已载入 · 仅作装配位置与单件识别','O22F7 当前打印本体已载入 · 装配位置与单件识别')
    js=js.replace("function updateStep(){", "function updateStep(){ $('#view-part-print').hidden=true;")
    marker="const p=guide.parts[state.part];"
    js=js.replace(marker,marker+"$('#view-part-print').hidden=!p;if(p)$('#view-part-print').href='../../../index.html?id='+p.id;")
    js+="\n$('#part-search').oninput=e=>{const q=e.target.value.trim().toLowerCase();let count=0;document.querySelectorAll('.part-search-results tbody tr').forEach(r=>{r.hidden=!r.textContent.toLowerCase().includes(q);if(!r.hidden)count++});$('#part-filter-state').textContent=`显示 ${count} / 193 件`};\n"
    write(G/'app.js',js)
    write(G/'engineering-files.html','<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>电子生产资料</title><link rel="stylesheet" href="style.css"><main><h1>电子生产资料</h1><p>Gerber、钻孔、坐标和原生 PCB 文件继续使用已保存的 PoseDoll_O22_Engineering_Package.zip 中的 manufacturing 目录。O22F7 的打印修订没有改动电路。</p><p>本打印包已附带 <a href="../../bench/revO22/manufacturing/electronic_bom.tsv">电子 BOM</a>、<a href="../../bench/revO22/manufacturing/RFQ.zh-CN.md">加工要求</a>和 <a href="../../bench/revO22/physical_tests/ACCEPTANCE.zh-CN.md">首件验收表</a>。当前打印件请使用本包 D01–D14 工程。</p><p><a href="index.html#electronics">返回电路安装</a></p></main></html>')
    write(G/'external-files.html','<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O22F7 打印文件</title><link rel="stylesheet" href="style.css"><main><h1>O22F7 · 14 盘 PLA</h1><p><a href="index.html#plates">返回当前盘图与取件清单</a> · <a href="../../../打印与拆撑.html">打印与拆撑</a></p><ul>'+''.join(f'<li><a href="../../../projects/D{i:02}_O22F7_PLA_final.3mf">D{i:02} · PLA 最终工程</a></li>' for i in range(1,15))+'</ul></main></html>')


def build():
    global CHANGED,EXCEPTIONS
    release,plates,parts,instances,steps=inventory()
    CHANGED=set(release['body_changed_from_F5_type_ids']);EXCEPTIONS=set(release['restored_original_support_type_ids'])
    base.D=CurrentDoc()
    base.part=lambda k:f"[盘 {parts[k]['address']} · {parts[k]['id']}（{base.zh(k)}）](../../../index.html?id={parts[k]['id']})"
    base.diagrams();intro(plates,instances);base.joint_steps();base.electronics();base.commissioning()
    data={'schema':'POSEDOLL-O22F7-ASSEMBLY-GUIDE/2','revision':REV,'steps':steps,'plates':plates,'instances':instances,'parts':parts,'first_use':base.FIRST,'routes':base.ROUTES,'hardware':base.STOCK,'pin_order':base.ROUTING['pin_order'],'source_plate_manifest_sha256':sha(F/'manifest.json'),'main_instances':186,'on_doll_instances':185,'optional_instances':7,'native_project_sha256':{p['project']:sha(F/p['project']) for p in plates}}
    put(G/'guide-data.json',data)
    plate_images(plates);scene(parts);html_page()
    write(F/'assembly/README.zh-CN.md','# O22F7 人偶拼装教程 · r2\n\n打开 tutorials/assembly-o22/index.html。当前 D01–D14 盘图、193 件对照、26 步说明与 O22F7 本体三维视图已同步。可选 7 件小样不装机；电路 A/B/C 端口与 D 打印盘分开标识。需要旋转三维时，使用完整打印包根目录的“打开3D与安装说明.cmd”。\n')
    # Legacy plate-folder entry points now lead to the current guide; no obsolete A plate drawings ship as current references.
    legacy=F/'assembly/bench/revO22/a1mini'
    put(legacy/'manifest.json',{'revision':REV,'source':'../../../../manifest.json','plates':plates})
    write(legacy/'README.zh-CN.md','本版使用 D01–D14。查看 [当前盘图与取件清单](../../../tutorials/assembly-o22/index.html#plates)。\n')
    for p in (legacy/'previews').glob('*.svg'):
        assert p.resolve().is_relative_to(F.resolve())
        if re.fullmatch(r'(A\d{2}|T01)\.svg',p.name):p.unlink()
    for path in [F/'index.html']:
        s=path.read_text('utf8').replace('图解中的装配整体示意沿用 O22；本页蓝色网格是最终打印形状。','教程已同步 D01–D14 盘位、26 步取件清单与 O22F7 当前本体形状。')
        write(path,s)
    print('GUIDE_BUILT',REV,flush=True)


if __name__=='__main__':build()
