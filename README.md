# PoseDoll 人偶硬件设计

通用静态测姿人偶的独立设计仓库；Manny / Quinn 为软件适配目标。原来位于 `DollSimulation` UE 工程中的硬件、固件与硬件诊断工具已经迁入本目录；UE 插件、角色资产与完整 Python 模拟器留在原项目。

## 当前状态

**2026-10-30 O24E 单臂 R5：七自由度测角升级。** 以用户已实装认可摩擦与持姿效果的 R4 为基线，复用六路 O22 MT6701CT 与七颗径向充磁磁铁，腕偏摆增加一路 TMAG5170A1，双轴腕分别测量。保留 R4 摩擦、预紧、防脱结构及 136 件机械五金；重印 P005、P007、P009、P010、P012，复用其余六件主体，新增 29 件传感器附件及 J003/J004 工具。交付打印工程、清单、走线、409 步装配动画、固件和标定工具。数字几何、装配、切片、浏览器与软件检查通过；R5 实物测角精度、走线和升级后的持姿仍待测试，未烧录硬件。

- [R5 打印与装配入口](Hardware/PoseDoll44/bench/revO24E_LArm_Sensing_R5/START_HERE.html) · [重印说明](Hardware/PoseDoll44/bench/revO24E_LArm_Sensing_R5/PRINTING.html)
- [R5 测角方案](Hardware/PoseDoll44/bench/revO24E_LArm_Sensing_R5/SENSING.html) · [逐步装配动画](Hardware/PoseDoll44/bench/revO24E_LArm_Sensing_R5/assembly_guide/index.html) · [验证记录](Hardware/PoseDoll44/bench/revO24E_LArm_Sensing_R5/VERIFICATION.html)
- [R5 完整离线包](Hardware/PoseDoll44/bench/revO24E_LArm_Sensing_R5/O24E_R5_Arm_Sensing_20261030.zip) · [R4 实装反馈](Hardware/PoseDoll44/docs/R4_MECHANICAL_FEEDBACK_20261030.json)

**2026-10-26 O24D 改版交接：** 用户满意当前 O24D 外观，后续保留外观与 UE 骨架，重点重做关节连接、预紧、防松、防脱及装配。T6 W 按用户实装反馈通过；T6 H 按用户依据 T5 安装和 T6 继承关系的判断接受通过，可用于设计推进。T6 R 的整组轴向拔出是已确认缺陷，必须修复。当前 D 的 20 组金属筒输出套还存在规定装入路径与横销干涉，旧球腕入口及机构也需更新。[完整经验、审查与新对话任务](Hardware/PoseDoll44/docs/HANDOFF_O24D_REDESIGN_20261026.zh-CN.md)。本次仅整理与审查，未改动 D/T6 冻结交付包；100 次不补紧目标保留，不虚构循环数据。

**O24C-T6：尼龙锁母防松测试版（以下为发布记录，最新实物反馈见上）。** 针对 T5 H 肩钉逐渐旋退，H、R、双轴腕的七组肩钉统一改用 M3×0.5 DIN985 尼龙锁紧螺母。新一体固定座采用完整六角止转窝和轴向装入，调整内部金属垫圈堆叠，保留原 Φ4×8 / M3×6 肩钉、A8、运动件及 UE 轴心。必须重印 H6-01、R6-01、W6-01，建议先印 C6-01 试配片；其余 10 件打印件与 T5 字节相同。按已备齐 T5 计算，补齐 7 颗锁母、14 片 9×4.3×0.8 平垫和 7 片 7×3.2×0.5 平垫。数字装配、活动采样、切片和教程检查通过；100 次不补紧仍待实测。

