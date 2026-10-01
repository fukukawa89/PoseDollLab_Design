"""Publish the O22 A1 mini plate guide and self-contained download archive."""
from pathlib import Path
from collections import Counter
import hashlib, html, json, zipfile

ROOT=Path(__file__).resolve().parents[1]
H=ROOT/'Hardware/PoseDoll44'
B=H/'bench/revO22'
OUT=B/'a1mini'
ARCHIVE=B/'PoseDoll_O22_A1mini_Print_Plates.zip'
E=html.escape


def main():
    m=json.loads((OUT/'manifest.json').read_text());v=json.loads((OUT/'verification/bambu_studio.json').read_text());assert v['status']=='PASS'
    plates=m['plates'];cards=[];summary=[];details=[]
    for p in plates:
        group='test' if p['optional'] else ('torso' if p['slug'].startswith(('head','torso')) else ('arm' if 'arm' in p['slug'] else 'leg'))
        rows=''.join(f'<tr><td>{i["number"]:02}</td><td><b>{i["id"]}</b><small>{E(i["part"])}</small></td><td>1</td></tr>' for i in p['items'])
        cards.append(f'''<article class="card" data-group="{group}" id="{p['id']}"><div class="card-head"><span class="plate-id">{p['id']}</span><span class="count">{p['count']} 件</span></div><h3>{E(p['title'])}</h3><div class="preview-switch" role="group" aria-label="{p['id']} 预览模式"><button type="button" aria-pressed="true" data-view="layout">编号排布</button><button type="button" aria-pressed="false" data-view="model">3D 模型</button></div><figure><img class="layout" src="{p['preview']}" alt="{E(p['title'])}，180毫米平台俯视编号排布" loading="lazy"><img class="model" src="previews/{p['id']}.png" alt="Bambu Studio 中的{E(p['title'])}模型" loading="lazy" hidden></figure><div class="plate-meta"><span>最高 {p['max_height_mm']:.1f} mm</span><span>{'可选小样' if p['optional'] else '本盘打印 1 次'}</span></div><a class="download" href="{p['file']}" download>下载 {p['id']} · 3MF <span aria-hidden="true">↗</span></a><details><summary>展开 {p['count']} 件零件清单</summary><table><thead><tr><th>图号</th><th>零件 / 所属位置</th><th>数量</th></tr></thead><tbody>{rows}</tbody></table></details></article>''')
        summary.append(f'| {p["id"]} | {p["title"]} | {p["count"]} | {p["max_height_mm"]:.1f} mm | [{Path(p["file"]).name}]({p["file"]}) |')
        details.append(f'### {p["id"]} · {p["title"]}\n\n'+ '\n'.join(f'- [ ] {i["number"]:02} · {i["id"]} · `{i["part"]}` × 1' for i in p['items']))
    page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>O22 · A1 mini 多零件打印盘</title><style>
