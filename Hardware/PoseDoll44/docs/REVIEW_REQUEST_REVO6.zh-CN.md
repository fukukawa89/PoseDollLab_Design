# Rev O6 审查请求：完整肩臂与背部集中路线

请先读 [本轮设计与结果说明](O6_DESIGN_AND_BACKPACK.zh-CN.md)，再读 [实际结果汇总](../verification/revO6/runs/o6_20260924_r1/results.json)。本轮为未提交工作树；基线 HEAD 为 451cbe0aa0c0b4016bee3da4d1dedc340a4c28f1。实际审查对象由 O6 delivery 的哈希清单固定，不能仅用旧 HEAD 代表本轮代码。

用户要求：静态摆姿采集、没有硬件、1.2 kg 不再是硬门槛；优先推进可验证工作，需要时允许回到背部集中。91 cm 备用版保留。没有改变 41 测量轴 + 3 固定槽位，也没有缩减动作清单。

## 当前证据入口

| 项目 | 相对于 Hardware/PoseDoll44 的路径 | 结论范围 |
|---|---|---|
| L6 原生模型 | generated/revO6/runs/o6_20260924_r1/joint_L6_validated | 58 件，checked pipe 参考螺纹 |
| M4 原生模型 | generated/revO6/runs/o6_20260924_r1/joint_M4_validated | 58 件，8 mm 国产碟簧尺寸候选 |
| L6 正确装配顺序 | verification/revO6/runs/o6_20260924_r1/joint_L6_final | 52 个磨损/压缩组合；名义几何通过 |
| M4 正确装配顺序 | verification/revO6/runs/o6_20260924_r1/joint_M4_validated | 32 个组合；名义几何通过 |
| 双臂共同排布 | generated/revO6/runs/o6_20260924_r1/bilateral_search | 两角色、左右共 18 个模块 |
| 实际双臂相交 | verification/revO6/runs/o6_20260924_r1/bilateral_search/bilateral.json | 100 个状态中 46 个失败，完整机构未通过 |
| 条件载荷与手感 | verification/revO6/runs/o6_20260924_r1/bilateral_search/loads.json | 真实模块 COM + 明示质量分配；低摩擦保持力缺口 |
| 背部六板试排 | verification/revO6/runs/o6_20260924_r1/backpack/backpack_study.json | 未布线原板、未确认配合头与 RF 空间；不是合格 PCBA |
| 背部空间扫描 | verification/revO6/runs/o6_20260924_r1/backspace | 人体包络路径筛查 + 真实模块否决；两者不能互相替代 |
| 独立 DC1 数字实验 | verification/revO6/runs/o6_20260924_r1/daisy/results.json | 2080 单比特反例；仍无法证明物理节点数和新鲜度；不可采集 |
| CAD 内核反例 | verification/revO6/runs/o6_20260924_r1/thread_diagnostics | 旧 ruled 螺旋产生不守恒结果；早期模型通过项作废 |
| 原厂依据 | references/revO6/primary_sources.json | 如实区分完整 PDF、索引片段、缺失资料 |

没有实物测试、生产公差、最大预紧力、整机关节寿命、电气保护或制造放行。UE 与 O5/O5CN 封存按原字节保留。

## 希望优先审查的决策

1. 肩、锁骨和上臂旋转轴仍互相碰撞，继续调独立模块位置是否已收益有限？优先给出一个具有真实轴承、制动受力与输出连接路径的共同承力结构，保留人体比例与必要动作。不要删除碰撞动作或仅画理想重合轴。
2. L6 缩短输出和支承跨度是否值得保留？请评估 8.2 mm 双支承带来的间隙放大、短双 D 锥面、中心螺钉、外圈四孔接口，以及导向薄片的实际保持和带载滑动。
3. M4 国产 8 mm A 碟簧模型名义几何成立，但低摩擦条件下部分轴保持力不足。请根据载荷、手掰力和真实力曲线决定适用轴；不能把 210 N 目录点作为最大力或简单增加所有预紧。
4. 六块旧板共仓仍厚，且实际肩锁骨机构占用背部空间。背部集中应与机构重构共同设计。54 × 48 × 22 mm 的人体包络候选与当前关节相撞，已否决用于当前布局；不应据此宣布中央板可装下。
5. DC1 是 AS5048 菊花链的隔离数字实验。除了校验角度和诊断寄存器，如何证明链上节点数、顺序、身份/新鲜度以及局部断链后的行为？若合并物理 MCU，必须重审故障域，不能继续套用旧七物理节点论证。
6. 检查 O6 螺纹布尔守恒护栏是否充分、磨损补偿是否超出弹簧目录工作点，以及完整装配、工具、线束、PCBA、颈胸/壳体仍缺哪些必要数字工作。

供应商只按有依据的改进更换。保留 AS5048 基线及 Alpha 线材，MT6701/CJT 仍为隔离候选；M4 的新导向已按锐尔立 8 mm 碟簧重建。这不是对供应商或整个机构的最终最优证明。

## 复算方式

在 design 仓库根目录运行。现有报告封存后，请把重算输出写入新目录，不要覆盖封存产物。

```powershell
.venv/Scripts/python.exe -X utf8 scripts/seal_revo6.py --verify
.venv/Scripts/python.exe -X utf8 Hardware/PoseDoll44/tools/run_cad.py Hardware/PoseDoll44/cad/revO6/compact_interfaces.py --compact-bearing --out .local/o6_recheck/L6
.venv/Scripts/python.exe -X utf8 Hardware/PoseDoll44/tools/run_cad.py Hardware/PoseDoll44/cad/revO6/small_joint.py --spring-series A --out .local/o6_recheck/M4
.venv/Scripts/python.exe -X utf8 Hardware/PoseDoll44/tools/run_cad.py Hardware/PoseDoll44/cad/revO6/verify_family_v2.py --joint .local/o6_recheck/L6 --out .local/o6_recheck/L6_check
.venv/Scripts/python.exe -X utf8 Hardware/PoseDoll44/tools/run_cad.py Hardware/PoseDoll44/cad/revO6/verify_family.py --joint .local/o6_recheck/M4 --out .local/o6_recheck/M4_check
.venv/Scripts/python.exe -X utf8 scripts/search_revo6_backspace.py --out .local/o6_recheck/backspace
```

其余原生双臂搜索、相交、载荷、空心工具和 DC1 入口见 delivery 清单中的脚本。CAD 检查退出码 0 表示报告生成完成；设计状态必须读取报告中的 FAIL/PASS 及范围，不能把程序完成当作设计通过。