- [O24C-T6：打印、装配与测试入口](Hardware/PoseDoll44/bench/revO24C_T6/START_HERE.html)
- [O24C-T6：H 35 步 / R 42 步 / W 74 步逐件动画](Hardware/PoseDoll44/bench/revO24C_T6/tutorial/index.html)
- [O24C-T6：三件重印工程](Hardware/PoseDoll44/bench/revO24C_T6/printing/REPRINT_T6_three_parts.3mf) · [锁母试配片](Hardware/PoseDoll44/bench/revO24C_T6/printing/FIT_T6_locknut_coupon.3mf)
- [O24C-T6：补购与复用清单](Hardware/PoseDoll44/bench/revO24C_T6/HARDWARE.html) · [100 次测试](Hardware/PoseDoll44/bench/revO24C_T6/TEST_PLAN.html)
- [O24C-T6：完整离线包](Hardware/PoseDoll44/bench/revO24C_T6/O24C-T6_print_and_assembly.zip)

**O24C-T5：一体承力座测试版。** 用户实物反馈确认 T3/T4 的 H 摩擦力可用，但 H3-01/02 接缝在强拧和反复摆动后张开。T5 将其合并为 H5-01，同时把 R 固定芯与双轴腕十字芯改成 R5-01、W5-01；五金从侧向导槽装入，保留原有摩擦堆叠和 UE 轴心。仅重印三件，其余 11 个打印件复用，无新增五金规格，省去八组合模五金。旧 H 的反馈仅为定性持姿认可，T5 结构、R/W、磨损和寿命仍需实测。

- [O24C-T5：打印、改动说明与实测](Hardware/PoseDoll44/bench/revO24C_T5/START_HERE.html)
- [O24C-T5：H 29 步 / R 39 步 / W 62 步逐件动画](Hardware/PoseDoll44/bench/revO24C_T5/tutorial/index.html)
- [O24C-T5：三个一体件重印工程](Hardware/PoseDoll44/bench/revO24C_T5/printing/REPRINT_T5_three_parts.3mf)
- [O24C-T5：完整 14 件一盘工程](Hardware/PoseDoll44/bench/revO24C_T5/printing/ALL_H_R_W_T5.3mf)
- [O24C-T5：完整离线包](Hardware/PoseDoll44/bench/revO24C_T5/O24C-T5_print_and_assembly.zip)

**T5 H 最新实测反馈：** 初始摩擦可用，但反复转动十几次后明显衰减。使用普通螺母、没有额外锁固；追加观察发现内侧螺钉尖端从凸出变为缩进，重新拧入约两圈后恢复，强烈支持肩钉旋退为主要原因。当前状态未满足用户“至少活动100次无需补紧”的目标；优先完善独立防松，再验证剩余的沉降、磨损及摩擦变化。[实物反馈与改进要求](Hardware/PoseDoll44/docs/TEST_FEEDBACK_O24C_T5_H.zh-CN.md)。

**O24C-T4：双轴碟簧腕测试版。** 在T3实臂接口上，腕部改回相交双铰链：Y屈伸、随动X偏摆，分别用O22轴肩螺钉和A8预紧。只新增W4-01～04四个打印件；T3的H/R、W3-09掌柄、F3测试附件及C3试片原样复用。E—W仍为80.496305mm。T3球腕未实测，原文件保留供对比；T4持姿与磨损也待实测。新腕约39.6mm横向外廓，独立调摩擦的便利以宽度和更多五金为代价。

- [O24C-T4：打印、装配与五金增量](Hardware/PoseDoll44/bench/revO24C_T4/START_HERE.html)
- [O24C-T4：H 36 步 / R 46 步 / W 76 步逐件动画](Hardware/PoseDoll44/bench/revO24C_T4/tutorial/index.html)
- [已购早期 O22 + T1-S2：T3 / T4 补购对照](Hardware/PoseDoll44/bench/revO24C_T4/HARDWARE.html)
- [O24C-T4：三个样件共 17 件，一盘打印工程](Hardware/PoseDoll44/bench/revO24C_T4/printing/ALL_H_R_W_T4.3mf)
- [O24C-T4：双轴腕三维及逐件定位](Hardware/PoseDoll44/bench/revO24C_T4/viewer/index.html?mode=W)
- [O24C-T4：完整打印测试包](Hardware/PoseDoll44/bench/revO24C_T4/PoseDoll_O24C_T4_Dual_Axis_Wrist_Kit.zip)