:root{color-scheme:light;--paper:#f6f4ed;--ink:#243d37;--soft:#65776c;--line:#d4d9cb;--accent:#365f4d}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 'Segoe UI','Microsoft YaHei',sans-serif}a{color:inherit;text-underline-offset:4px}button{font:inherit;cursor:pointer}header,main,footer{max-width:1260px;margin:auto;padding:0 34px}header{display:flex;align-items:center;justify-content:space-between;gap:20px;padding-top:25px;padding-bottom:24px;border-bottom:1px solid var(--line);font-size:14px}.brand{font-weight:750;letter-spacing:.12em}.brand span{font-weight:400;color:var(--soft);letter-spacing:.04em;margin-left:12px}.hero{padding:53px 0 34px;max-width:910px}.eyebrow{font-size:12px;letter-spacing:.12em;color:var(--soft)}h1{font-size:clamp(32px,5vw,60px);font-weight:650;letter-spacing:-.04em;line-height:1.2;margin:15px 0 24px}h1 span{color:#6d825b}.intro{font-size:18px;max-width:770px;color:#52655b}.actions{display:flex;align-items:center;gap:22px;flex-wrap:wrap;margin-top:28px}.primary,.download{display:flex;align-items:center;justify-content:space-between;text-decoration:none;background:var(--accent);color:white;padding:12px 19px;border-radius:5px;font-weight:650}.primary{display:inline-flex;gap:28px}.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;padding:8px 0 32px}.fact{border-top:1px solid #abb5a1;padding-top:14px}.fact strong{display:block;font-size:28px;font-weight:650}.fact span{font-size:13px;color:var(--soft)}.instructions{display:grid;grid-template-columns:1fr 1fr;gap:30px;padding:24px 26px;background:#e8ece1;border-radius:8px;margin-bottom:40px}.instructions h2{font-size:17px;margin:0 0 8px}.instructions p{font-size:14px;margin:0 0 8px;color:#40574b}.instructions small{font-size:12px;color:#617064}.section-head{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:20px;flex-wrap:wrap}h2{font-size:25px;margin:0}.filters{display:flex;gap:6px;flex-wrap:wrap}.filters button,.preview-switch button{border:1px solid var(--line);background:transparent;border-radius:30px;padding:6px 14px;font-size:13px;color:var(--ink)}button[aria-pressed=true]{background:var(--ink);color:#fff;border-color:var(--ink)}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #9c632f;outline-offset:3px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));align-items:start;gap:24px}.card{border:1px solid var(--line);border-radius:9px;background:#fffdf8;padding:21px;min-width:0}.card-head{display:flex;align-items:center;justify-content:space-between}.plate-id{font:600 13px/1.7 Consolas,monospace;letter-spacing:.08em}.count{color:var(--soft);font-size:13px}h3{font-size:18px;line-height:1.5;min-height:54px;margin:8px 0 12px;font-weight:650}.preview-switch{display:flex;gap:6px}.preview-switch button{font-size:12px;padding:4px 11px}figure{margin:15px 0 9px;background:#f6f4ed;border-radius:6px;aspect-ratio:194/201;display:flex;align-items:center}figure img{width:100%;height:100%;object-fit:contain;border-radius:6px}img[hidden],article[hidden]{display:none}.plate-meta{display:flex;justify-content:space-between;color:var(--soft);font-size:12px;margin:9px 0 17px}.download{font-size:14px;padding:10px 14px}details{margin-top:16px;border-top:1px solid var(--line);padding-top:12px}summary{font-size:13px;cursor:pointer}table{border-collapse:collapse;width:100%;font-size:12px;margin-top:13px;table-layout:fixed}th{text-align:left;color:var(--soft);font-weight:500}th:first-child,td:first-child{width:37px}th:last-child,td:last-child{width:32px;text-align:right}td{border-top:1px solid #e3e5db;padding:9px 0;vertical-align:top}td small{display:block;overflow-wrap:anywhere;color:var(--soft);line-height:1.5}footer{font-size:12px;color:var(--soft);padding-top:35px;padding-bottom:40px}footer p{border-top:1px solid var(--line);padding-top:20px}.tiny{font-size:13px;color:var(--soft);margin:0 0 24px}@media(max-width:1000px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:620px){header,main,footer{padding-left:20px;padding-right:20px}header .brand span{display:none}.hero{padding-top:33px}.facts{grid-template-columns:repeat(2,1fr);gap:20px}.instructions{grid-template-columns:1fr;gap:15px;padding:20px}.grid{grid-template-columns:1fr}.card{padding:20px}h3{min-height:0}.intro{font-size:16px}header>a{font-size:12px}}
</style></head><body><header><div class="brand">POSEDOLL O22 <span>A1 MINI PRINT PLATES</span></div><a href="../../../tutorials/full-doll-o22/index.html">返回人偶设计</a></header><main><section class="hero"><div class="eyebrow">2026.10.02 / 按身体部位排盘</div><h1>整套人偶，<span>10 盘打印。</span></h1><p class="intro">把 186 件集中到 A1 mini 的平台上，减少反复暖机和冷却。左右肢体优先分开；同一区域的骨架、关节和小件一起收纳。</p><div class="actions"><a class="primary" href="../PoseDoll_O22_A1mini_Print_Plates.zip" download>下载完整拼盘包 <span>↓ ZIP</span></a><a href="README.zh-CN.md">打印说明与勾选清单</a></div></section><section class="facts" aria-label="打印盘概况"><div class="fact"><strong>10 盘</strong><span>A01–A10，各打印一次</span></div><div class="fact"><strong>186 件</strong><span>185 件人偶零件 + 1 件量规</span></div><div class="fact"><strong>180 × 180</strong><span>平台尺寸 mm，高度上限 180 mm</span></div><div class="fact"><strong>6 mm</strong><span>模型最小间距与平台边距</span></div></section><section class="instructions"><div><h2>打开一盘，就打印这一盘。</h2><p>在 Bambu Studio 选择 A1 mini，导入一份 3MF，保持 100% 比例和现有摆放，使用「按层打印」。不要把多个盘的文件同时导入同一个平台。</p><p>文件包含独立零件和已排好的位置。使用你在 O11 小样上验证过的材料及打印工艺，切片后再打印。</p></div><div><h2>已经完成试切片。</h2><p>11 个文件全部通过 Bambu Studio 2.8.2.61 导入和切片检查，无网格修复、无切片警告。参考检查使用 0.4 mm 喷嘴、PLA、0.20 mm 层高、普通自动支撑和 2 mm 外裙边。</p><small>3MF 不含机器 G-code 或固定耗材预设。改用更宽裙边或树状支撑后需重新确认占位。T01 为可选传感器小样，不计入整机 10 盘。</small></div></section><section id="plates"><div class="section-head"><h2>每盘内容</h2><div class="filters" role="group" aria-label="按身体部位筛选"><button type="button" data-filter="all" aria-pressed="true">全部</button><button type="button" data-filter="torso" aria-pressed="false">头颈 / 躯干</button><button type="button" data-filter="arm" aria-pressed="false">双臂</button><button type="button" data-filter="leg" aria-pressed="false">双腿</button><button type="button" data-filter="test" aria-pressed="false">可选小样</button></div></div><p class="tiny">编号图显示模型的平面外包轮廓，图号与清单一一对应；「3D 模型」来自 Bambu Studio。左、右按人偶自身区分。</p><div class="grid">__CARDS__</div></section></main><footer><p>O22 单件设计和已保存的工程包保留。本轮仅调整打印排布：无缩放、无镜像、无切割，沿用原贴床朝向。<a href="manifest.json">排盘清单</a> · <a href="verification/bambu_studio.json">切片检查记录</a> · <a href="https://cdn1.bambulab.com/documentation/quick-start-f507128172bdf/Quick%20start%20guide%20-%20A1%20mini-EN.pdf">A1 mini 官方尺寸</a></p></footer><script>
if(location.protocol==='file:'){document.querySelector('header>a').hidden=true;const link=document.querySelector('.primary');link.removeAttribute('download');link.href='#plates';link.textContent='查看各盘文件 ↓';}
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));document.querySelectorAll('.card').forEach(c=>c.hidden=button.dataset.filter!=='all'&&c.dataset.group!==button.dataset.filter)}));
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{const card=button.closest('.card');card.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));card.querySelector('.layout').hidden=button.dataset.view!=='layout';card.querySelector('.model').hidden=button.dataset.view!=='model'}));
</script></body></html>'''
    (OUT/'index.html').write_text(page.replace('__CARDS__','\n'.join(cards)),encoding='utf-8')
    readme='''# O22 · 拓竹 A1 mini 多零件打印盘

