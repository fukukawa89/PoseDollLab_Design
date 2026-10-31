# O23G STL 导出修复与切片验证

原来 32 件导出中有 **20 件 STL 回读失败**；本轮修复后 **32/32 件通过**。原装配几何、关节位置、动作参数、外形、连接杆数量和布线位置均未更改。此处 32 件为本轮新制或修改的结构件、背盒和右腕件；其余沿用 O22F7 的关节打印件继续使用原文件。

## 失败的具体原因

1. 二进制 STL 使用单精度坐标且不保存共享顶点索引。原布尔网格中的部分极短边在量化、按坐标焊接后塌缩，留下零面积三角面或多片面共用一条边。
2. 有些旧布尔运算留下两张重合但方向相反的面，形成没有厚度的内部薄面。原先只检查带索引网格的封闭性，没充分暴露这些问题。
3. 背盒尤为明显：旧版盖板螺钉柱修改留下重叠薄面。此处根据现有参数重新生成底板、侧壁、孔柱、安装耳和布线座，去除历史运算残面。重新生成的实体与原设计的布尔差体积小于 0.000001 mm³，孔位和名义尺寸相同。

修复使用零面积面清理、方向相反的重合面对消和必要的极小公差网格简化。没有用自动补洞填住关节开口、线槽或安装孔，也没有对整件进行体素重建。网格简化最大公差为 0.001 mm，加上 STL 量化后的声明表面位移上限为 **0.0010038 mm**。逐件增加/减少体积另有记录。

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

修复前文件保留在 `history/O23G_before_export_repair_20261021/`。装配 SHA-256 仍为 `0c8009b72d72fce6acdf76d06cdcbebd2b16949ee578720b688713e71b34671d`；设备参数 SHA-256 仍为 `54b8f3ffc86b059183ba58310c25a87226fc2cf369ea33e72fca344c067f91f2`。

## 本地复现

在 design 根目录使用现有 `.venv/Scripts/python.exe -X utf8 -u` 运行以下脚本。仅离线生成文件，不连接打印机。

1. `scripts/revo23_export.py`：生成隔离的修复候选 STL。
2. `scripts/slice_revo23_exports.py`，随后 `scripts/audit_revo23_slices.py`：实际切片及保存后模型/打印路径复核。
3. `scripts/verify_revo23_exports.py` 的 `features`、`fixed`、`daily`、`edge` 四种模式：回读 STL 后复查连接、布线和动作。
4. `scripts/publish_revo23_export_repair.py`：全部通过才更新公开导出。
5. `scripts/finish_revo23_g.py --notes`、`scripts/present_revo23.py`、`scripts/present_revo23_g_review.py`：刷新说明与预览。
6. `scripts/plot_revo23_slice_paths.py`（绘图需要 matplotlib）、`scripts/document_revo23_export_repair.py`、`scripts/audit_revo23_delivery.py`：生成路径图、带校验和的下载包并审核交付一致性。