**O24C-T3：可按实际骨长联装的肘 H、前臂旋转 R、腕 W 测试模块。** 用户已报告旧 T1 H 持姿不足；T2-H 通用摩擦样条不作为实际手臂的资格验证。T3 在同一组实际零件上借鉴 O22 的轴肩螺钉与 A8 碟簧预紧，E—W 保持 80.496305 mm；腕固定侧球窝与骨杆桥一体，避免整组横向窜动。提供15个关节打印件、4个可拆测试附件、1个试配片及5盘工程。数字装配/姿态/切片检查与实际承载分开记录；实物持姿、磨损、肩部和完整人偶仍待验证。

- [O24C-T3：打印、五金及装配入口](Hardware/PoseDoll44/bench/revO24C_T3/START_HERE.html)
- [O24C-T3：真实尺寸联装和分步定位](Hardware/PoseDoll44/bench/revO24C_T3/viewer/index.html)
- [O24C-T3：完整样件包](Hardware/PoseDoll44/bench/revO24C_T3/PoseDoll_O24C_T3_Arm_Test_Kit.zip)

完整人偶设计交接：[O24D 交接指南](Hardware/PoseDoll44/docs/HANDOFF_O24D.zh-CN.md)。其中原S1测试假设已由2026-10-22的H04实物问题反馈补充；最新T1结构修正见S2重印说明。整机工作以O24D目录最新状态为准。

**O24C-T1-S2：关节台架结构修正版。** 用户实物反馈暴露了H04固定压板的薄弱根部，S2将H04/R04改为连续腹板，并加宽H04/H05/R04/R05的锁轴螺母座及侧向入口。只需重印这四件各1个；其余22件基础件、12件备选件和五金沿用S1。提供四件专用重印盘；完整套件仍为26件基础件、6盘。数字连接/装配/活动/切片检查见交付报告，S2实物刚度、持姿与磨损待测。[S2重印说明](Hardware/PoseDoll44/bench/revO24C_T1/REPRINT_S2.html)。

- [O24C-T1：打印、采购与装配入口](Hardware/PoseDoll44/bench/revO24C_T1/START_HERE.html)
- [O24C-T1：可旋转样件与拆解](Hardware/PoseDoll44/bench/revO24C_T1/preview/index.html)
- [O24C-T1：打印测试包](Hardware/PoseDoll44/bench/revO24C_T1/PoseDoll_O24C_T1_Print_Test_Kit.zip)

**O24C：肩、肘、球面腕的紧凑候选。** 保留 UE 骨架中心和 560 mm 参考比例；相较 B，中立关节包围盒体积分别减少约 9.1%、15.1%、25.5%。标准轴承、主轴径、销径和衬片厚度保留，1,001 组实体动作及选定活动间隙检查通过。可靠性仍需预紧锁固细化和实物验收，A/B 原文件保留。

- [O24C：B / C 同尺度三维对比](Hardware/PoseDoll44/bench/revO24C/preview/index.html)
- [O24C：缩小尺寸、间隙与可靠性取舍](Hardware/PoseDoll44/bench/revO24C/DESIGN.zh-CN.md)

**O24B：新增共心球面手腕研究候选。** 同一个 D24 球形输出件完成两个方向摆动，导向槽限制多余自转；保留 O24A 肩肘和 560 mm 整偶骨架参考。326 个离散姿态通过新腕部干涉检查，磁测角仍需整臂干扰标定，导向间隙、预紧和接口尚未实物验证。B 暂不取代 A。

- [O24B 动画：球体摆动、拆解与 A / B 对比](Hardware/PoseDoll44/bench/revO24B/preview/index.html)
- [O24B 设计、验证结果与制造前条件](Hardware/PoseDoll44/bench/revO24B/DESIGN.zh-CN.md)
- [O24B：9 组机器人方案调研](Hardware/PoseDoll44/bench/revO24B/RESEARCH.zh-CN.md)