整套人偶为 **A01–A10 共 10 盘、186 件**，每盘打印一次。其中 185 件装在人偶上，P242 是 XIAO 装配间距量规。`optional/T01_sensor_coupon.3mf` 是额外的两件传感器安装小样，不计入整机数量。

打开本文件旁的 `index.html` 可离线查看排盘、3D 预览和每件所属位置。离线页面的首个按钮会跳转到各盘文件；也可以直接使用 `plates` 文件夹。

## 使用方法

1. 解压完整压缩包，在 Bambu Studio 中选择 **Bambu Lab A1 mini** 和实际喷嘴，打开 `plates` 中的一份 3MF。每个文件已经是一盘，不要同时把十份文件叠放进同一个盘。
2. 如果提示导入模型/几何，选择导入模型；保持各件现有相对位置，比例 **100%**。不执行自动排列或自动摆正，不逐件重新居中。核对对象数量与本表一致、与编号图布局相符。
3. 使用 **按层打印**。这种密集排布没有为“逐件打印”的整颗打印头预留避碰空间。
4. 使用你在 O11 小样上验证过的材料与工艺。文件只存几何、名称、排布，不绑定耗材、喷嘴或 G-code。切片后查看支撑、裙边和首层预览。
5. 打完后按盘号装袋；每盘内部按编号图和下面的清单核对。左右按人偶自身区分。相同打印编号（例如 N003）的多件复制已放齐，不必额外补数量。

