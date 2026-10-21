"""Human-readable repair evidence and checksum-verified download bundles."""
from revo23_export import *
from package_revo23 import NAMES
from html import escape

def main():
    r=read(B/'verification/stl_export_repair.json');reg=read(B/'verification/stl_regression.json');s=read(B/'verification/slice_validation.json')
    assert r['passed'] and reg['passed'] and s['passed']
    out=B/'verification/stl_export_review';out.mkdir(parents=True,exist_ok=True)
    assert (out/'slice_paths.png').exists()
    notes=f'''# O23G STL 导出修复与切片验证

原来 32 件导出中有 **20 件 STL 回读失败**；本轮修复后 **32/32 件通过**。原装配几何、关节位置、动作参数、外形、连接杆数量和布线位置均未更改。此处 32 件为本轮新制或修改的结构件、背盒和右腕件；其余沿用 O22F7 的关节打印件继续使用原文件。

## 失败的具体原因

1. 二进制 STL 使用单精度坐标且不保存共享顶点索引。原布尔网格中的部分极短边在量化、按坐标焊接后塌缩，留下零面积三角面或多片面共用一条边。
2. 有些旧布尔运算留下两张重合但方向相反的面，形成没有厚度的内部薄面。原先只检查带索引网格的封闭性，没充分暴露这些问题。
3. 背盒尤为明显：旧版盖板螺钉柱修改留下重叠薄面。此处根据现有参数重新生成底板、侧壁、孔柱、安装耳和布线座，去除历史运算残面。重新生成的实体与原设计的布尔差体积小于 0.000001 mm³，孔位和名义尺寸相同。

修复使用零面积面清理、方向相反的重合面对消和必要的极小公差网格简化。没有用自动补洞填住关节开口、线槽或安装孔，也没有对整件进行体素重建。网格简化最大公差为 0.001 mm，加上 STL 量化后的声明表面位移上限为 **{r['max_declared_surface_displacement_mm']:.7f} mm**。逐件增加/减少体积另有记录。

## 已完成的验证

| 检查 | 结果 |
|---|---|
| 实际 STL 回读 | 32 件均封闭、面朝向一致、正体积、单连通实体 |
| 边与面 | 开边、非流形边、退化面、重复面均为 0 |
| 实际切片 | OrcaSlicer 2.4.2，32 件全部产生有效打印路径，修复计数为 0 |
| 切片后模型回读 | 32 件三角面索引保持一致，顶点仅有数值写入误差，均单实体且封闭 |
| 路径覆盖 | 检查模型底部及顶部实际挤出高度、非空模型层与挤出路径 |
| 连接结构 | 44 条圆截面连接及其底座材料完整性通过，单个相邻部件最多 3 根连接 |
| 布线 | 33 个固定座、8 条内部通道通过；46 路线束计划保持不变 |
| 动作 | 将实际 STL 放回装配，408 个日常姿态 + 114 个过渡姿态，相邻部位新增干涉为 0 |
| 固定配合 | 实际 STL 与固定五金、安装件配合检查通过 |

两个零件（右锁骨外段 O23G-S09、左肘下段 O23G-S17）在原包围盒候选摆放下未产生模型首层。改为让已有平面朝向热床，重新切片后通过；没有缩放、切削或修改零件。

验证配置：**Bambu Lab A1 mini、PLA、0.4 mm 喷嘴、0.16 mm 常规层高、0.2 mm 首层、3 道壁、20% 填充、自动支撑**。每件单独一盘。这些是切片验证工程，尚未经过实际打印；打印方向、支撑拆除、静载强度、疲劳和线束反复弯折仍需首件确认。

## 文件

- [检查页面与逐件下载](verification/stl_export_review/index.html)
- [32 件 STL 压缩包](exports/O23G_STL_checked.zip)，单位 mm，保留零件局部坐标。
- [32 件切片验证工程压缩包](exports/O23G_slice_validation_A1mini_PLA.zip)，含摆放、设置、自动支撑和已生成路径。
- `review_3mf/`：与修复 STL 相同网格的纯几何 3MF，使用验证过的摆放方向；原 CAD 索引网格保留在 `assembly.npz`。
- [导出前后逐件统计](verification/stl_export_repair.json)、[连接/布线/动作回归记录](verification/stl_regression.json)、[切片与模型回读记录](verification/slice_validation.json)。

修复前文件保留在 `history/O23G_before_export_repair_20261021/`。装配 SHA-256 仍为 `{r['geometry_sha256']}`；设备参数 SHA-256 仍为 `{reg['profile_sha256']}`。

## 本地复现

在 design 根目录使用现有 `.venv/Scripts/python.exe -X utf8 -u` 运行以下脚本。仅离线生成文件，不连接打印机。

1. `scripts/revo23_export.py`：生成隔离的修复候选 STL。
2. `scripts/slice_revo23_exports.py`，随后 `scripts/audit_revo23_slices.py`：实际切片及保存后模型/打印路径复核。
3. `scripts/verify_revo23_exports.py` 的 `features`、`fixed`、`daily`、`edge` 四种模式：回读 STL 后复查连接、布线和动作。
4. `scripts/publish_revo23_export_repair.py`：全部通过才更新公开导出。
5. `scripts/finish_revo23_g.py --notes`、`scripts/present_revo23.py`、`scripts/present_revo23_g_review.py`：刷新说明与预览。
6. `scripts/plot_revo23_slice_paths.py`（绘图需要 matplotlib）、`scripts/document_revo23_export_repair.py`、`scripts/audit_revo23_delivery.py`：生成路径图、带校验和的下载包并审核交付一致性。
'''
    (B/'STL_EXPORT_REPAIR.zh-CN.md').write_text(notes,encoding='utf8')
    rows=[]
    for x in r['rows']:
        rid=x['id'];key=x['key'].split('/',1)[1];label=NAMES.get(key,{'controller_housing':'背盒','controller_lid':'背盒盖'}.get(key,key))
        sx=next(v for v in s['rows'] if v['id']==rid)
        rows.append(f'<tr><td>{rid}</td><td>{escape(label)}</td><td class="ok">封闭 · 单实体</td><td>{sx["layer_count"]}</td><td><a download href="../../{x["stl"]}">STL</a> · <a download href="../../{sx["validation_project"]}">切片工程</a></td></tr>')
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>O23G · STL 修复与切片验证</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f4ee;color:#263b37;font:16px/1.75 "Microsoft YaHei",sans-serif}main{max-width:1100px;margin:auto;padding:38px 24px}h1{font-size:34px;margin:0 0 10px}h2{font-size:22px;margin-top:32px}.eyebrow{font-size:12px;letter-spacing:2px;color:#586d65}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:25px 0}.card{background:#e6eee8;border:1px solid #c8d7cd;border-radius:10px;padding:18px}.card strong{font-size:29px;display:block}a{color:#11685c}p{max-width:960px}.downloads{display:flex;gap:12px;flex-wrap:wrap}.downloads a{background:#175e53;color:white;padding:10px 17px;border-radius:7px;text-decoration:none}.muted{color:#5b6c67;font-size:14px}img{width:100%;border:1px solid #d6ded6;border-radius:8px}table{width:100%;border-collapse:collapse;background:white;font-size:14px}th,td{text-align:left;padding:10px;border-bottom:1px solid #e0e5df}th{background:#e6eee8}.scroll{overflow:auto}.ok{color:#176e50}code{word-break:break-all;font-size:12px}@media(max-width:700px){.cards{grid-template-columns:1fr}main{padding:25px 16px}h1{font-size:27px}}
</style><main><p class="eyebrow">POSEDOLL LAB / O23G / 导出验证</p><h1>32 件 STL 修复完成</h1><p>原来有 20 件 STL 回读失败。本轮清理导出网格并验证实际切片；装配模型、关节位置、外形和布线位置保持不变。</p>
<div class="cards"><div class="card"><strong>32 / 32</strong>封闭 · 单实体 · 面朝向正确</div><div class="card"><strong>32 / 32</strong>实际切片通过 · 零网格修复</div><div class="card"><strong>522 姿态</strong>STL 回装后无新增相邻干涉</div></div>
<div class="downloads"><a download href="../../exports/O23G_STL_checked.zip">下载本轮 32 件 STL</a><a download href="../../exports/O23G_slice_validation_A1mini_PLA.zip">下载切片验证工程</a></div>
<h2>原来为什么失败？</h2><p>部分极短边在 STL 单精度坐标量化、顶点焊接后塌缩；旧布尔运算还留下了方向相反的重合薄面。背盒中保留了旧螺钉柱修改产生的残面。只检查源网格的索引封闭性不足以发现这些问题。</p><p>本轮清理退化面、对消零厚度重合面，并在必要时用不超过 0.001 mm 的公差整理网格。背盒按现有相同参数重新生成。孔位、关节开口、连接杆和线槽均保留，未使用整体补洞或体素重建。</p>
<h2>哪些检查保持通过？</h2><p>44 条连接与底座材料完整性、每个相邻部件最多 3 根连接、33 个线材固定座、8 条内部通道、固定配合，以及原有 408 个日常姿态和 114 个过渡姿态，均使用导出的 STL 重新核对。</p>
<h2>实际打印路径抽查</h2><p>下图来自已生成的 G-code。深绿是模型路径，淡蓝是支撑，灰色是对应模型截面。</p><a href="slice_paths.png"><img src="slice_paths.png" alt="大腿、小臂、骨盆和背盒在两个高度的实际切片路径"></a>
<p class="muted">OrcaSlicer 2.4.2 · A1 mini · PLA · 0.4 mm 喷嘴 · 0.16 mm 层高 · 3 道壁 · 20% 填充 · 自动支撑。两件零件调整了摆放以生成模型首层。验证工程每件一盘，尚未实物试打；支撑拆除与强度仍需确认。</p>
<h2>逐件文件</h2><p class="muted">本包包含本轮新制或修改的 32 件；其余沿用 O22F7 的关节打印件继续使用原文件。</p><div class="scroll"><table><thead><tr><th>编号</th><th>部位</th><th>网格</th><th>总层数¹</th><th>下载</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div><p class="muted">¹ 总层数包含自动支撑的中间层，不等于模型高度除以常规层高。</p>
<p><a href="../../STL_EXPORT_REPAIR.zh-CN.md">详细原因与复现说明</a> · <a href="../stl_export_repair.json">导出统计</a> · <a href="../stl_regression.json">回归记录</a> · <a href="../slice_validation.json">切片记录</a> · <a href="../../preview/index.html?revision=O23G-export-repair">打开完整人偶</a></p>
<p class="muted">原装配几何 SHA-256：<code>'''+r['geometry_sha256']+'''</code></p></main></html>'''
    (out/'index.html').write_text(html,encoding='utf8')
    exports=B/'exports';exports.mkdir(exist_ok=True)
    bundles=[]
    for name,files in [('O23G_STL_checked.zip',[B/x['stl'] for x in r['rows']]+[B/'review_stl/先读我.txt']),
                       ('O23G_slice_validation_A1mini_PLA.zip',[B/x['validation_project'] for x in s['rows']])]:
        files+= [B/'STL_EXPORT_REPAIR.zh-CN.md',B/'verification/stl_export_repair.json',B/'verification/stl_regression.json',B/'verification/slice_validation.json']
        manifest={p.relative_to(B).as_posix():sha(p) for p in files};dest=exports/name
        with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in files:z.write(p,p.relative_to(B).as_posix())
            z.writestr('SHA256.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        with zipfile.ZipFile(dest) as z:
            assert z.testzip() is None
            for rel,h in manifest.items():assert hashlib.sha256(z.read(rel)).hexdigest()==h
        bundles.append(dict(file=dest.relative_to(B).as_posix(),sha256=sha(dest),files=len(manifest),size_bytes=dest.stat().st_size,archive_verified=True))
    put(exports/'manifest.json',dict(geometry_sha256=r['geometry_sha256'],export_set_sha256=r['export_set_sha256'],bundles=bundles))
    put(out/'provenance.json',dict(geometry_sha256=r['geometry_sha256'],export_set_sha256=r['export_set_sha256'],
        image_sha256=sha(out/'slice_paths.png'),index_sha256=sha(out/'index.html'),report_sha256=sha(B/'verification/stl_export_repair.json')))
    print('DOCUMENTED',bundles,flush=True)

if __name__=='__main__':main()