**O24A：新增 UE 骨架对齐的左臂数字布局。** 对应 Quinn 560 mm 中立站姿参考高度；肩、肘、腕中心对齐，前臂沿肘—腕线扭转。包含 9 路肩带与手臂测角、可编辑装配、动作预览及独立骨架/网格检查。尚需完善预紧锁固、磁铁杯、线束和实物验收，当前不是可直接打印的制造包。

- [O24A 设计、活动范围与验证边界](Hardware/PoseDoll44/bench/revO24/DESIGN.zh-CN.md)
- [O24A 可摆动三维预览](Hardware/PoseDoll44/bench/revO24/preview/index.html)
- [O24A 手臂动画教程：拆解、旋转与分步装配](Hardware/PoseDoll44/bench/revO24/preview/tutorial.html)
- [O24A 参数化源文件](Hardware/PoseDoll44/cad/revO24/arm.py)
- [O23I 既有整偶设计](Hardware/PoseDoll44/bench/revO23/DESIGN.zh-CN.md)

### O21 历史记录

**O21 已生成约 1500 元的降本工程候选。** 保留 O20 骨架和46路测量；改用 MT6701CT、单面传感板、中央三组16路选择和预制五芯线。单套目标分配1482.50元，尚无正式报价。传感板 ERC/DRC 与固件/主机测试通过；中央板布线、装配集成、实物标定和UE端到端仍未完成，不是整机制造放行。

- [O21设计与成本依据](Hardware/PoseDoll44/docs/DESIGN_REVO21.zh-CN.md)
- [O21预算与通道预览](Hardware/PoseDoll44/tutorials/full-doll-o21/index.html)
- [O21工程设计包](Hardware/PoseDoll44/bench/revO21/PoseDoll_O21_CostDown_Design.zip)
- [加工询价要求](Hardware/PoseDoll44/bench/revO21/RFQ.zh-CN.md)

### O20已保存机械基线

O20为900f572 / posedoll-o20-lightweight-20260930，原ZIP和文件保持不变。保留用户已接受的双髋布局、非相邻姿势避碰及O11摩擦配合结论。

- [O20设计说明](Hardware/PoseDoll44/docs/DESIGN_REVO20.zh-CN.md)
- [O20机械设计包](Hardware/PoseDoll44/bench/revO20/PoseDoll_O20_Universal_Design.zip)

### O19历史记录

**O19 已生成腿杆对齐候选：替换4件腿部连接架，仍为188件/117种打印件。** O11独立小样的配合与可调摩擦已由用户报告通过，不增加摩擦冗余。左大腿及双小腿中间直段对齐参考骨线，右大腿中间段保留向前6mm偏移。双髋中心各外移16mm和既有整机干涉仍保留；24案例及43个中间样本无新增干涉，不能据此声称整机全域通过。

- [O19设计与验证说明](Hardware/PoseDoll44/docs/DESIGN_REVO19.zh-CN.md)
- [O19单台设计包](Hardware/PoseDoll44/bench/revO19/PoseDoll_O19_Universal_Design.zip)
- [O19腿部对照与干涉展示](Hardware/PoseDoll44/tutorials/full-doll-o19/index.html)：本地服务 `/tutorials/full-doll-o19/index.html`。

### O18已保存基线

O18已保存为 `08e8f8b` / `posedoll-o18-prototype-20260930`，342项文件和原ZIP校验通过。以下为O18发布时状态。

**O18 已生成结构简化候选：188件/117种打印件，保留46路测量与USB直连。** 相比O17少14件半壳、28枚螺钉和28枚螺母。O17已冻结为 `5a5ac22` / `posedoll-o17-prototype-20260930`。整机既有干涉仍未解决，先验证Q001/Q002关节小样，不能制造放行。

- [O18设计与已知问题](Hardware/PoseDoll44/docs/DESIGN_REVO18.zh-CN.md)
- [O18简化设计包](Hardware/PoseDoll44/bench/revO18/PoseDoll_O18_Universal_Design.zip)
- [O18三维与外壳对照页](Hardware/PoseDoll44/tutorials/full-doll-o18/index.html)：本地服务 `/tutorials/full-doll-o18/index.html`。

### O17已保存基线