## 排盘原则与验证

- 打印机官方成型空间 180 × 180 × 180 mm。模型离平台边缘至少 6 mm，模型包围框之间至少 6 mm。
- 保留原单件贴床朝向。只做平移、绕 Z 轴转 0°/90°；无缩放、镜像、切割或合并实体。
- 150 种源文件展开为 186 个实际实例，逐件核对恰好出现一次。输出 3MF 的每个顶点和三角面已读回检查，与刚体变换后的源网格完全相同。
- 按身体部位分组做 700 组排序搜索。头颈盘利用余量放背盒盖；腿部按左右大腿/关节件和双侧小腿/脚掌骨架分三盘。10 盘是本次找到的排布，不声称是所有工艺条件下的理论最少盘数。
- **11/11 文件通过本机 Bambu Studio 02.08.02.61 的完整导入和切片**：对象数及名称对应、无网格修复、无切片警告。参考设置为 A1 mini / 0.4 mm 喷嘴 / Generic PLA / 纹理 PEI / 0.20 mm 层高 / 3 圈墙 / 20% 填充 / 普通自动网格支撑 / 30°支撑阈值 / 2 mm 外裙边 / 无环形裙线 / 按层打印。
- 参考设置只是排布检查，不替代 O11 已验证的实际材料与配合工艺。本轮未进行实物打印。使用更宽裙边、树状支撑或筏层时，重新检查支撑占位是否越界、是否靠近其他模型。
- 机器暖机和冷却的实际时间未计量，不给出虚构的节省时长。`verification` 中的耗材和时间是上述参考设置的切片估计，不是测量值或预算变更。

官方尺寸：[A1 mini Quick Start Guide](https://cdn1.bambulab.com/documentation/quick-start-f507128172bdf/Quick%20start%20guide%20-%20A1%20mini-EN.pdf)。

## 每盘一览

| 盘号 | 部位 | 件数 | 最高模型 | 文件 |
|---|---|---:|---:|---|
'''+ '\n'.join(summary)+'''

## 每件核对清单

编号对应 SVG 排布图中的数字和 3MF 对象名。勾选清单只是装袋/装配辅助，不是额外要打印的标签。

'''+ '\n\n'.join(details)+'\n'
    (OUT/'README.zh-CN.md').write_text(readme,encoding='utf-8')
    index=H/'tutorials/full-doll-o22/index.html';text=index.read_text(encoding='utf-8')
    section='''<section id="a1mini" class="panel"><div class="eyebrow">A1 MINI · 多零件拼盘 · 2026.10.02</div><h2>整套 186 件，合成 10 盘打印。</h2><p>按头颈、躯干、左右手臂和腿部集中排布；适配 180×180×180mm 平台。每盘一个3MF，重复件数量已放齐，沿用原贴床朝向。10盘整机文件与1盘可选小样均通过Bambu Studio导入和切片检查。</p><div class="downloads"><a class="primary" href="../../bench/revO22/PoseDoll_O22_A1mini_Print_Plates.zip" download>下载 A1 mini 拼盘包</a><a href="../../bench/revO22/a1mini/index.html">查看每盘预览与清单</a></div><p>按层打印；使用O11已验证的材料工艺，切片后检查支撑和裙边。下方保留单件文件，方便补打。</p></section>'''
    if 'id="a1mini"' not in text:
        text=text.replace('<section id="print"',section+'\n<section id="print"',1)
        text=text.replace('<a href="#print">打印包</a>','<a href="#a1mini">A1 mini 拼盘</a>',1)
        text=text.replace('<div class="eyebrow">一套完整文件</div><h2>150种，186件。</h2>','<div class="eyebrow">单件文件 · 补打用</div><h2>150种，186件。</h2>',1)
        index.write_text(text,encoding='utf-8')
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file():z.write(path,'PoseDoll_O22_A1mini/'+path.relative_to(OUT).as_posix())
    digest=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    (B/'PoseDoll_O22_A1mini_Print_Plates.zip.sha256').write_text(digest+'  '+ARCHIVE.name+'\n',encoding='utf-8')
    print('Published',ARCHIVE,'bytes',ARCHIVE.stat().st_size,'SHA256',digest)

if __name__=='__main__':main()