**O17简化候选已冻结：202件/124种打印件。** 保留设计包、三维页面、USB固件与验证报告的原始字节。

- [O17设计与已知问题](Hardware/PoseDoll44/docs/DESIGN_REVO17.zh-CN.md)
- [O17设计包](Hardware/PoseDoll44/bench/revO17/PoseDoll_O17_Universal_Design.zip)
- [O17三维页面](Hardware/PoseDoll44/tutorials/full-doll-o17/index.html)

### O16已保存基线

**O16 单一通用测姿人偶设计候选已冻结保存。** 实体型号收敛为一个，数字高度492.14 mm，46路原始测量；保留O15 Quinn机械几何，不再分别生成两种体型。相邻机构不干涉仍是硬要求，连续全域避碰、实物标定与O16双角色UE验收尚未完成。

- [O16完整设计说明](Hardware/PoseDoll44/docs/DESIGN_REVO16.zh-CN.md)
- [O16单人偶设计包](Hardware/PoseDoll44/bench/revO16/PoseDoll_O16_Universal_Design.zip)：一套打印、采购、线束、实体profile与离线测量参考。
- [O16三维查看页](Hardware/PoseDoll44/tutorials/full-doll-o16/index.html)：先运行下方本地服务，再访问 `/tutorials/full-doll-o16/index.html`。
- 复建与核验脚本：`Hardware/PoseDoll44/cad/revO16/`。本轮不含接触修正，不要求目标角色与实体几何重合。

### O15历史基线

**O15完整数字样机保留，等待实物验证。** 480 mm UE 参考、静态摆姿采集；整机无 1.2 kg 硬门槛，允许手托。采用 FDM 打印与现成金属小件，不需要定制机加工金属件。91 cm 方案继续保留为备用。

- [本次提交与审查入口](Hardware/PoseDoll44/docs/REVIEW_HANDOFF_O15.zh-CN.md)：先读此页，再查详细设计、证据和未验证项。
- [O15 详细审查请求](Hardware/PoseDoll44/docs/REVIEW_REQUEST_REVO15.zh-CN.md)；[数字结果汇总](Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1/FINAL_BATCH_SUMMARY.json)。
- [Quinn 统一测试包](Hardware/PoseDoll44/bench/revO15/PoseDoll_O15_Quinn_Prototype.zip) / [Manny 备选包](Hardware/PoseDoll44/bench/revO15/PoseDoll_O15_Manny_Prototype.zip)：只选一套，每套 214 种文件、273 件打印件。
- [中文装配与测试说明](Hardware/PoseDoll44/bench/revO15/guide.html)；[静态采集软件设置](Tools/PoseDollHardwareBridge/README_O15.zh-CN.md)。HTML 请下载打开或通过下方本地服务查看。

本次提交同时收录此前尚未提交的 O5—O14 迭代和 O15 使用的历史依赖。各轮已封存文件保留原字节，旧文档中的“当前”指该轮检查点。O15 的采样几何检查、切片、电路规则、固件构建和 UE 桥接已有数字证据；完整强度、保持力、耐久、带线运动和电子实测仍未完成。

历史入口：[O4](Hardware/PoseDoll44/docs/REVIEW_REQUEST_REVO4.zh-CN.md)、[O3](Hardware/PoseDoll44/docs/START_HERE_REVO3.zh-CN.md)、[O2](Hardware/PoseDoll44/docs/START_HERE_REVO2.zh-CN.md)、[O 初轮](Hardware/PoseDoll44/docs/START_HERE_REVO.zh-CN.md)。不要把历史制造说明与 O15 混用。

以下为备用版的历史基线：

- **机械基线为 Rev N1**：两款分别按 UE 人物参考比例设计，参考身高约 91 cm；胸前大挡板已取消，左肩局部刮碰已修正。
- **下一项为“局部采集 + 外置电源/USB 接口盒”**：方向已确定，新电路板、安装结构和线束尚未实施。
- **小型化仍待比较**：当前尺寸不是已证明的下限，不能直接缩放现有文件，也不能认定重新设计的小型关节必然昂贵。
- 44 个协议槽中，41 轴测量，骨盆 3 轴固定参考；整体位置和全部整体旋转在 UE 调整。
- 当前交付是数字原型候选，尚未实物鉴定。

## 阅读入口

0. [O15历史方案](Hardware/PoseDoll44/docs/REVIEW_HANDOFF_O15.zh-CN.md)。以下 Rev M/N 文档用于备用版。

1. [最新 Rev N1 设计入口](Hardware/PoseDoll44/START_HERE_REVN.zh-CN.md)
2. [胸部修订与设备外置方案](Hardware/PoseDoll44/docs/CHEST_AND_EXTERNAL_REVN.zh-CN.md)
3. [尺寸、磁铁和关节小型化评估](Hardware/PoseDoll44/docs/SIZE_REVIEW_BEFORE_EXTERNAL.zh-CN.md)
4. [制造说明](Hardware/PoseDoll44/docs/FABRICATION_REVM.zh-CN.md)、[装配说明](Hardware/PoseDoll44/docs/ASSEMBLY_REVM.zh-CN.md)、[测试和校准](Hardware/PoseDoll44/docs/BUILD_AND_CALIBRATE_REVM.zh-CN.md)
5. [迁移记录和验证](docs/MIGRATION.zh-CN.md)

Rev M 文档描述原完整基线，使用时应应用 Rev N1 的取消件和左肩修订。更早版本与 `planning/` 是历史依据，不能混作当前制造说明。

## 目录组织

| 路径 | 用途 |
|---|---|
| `Hardware/PoseDoll44/cad/` | 参数化机械模型，保留当前模型仍引用的历史模块 |
| `Hardware/PoseDoll44/electronics/` | 原生 KiCad 工程、符号/封装及板级 STEP 输入 |
| `Hardware/PoseDoll44/mechanical_manifest/` | 轴、接口、比例和网络定义 |
| `Hardware/PoseDoll44/docs/`、`verification/` | 设计说明、数字检查和原型验收依据 |
| `Hardware/PoseDoll44/generated/` | 总装、打印件、查看器、交付清单和本地 CAD 缓存 |
| `Hardware/PoseDoll44/reference/`、`references/` | UE 参考数据及元件资料 |
| `Hardware/PoseDoll44/harness/` | 两款线束与下料表 |
| `Firmware/PoseDollFullBody/` | 六节点完整固件与主机端 C 核心测试 |
| `Firmware/PoseDollHardware/` | 早期单关节固件，历史用途 |
| `Tools/PoseDollHardwareBridge/` | 诊断、校准、数据转换和测试 |
| `Tools/PoseDollSimulator/`、`Shared/` | 硬件需要的协议/运动学代码及配置快照，不含模拟器 GUI |
| `planning/` | 原始规划包副本，父目录中的原下载包也保留 |
| `scripts/` | 独立仓库的检查、构建和查看器入口 |
| `.local/` | 本机迁移清单、运行结果等，不入 Git |

保留 `Hardware/`、`Firmware/`、`Tools/` 层级，以保持已有相对路径及历史资料的可追溯性。协议快照来源与逐文件哈希见 [software_snapshot.json](docs/software_snapshot.json)。

## 环境与离线检查

在本目录打开 PowerShell。本机已经建立独立 `.venv`；新克隆可执行：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/check_repository.py
.\scripts\Build-Design.ps1 -Stage OfflineTests
```

离线检查包括协议配置、Python 测试、C 核心测试和 C/Python 数据帧一致性；不连接硬件或操作 UE。C 测试需要 Visual Studio C 工具链，`-VcVars` 可指定 `vcvars64.bat`。本机迁移后结果为 **81 个 Python 测试、9 个 C 场景通过，数据帧逐字节一致**。

## 打开三维查看器

O15 使用以下命令启动服务，然后访问 `http://127.0.0.1:8769/tutorials/full-doll-o15/index.html`（脚本原来的启动提示仍指向 O14，以此 URL 为准）：

```powershell
python scripts/serve_posedoll_tutorials.py --port 8769
```

提交资料可在新克隆中用 Python 标准库复核：

```powershell
python scripts/verify_o15_review.py
```

以下命令与说明保留为旧版查看器入口：

```powershell
.\scripts\Start-Viewer.ps1
```

默认根据 `verification/revO3/latest.json` 打开 Rev O3 查看器，当前为 `http://127.0.0.1:8874/generated/revO3/runs/o3_20260924_r3/review.html`；通过 `-Revision revN` 打开 91 cm 备用版，仅绑定本机。`-NoBrowser` 只启动服务；端口冲突时可用 `-Port` 指定另一端口，不会自动终止其他进程。

Rev O3 的当前及历史检查运行、HTML、网格、STEP、原生 KiCad 板件、固件产物与原始日志随本次审查提交收录；宿主 C 编译产物通过逐件哈希的 portable ZIP 保存。Rev O 第一轮的 HTML、轻量网格、布局数据及三档关节 STEP 也保留。十份体型布局 STEP 下载需先用 `Build-RevO.ps1 -Stage CAD` 重建。91 cm 备用查看器仍依赖未纳入 Git 的大型网格，需复制旧输出或重建。

## CAD、电路和固件

- CAD：CadQuery 2.7。现有 `Hardware/PoseDoll44/tools/run_cad.py` 可使用本机 CQ-editor 2.7 的环境，需要 CQ-editor 保持开启、Python 版本匹配；也可自行安装常规 CadQuery 环境。
- 电路：KiCad 10，打开 `electronics/` 中对应 `.kicad_pro`。搬迁前已打开的 CQ-editor/KiCad 文件，应从新目录重新打开，避免保存回原路径。
- 固件：ESP-IDF 6.1、ESP32-S3。旧构建缓存已保留，但含旧绝对路径；不要直接在其中增量构建。
- 布线工具：Freerouting 2.4.1 JAR 保留在本机 `Hardware/PoseDoll44/tools/vendor/`，不入 Git；许可证与说明保留。

```powershell
.\scripts\Build-Design.ps1 -Stage CAD
.\scripts\Build-Design.ps1 -Stage Firmware
```

CAD 阶段生成/复核 Rev M 完整基线，耗时较长。Rev N1 的修订脚本位于 `cad/revN/`，依赖 Rev M 完整输出及其复核结果，不是上述命令自动生成的另一套角色。当前源码与必要 CAD 输入纳入 Git。

新构建入口使用本仓库 `.venv`。Firmware 阶段会把检测到旧工程路径的节点缓存移入 `.local/legacy-firmware-builds/` 后重新构建，不删除缓存、不烧录。旧脚本中的 CQ-editor、KiCad、ESP-IDF 安装盘符仍是本机配置；换电脑须配置工具路径，历史工具可参考 `local_toolchain.example.json`。UE 参考重新导出需要原 UE 工程及插件，但导出脚本现在将数据写到本设计仓库。

## Git 与本地成果

Git 收录设计源码、KiCad 工程、固件、必要板级 STEP/角色参考输入、协议快照、说明、交付元数据和检查记录。`.gitattributes` 保留原行尾，避免检出时破坏来源文件的字节哈希。

大型总装 STEP、查看器大网格、CAD 缓存、ESP-IDF 构建目录、Python 环境和第三方工具二进制保留在磁盘，由 `.gitignore` 排除；没有启用 Git LFS。Rev O 审查快照额外收录三档单关节总成 STEP、两个 A 级配合样片 STEP/STL、轻量查看器与本轮原始编译/ERC/DRC 日志，Rev O3 本次另显式收录三个检查运行及其可追溯产物，仍未放开其他版本的整个生成目录。其他机器如需完整本地成果，应另外复制 `Hardware/PoseDoll44/generated/`。**推送 Git 不等于备份全部 6.87 GB 本地成果。**

现有验证报告保留为历史快照，迁移后的路径修复和检查另列记录；没有把迁移当成新一轮全身工程验证。本轮提交由使用者推送到远端；审查应指定 `design/revO-desktop-external` 分支和所读取的完整提交号。
