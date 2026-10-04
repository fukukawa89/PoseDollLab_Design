# PoseDoll Rev O2 独立审查及 O3 执行计划

审查日期：2026-09-23。
固定提交：`239d4430cec49eecaf12c37f1ec4717055d3fbfe`。
分支：`design/revO-desktop-external`。被审查运行：`o2_20260923_r1`。

本报告是设计审查和下一轮任务书，不是制造文件。没有修改远端仓库，没有采购或烧录。

## 0. 范围与结论

通过 GitHub 连接器读取 REVIEW_REQUEST_REVO2、主要机械/电路/固件/证据生成器，以及 status、mechanics_analysis 和部分电子原始记录；读取上轮审查任务原文。完整 Git 克隆因当前运行环境 DNS 失败而未获得。没有重跑原项目全 CAD、KiCad、ESP-IDF、107 个 Python 测试或全部原始验证；这些通过项仍是仓库报告，不是本次独立复现。

本次实际执行了 `audit_revo2_focused.py`：使用 CadQuery 2.8.0 按源码重建指定的制动盘、定位销、支柱和底座凸台，执行局部 BRep 求交；另用 SciPy 运行接触约束反例，并执行质量、力矩、时序字段和维护调度的条件计算。它不是原 CadQuery 2.7 全模型重建，不包含外部 STEP 的完整总成验证。原始结果在 `focused_results.json` 与 `focused_run.log`，脚本与结果均随包交付。

总体判断：真实螺纹、径向装配、14 mm 双支承、双面制动、近五远四拆板和无重复 EPOCH 风暴的方向可以保留。但 L6 仍有传感板底座未固定和寿命状态下定位销碰盘的 P0 问题；载荷模型、质量、真实装入空间、统计器和恢复调度均未闭合。下一轮不应放大人偶、增加弹簧力或全面复制 L6。

证据等级：E＝源码/报告直接证据；C＝明确假设的计算；G＝本次局部几何/数学反例已执行；U＝待建模或实测。G 不意味着整机通过。

## 1. R01–R10 判定

| 条目 | 旧问题是否修复 | 本轮关闭判定 |
|---|---|---|
| R01 后盖保持 | 零啮合旧缺陷已在名义几何上修复；有实际螺旋、单体杯和锁定件。 | 部分关闭。参考螺纹不是标准公差认证；全部预紧范围/磨损/装配力矩和薄壁强度仍待鉴定。 |
| R02 装不进去 | L6 的分体轴承盒、分体衬套和从后端加载具有名义装配路径证据。 | 部分关闭。其他关节族仍是 O1 质量参考；实际小螺钉工具、输出连接器、配合公差未完成。 |
| R03 夹紧与测角基准 | 名义力路改为浮动盘双面夹紧，轴向定位另列。 | 部分关闭。新增磨损定位销碰盘；带扭矩轴向滑动可能把寄生力传回转轴，不能用字符串力路列表替代机械验证。 |
| R04 支承精度 | 支承跨度由 4.6 mm 改为 14 mm，间隙预算更具体。 | 部分关闭。夹紧圆度、衬套与壳体定位、轴挠曲和反向实测仍缺失。 |
| R05 板位 | 已实现真正近五远四原理分区及实封装布局，不再仅裁短旧板。 | 部分关闭。完整 PCBA/接头、胸肩机构和运动线束仍未装入。 |
| R06 质量/COM/支撑 | 真实单件 COM、材料分类和非零头部 COM 是实质改进。 | 部分关闭。接触点没有几何激活条件；部分质量仍分配或重叠；总预算 1635.59 g。 |
| R07 电气完成度 | 热孔改为明确 0.3 mm/0.65 mm 的新图形，而非无依据放宽规则。 | 未关闭工程门槛。三板仍未布线，整套其他节点/G0/保护没有完整新验收。 |
| R08 风暴与时序 | 重复同一 EPOCH 不再回复，定向握手与正常采样分开。 | 旧风暴已关闭；整体部分关闭。掉线维护抑制所有节点 SYNC；统计器把两种时间混用；真实台架未跑。 |
| R09 装拆/动作 | 中空工具、径向路径及有限采样检查有进步。 | 部分关闭。传感板支柱没有底部保持；EOL/公差状态、配合线和多轴动作未覆盖。 |
| R10 证据链 | 唯一 run_id、部分依赖即时哈希、集合核对和失败传递改善了旧问题。 | 部分关闭。消费者读取的逐件 STEP/板件并未全部在生产者结束时锁定；若干门槛/实体数量写死。 |

不能因为还有问题就把本轮的名义通过一律判成假；同样不能把名义通过扩大成能制造、能保持精度或能装入整机。

## 2. 优先级问题表

P0：B 级单关节制造前必须关闭。P1：相关单臂/台架/整机阶段前必须关闭。

| ID | 级别/证据 | 触发及影响 | 下一轮修法与验收 |
|---|---|---|---|
| O3-01 | P0/E+G | `sensor_post_*` 底面 z=20 与壳体凸台顶面相贴；没有连接到底座的紧固件或一体结构。PCB 顶部螺钉最低 z=26.295，仍高出底座 6.295 mm。 | 优先把各侧支柱与对应半盒一体化，保留硬基准和可拆顶夹；或用有肩定位的金属紧固方案。做固定/转动/滑动/接触约束图，证明没有可自由拔出的板架。 |
| O3-02 | P0/E+G | 前摩擦片厚 0.6 mm，定位销伸出 0.5 mm；前片仅磨损超过 0.1 mm 即可能碰盘。报告总磨损 0.6 mm 的对称分配触发明确穿插。 | 移除摩擦工作面内会露头的定位销；采用金属背板与外缘止转/保持。维持总磨损预算，扫描非对称磨损、压缩和公差。 |
| O3-03 | P0/C | 两颗 Ø0.6 定位销承担完整单面扭矩时，326 N、μ=0.22 的等分直接剪应力约 103 MPa；衬片孔壁承压和其他小键未算。 | 对全扭矩链按最大实际弹簧力和最高摩擦条件验算，不只算螺纹。不得在没有结合强度数据时给背面摩擦/胶接免费承力信用。 |
| O3-04 | P1/E+G | 支撑平衡只用 XY 与非负力，不验证高度、法向、间隙或接触。可将力分给悬空身体部位，1.8 N·m 不可直接用于定型。 | 先进行真实接触激活；无壳体时输出 ASSUMED/UNRESOLVED 而非物理可行。分工况、分支撑和不确定性计算。 |
| O3-05 | P1/E+C | 991.59 g 关节参考子集加 644 g 分配共 1635.59 g；超过目标 435.59 g，且其他关节未完整定型。 | 分轴选型和共享多轴结构；逐项消重而非删除分配数字；保留电路/线束和新增紧固件。 |
| O3-06 | P1/E | 目前包装筛查用预设盒子和有限角点/位置，不由完整 PCBA 与真实机构驱动；4 mm 弯曲半径无实测依据。 | 真实占用体、服务扫掠和功能禁布区分层；局部刚体坐标中的旋转/平移搜索；线材型号及动作路径冻结后再认证半径。 |
| O3-07 | P1/E+C | 一个节点持续掉线即可约每 100 ms 占用整帧维护，健康节点也停采。 | 快速有限重试后指数退避；进一步在可证明的帧间余量中分段握手，健康采样优先。分别统计健康节点和完整全身可用率。 |
| O3-08 | P1/E+C | 统计器把 USB 中的 G0 SYNC→END 包络当成节点采样时间，与 8 ms 比较，正常批次也会被误判。 | 保持 USB PD41 v1 语义；采样 8 ms 用原始 END 或节点 trace，USB 仅作新鲜性与保守包络统计。补低帧率、长暂停、重启会话测试。 |
| O3-09 | P1/E | `joint` 即时输出哈希只有 joint.json 和总 STEP，装配却读取逐件 STEP；类似问题存在 PCBA 消费链。 | 生产者逐文件 manifest/Merkle 根；消费者校验所有实际读取文件。插入变异测试，替换一个 STEP 必须 BLOCKED。 |

## 3. 机械反例与直接替代

### 3.1 传感板架必须有底部保持

`cad/revO2/compact_joint.py` 中轴承座两侧凸台范围到 z=20；随后 `sensor_post_*` 从 z=20 开始。顶部夹板螺钉只固定夹板与支柱上部，没有穿入壳体。支柱的孔也只从支柱自身切出，没有在底座生成对应螺纹。

本次按同一尺寸重建一侧支柱与凸台：在 z=0 偏移时只是面接触；抬起 0.1、1、5 mm 均无穿插，间隙分别为对应偏移。结合源码缺少底部保持，存在板架脱离的自由度。该局部测试不是整机跌落模拟。

推荐把支柱并入对应的 L/R 半盒，保留当前外包络和 PCB 顶部可拆夹板；支柱之间不能跨接后妨碍径向合拢。合并后零件数量会改变，应通过零件身份集合和设计变更记录更新验收，不能再靠写死“48 件”判断完整。

传感板、连接器插拔力和线尾牵引力需通过壳体固定结构传递，不通过测角磁铁或活动轴。尺寸与材料改变后重新生成气隙、公差、刚度和走刀/螺丝刀空间。

### 3.2 磨损后销头碰盘：已复现

源坐标：前摩擦片 z=-0.6…0；前定位销 z=-0.5…0.05；制动盘主盘 z=-2.1…-0.6。前片磨损 wf 后，盘向正 z 移动 wf。若前后各磨损 0.3 mm，后压板和后销移动 wf+wr=0.6 mm，维持原弹簧工作高度。

| 状态 | 前销/盘交叠 mm³ | 后销/盘交叠 mm³ |
|---|---:|---:|
| 新件 | 0 | 0 |
| 前片磨损 0.15 mm | 0.0282743 | 0 |
| 两片各磨损 0.3 mm | 0.1130973 | 0.0565487 |

前销顶到盘的磨损量级只有 0.1 mm，后销约 0.2 mm。这里只计算刚体磨损几何；压缩、偏磨、公差可能进一步改变剩余间隙，不能用无材料模型的名义状态抵消风险。

推荐保留浮动双面制动，但把止转特征移到旋转工作环之外。优先比较“有金属背板的可更换摩擦片＋外缘止转耳/机械保持”，背板和摩擦层结合强度由供应方限定。工作环仍沿用当前尺寸进行比较，不直接加大关节。

止转耳初始探索可采用 2–3 个分布位置、毫米级有效颈部与承压面积；必须基于具体力矩、材料和圆角重新计算。不能把 0.6 mm 销换成稍短销就结束：磨损碰盘和扭矩承载是两个不同门槛。

应输入前后独立磨损值、衬片受压缩量、装配误差、弹簧公差和盘偏摆。至少验证 (0,0)、(0.3,0.3)，并检查满足总磨损预算与最小剩余衬片厚度的偏磨组合。保持 0.6 mm 原总预算，不允许通过缩小它掩盖干涉。

### 3.3 从“预紧力路”扩展到完整“扭矩链”

当前 R2 确实把大部分名义轴向夹紧载荷从测角轴定位中分离，值得保留。但 `nominal_force_path` 是设计声明，字符串不含轴名不等于所有状态无寄生轴向力。

必须绘制并验算：输出连接→测角轴→整体凸键→浮动盘→两摩擦面→各定子/背板→压力板止转键/杯体→支承与外部结构。每一级列接触、摩擦、正向键合、轴向自由度、最大载荷和失效方式。

326 N 与 μ=0.22 条件下，单面扭矩约 0.6258 N·m。若两颗半径位置 10.7 mm 的 Ø0.6 销分担全部单面扭矩，每销约 29.24 N、直接剪应力约 103.43 MPa；μ=0.08 时也约 37.61 MPa。这是风险筛查，不是已知材料破坏判断。真实负载分配、销根弯曲、衬片孔壁承压、胶接/背面摩擦能力均要有数据。

带扭矩浮动盘沿键滑动可能产生轴向摩擦，支承和轴向定位须承受这部分寄生力。测试要覆盖施加扭矩的轴向滑移、反转回差、最大/最小预紧、磨损和温度，不能只手推空载盘。

## 4. 接触、质量与关节族

### 4.1 先修正物理工况，禁止按可疑 1290 N 选簧

`study_revo2.py::support_study` 的反力可行域仅包含 ΣF=W、ΣxF=x_COM W、ΣyF=y_COM W、F≥0。其数学极值对所假定点集有效，但缺少实际接触前提。侧卧等模式把多个 owner 周围的点都加入；点可能不在同一地面，也可能并未触地。

本次用同样平衡约束构造上下两组 XY 投影重合的接触点：没有间隙约束时，20 mm 高处的点可以承担全部 10 N；强制离地接触力为 0 后为 0 N。这验证缺少接触激活条件的后果，不是重算整个人偶 1.8 N·m 的实值。

下一步：每个工况记录根变换、关节角、真正支撑对象、地面/手托/座面的几何和法向。平面接触至少满足 g≥0、λ_n≥0、g·λ_n=0；有切向力时加摩擦锥及全六维平衡。先判断几何可接触，再求反力。反力不唯一时用有物理依据的柔顺模型或报告合法接触集的范围，不任选一个“好看”的分配。

对未建模壳体保持 UNRESOLVED；现有结果只标成过宽假设集合的上界，不用于弹簧定型。单足当前假设 COM 越界不等于人偶不能摆单足姿势，应先区别无手托站立和手托摆姿工况，不自动新增或取消用户的支撑要求。

### 4.2 质量账要消重，但不能靠消重假装解决全部超重

当前分配项合计 644 g，关节参考子集 991.59 g，总 1635.59 g。对 1200 g 目标超出 435.59 g。644 g 包含 150 g 框架、90 g 线束、100 g 未决紧固件/弹簧、130 g 外罩、127 g 八 PCBA、35 g 保护与 12 g 新链路。

详细 L6 已含一些弹簧/螺钉，100 g 分配可能部分重叠。应通过 part_id、数量、父总成和“分配替换归属”逐项移交。其他关节仍是未完整定型的 O1 参考，不能一次删除全部 100 g。即使理论上删除全部 100 g，也还有约 335.59 g 差额，因此不能把超重只解释为重复计算。

若其他分配不变，41 轴关节总预算只剩 556 g，平均约 13.56 g/轴。这是任务约束而非保证可实现的重量。14 个旧分配为 L6 的轴全部换用约 39.83 g 大模块，对紧凑目标压力很大。

推荐：修复 L6 后保留为高载荷参考；按经修正的工况分别选择大、中、小模块，并在肩、髋、胸腰嵌套时共享固定架、相邻支承和板托。不得删轴或改变轴语义，也不能为了共享结构强行采用错误同轴/共点几何。每轮报告净减重：删掉什么、增加什么、材料/工序变化及验证代价。不得用旧不完整 S4/M6 的质量证明新成品达到目标。

## 5. 电子、实际包装与线束

保留近端五路＋远端四路，先不更换 MCU/传感器。SN74LVC125A BQA 的实际封装采用比旧 TSSOP 紧凑的路线成立；但电路必须完整重布，不可把未布线布局当成可生产板。

### 5.1 包装检查需要由真实输入驱动

`packaging_revo2.py` 当前用 [15,28,32] / [15,22,38] 等预设盒子做角点筛查，依赖 pcba_geometry 的执行完成，却没有真正从完整 PCBA 几何构造这些占用体。其有限 Z 旋转/平移失败只代表当前试位失败。`audit_layout.py` 的部分插头以 courtyard 中心推导配合位置，且仍缺 J1/J2/J3 配合模型，不能宣称实际插合基准已确认。

新增同一元件的三类体：physical_solid（真实占用）、service_sweep（装拆/弯曲扫掠）、functional_keepout（RF、电气间隙等）。用器件坐标系、配合基准和 part number 驱动，不能让热焊盘/连接器方向或配合高度仅靠通用类别赋值。缺失 3D 模型可用厂家最大尺寸包络保守替代，但必须记录来源及尚未认证条件。

胸腔必须同时放入 N2/N3/N4、真实肩/胸腰结构和接头，不允许孤立单板各自“能放”便通过。按部件所属刚体变换到局部坐标搜索，包括真实纵轴方向、可用腔体、壳厚和工具通道。

### 5.2 顶入与侧入必须比较总高度和服务路径

保留当前顶入 J50 为一个候选，同时恢复侧入作为有真实尺寸的对照。顶入可减少沿板平面的插拔需求，但增加板法向的插头和线弯高度；侧入相反。选择以完整总成最小干扰为准，不以板框面积最小为准。

当前 14 芯、单线 OD≤0.8 mm、填充率 0.65 对应等效束径约 3.71 mm；4 mm 弯曲半径与该尺度相近，但仅凭此不能断言某线材可用或不可用。没有材料/绞线结构/连续弯曲寿命证据前，不把从旧 12 mm 候选改为 4 mm 的数字当作已获得的空间。两半径均可作为敏感性研究，合格值须绑定具体线束和测试结果。

### 5.3 失电三态不能靠器件名字推断

TI SN74LVC125A Rev T 的电气表没有给出可用于本设计的 VCC=0 Ioff 保证；IOZ 是在供电条件下测的三态泄漏，不能替代它。源码部分链路驱动 OE 固定为低，且 MISO 是共享返回。需审查远端 V+ 断线、地线断线、局部掉电、复位/上电默认状态及总线争用。

先让供应方给出可验证的 OE/电源排序/隔离实现；若必须换器件，另做有明确 Ioff/掉电输出条件的候选比较、引脚/封装和时序验证。本任务不指定未经核对的新型号。USB、CAN 和内部分路短路保护仍须分别完成；旧 5 V 硬件禁止直接供 12 V。

### 5.4 天线净空是功能约束，不是买来的实体

Espressif 推荐天线超出主板边缘，并为无线性能保留净空。固件/硬件若确实是无无线需求的纯 CAN 设备，可以建立“无线禁用、无 RF 性能承诺”的设计模式进行另行评审；但不能在 CAD 中无说明删除净空以通过，更不能删掉模块实体、焊接、电气、热和结构间隙。默认继续保留现有厂家无线建议；这不是当前方案一定能塞入胸腔的承诺。

## 6. 固件与统计：分开三个时间/可用性概念

### 6.1 相同 EPOCH 风暴已修复

`pd41_session.c` 同 epoch 返回 O2_NO_ACTION，加入使用定向挑战与 BOOT 关联，JOIN_OK 后才接受 SYNC。可继续保留；不必退回 O1。仍需丢包、乱序、延迟、重启/旧会话及长时间恢复台架。XOR 关联不是安全认证，本装置的可靠性测试不能被描述成抗恶意认证。

### 6.2 单坏节点不应长期让健康节点一起停采

现有 `main.c` 在有维护目标时不发 SYNC，并输出所有节点缺失批次；`o2_select_maintenance` 最小间隔 100 ms。一个节点持续缺失时，在理想 16667 μs 周期里每 60 批约有 10 个维护批、50 个正常采集批。健康节点的可获取新数据机会约 83.3%，不是实测帧率；全部健康且稳定加入时这个问题不存在。

O3 两级修改：首先限次数快速重试、每节点指数退避、超时清理和公平游标，保留故障记录；随后把入网控制拆为可跨帧状态机，放到严格截止后的空闲窗口或明确预留的低优先级时隙，健康采样优先。原 14 ms 截止到 16.667 ms 仅约 2.667 ms，是否足够必须算控制帧、驱动与抖动，不能直接宣称放得下。若缺少可证明时隙，报告受限降级而非隐藏停采。

统计同时给出：全身完整新鲜率、各在线健康节点新鲜率、明确维护损失、重入时间、最长无更新间隔。缺一个节点时完整全身率必然不达正常工作指标，但不应把其他节点的额外停采藏起来。

### 6.3 8 ms 统计器语义错误：直接可定位

`pd_end` 验证节点上报的 delay+span≤8000 后，保存的是 `now - cohort.start_us`。`pd_finish` 把该值写到 `timing[i][1]`，即 USB PD41 v1 暴露的是 G0 SYNC 到 END 收到的保守包络，并非原始节点采样跨度。

`capture_metrics_revo2.py` 又把 `node_timing_us` 的 delay+span 与 8000 比较，进而把它作为 `fresh_complete_normal_rate` 的分子。这是两个时间含义混用。

反例：节点 delay=200 μs、span=6200 μs，采样 6.4 ms 合格；G0 在 11 ms 收到 END，严格 14 ms 也合格；USB 中 timing=[0,11000]，当前统计器却按超出 8 ms 扣除。

修复不得改变 USB v1 字段含义或把 8 ms 放宽到 14 ms。USB 计算完整/正常/新鲜率与真实输出间隔；节点 8 ms 用原始 CAN END 或另行关联的节点日志，G0 严格 <14 ms 用共享时钟 CAN trace。只有 USB 文件时，8 ms 验证应为 NOT_OBSERVABLE。还要用时间戳检查有效 60 Hz 与 ≥30 min；连续序号不能证明发送频率。显式会话重连后分别统计，不让重启后的数据被旧 Decoder 会话静默排除而只汇总旧段。

## 7. 证据链：已经改善，但应补消费闭环

`Run.step` 对声明的 expected_paths 做即时哈希是进步。然而 `joint` 只把 joint.json、L6_R2_assembly.step 列为即时输出，`check_assembly.py` 实际读取 48 个逐件 STEP 和工具 STEP。这些文件在消费者执行前没有全部按生产者原哈希复核；运行结束才给它们哈希不能证明消费的是最初那版几何。

必须新增逐件输出 manifest：part_id、文件哈希、材料、owner、坐标系、单位、体积/质量摘要。消费时核对每个文件。PCB 导出、配合模型、布局 JSON 和源库也按实际读取集合执行。补全几何内核、PCB 模型库、编译环境依赖版本/摘要；声明跨机缺失是 BLOCKED_TOOL/INPUT，而非 CAD 失败。

变异测试至少覆盖：生产者通过后替换单个 STEP、删除工具 STEP、替换配合头 STEP、变更板框不更新 layout、遗漏角色/轴记录、依赖失败后遗留旧金样、篡改 source/报告哈希。不能得到相关 V0/V1 通过。

不要把固定 48 件、至少 35 步当作完整性定义。应以本轮 BOM 的准确身份集合和装配 DAG 为源，检查零件是否真正固定/受约束，以及每一有效生命周期状态的运动边界。源代码字符串 `preload_path` 应标 DESIGN_DECLARATION，不应单独贡献机械通过。

## 8. O3 文件改动和依赖顺序

所有以下新文件名为建议，不声称仓库已有。推荐在新 `cad/revO3/` 与新运行目录工作，保留全部 O1/O2 和 Rev N1；禁止再次 Initialize 或覆盖 o2_20260923_r1。

### A. 先补反例和证据（其他工程可并行）

修改 `scripts/revo2_evidence.py` / 对应 O3 版本、`run_revo2.py`、`report_revo2.py`。
新增 `mechanical_manifest/joint_constraints_revO3.json`、`lifecycle_states_revO3.json` 与逐件产物清单。
新增回归：自由拔出传感板架、定位销 EOL 碰盘、悬空点承力、11 ms 包络误当 8 ms、单 STEP 替换。

### B. P0 单关节闭合

从 `cad/revO2/compact_joint.py` 派生 O3。
落实一体板托/可核验底部紧固、外缘止转摩擦件、完整扭矩链和固定/转动/滑动约束图。
扩展 `check_assembly.py`：新件/磨损/偏磨/公差/预紧多状态，组内与组间碰撞，所有实际紧固工具、输出接头和真实 sensor 插头。
只保留有明确批准依据的接触分类，不用忽略所有接触或缩小阈值过关。

### C. 支撑与质量（在最终强度选型前）

重构 `study_revo2.py`，将 contact geometry、工况、反力求解、质量来源和关节选型分离。
新增 `support_cases_revO3.json`、`mass_ledger_revO3.json`、`axis_family_selection_revO3.json`。
无法建模接触的工况不得输出可制造弹簧规格。逐项抵扣详细 L6 已覆盖的预算，同时补其他关节遗漏。

### D. 真实多轴及电路联合包装

修订 `build_revo2_electronics.py`、`audit_layout.py`、`packaging_revo2.py`。
先做肩/髋/胸腰真实嵌套与真实孔轴偏置，把单轴共用结构整合；同时完成胸腔 N2/N3/N4 与一条完整手臂的实际 PCBA/接头/线束。
对顶入/侧入、宽/窄板方案给出实际总包络、维护路径、增减质量与加工差异，择最小干扰者。
不能把 39.83 g 的 L6 复制到所有轴之后只靠镂空减重。

### E. 统计修复和七节点恢复逻辑（可以现在并行）

修改 `capture_metrics_revo2.py`、Rev O2 后继固件 `main.c` / `pd41_session.*`，扩展 session tests。
正常 PD41 v1 兼容、44 槽语义和六采集节点不变。构建七角色，测试全部健康、单节点持续缺失、JOIN_OK 丢失、G0/节点重启、慢恢复与业务队列积压。
本步骤可在桌面测试夹具上开展，不必等整机外壳设计完毕。电气台架仍必须有保护和已审核布线；临时测试板通过不能冒充最终紧凑板通过。

### F. 样件与最终验收

B 级关节样件只有在对应 P0、图纸/材料/紧固/公差与供应方审核完成后才放行；不要求先完成全身才允许测摩擦材料和单关节。
PCB 布线/保护和单关节台架可并行；完整单臂须真实电路与线束；全身在关节族、实际 profile、尺寸/质量和动作全部闭合后进入。

## 9. 不变验收标准和新增检查

- 全部 41 测量轴和骨盆 3 固定槽，六采集节点＋外置 G0；Manny/Quinn 各自比例，完整本体目标 ≤500 mm、硬上限 ≤600 mm，本体含全部内部件目标 ≤1.2 kg。
- 旧 Rev N1 和历史运行原位保护。尺寸候选不得替换成无证据“更大就能放”。
- 数字：完整材料/约束/接口/BOM、每个实际消费文件的来源哈希、真实配合工具、装拆 DAG、磨损及公差状态、动作路径、完整电路 ERC/DRC 和零未连接。
- 新增 P0：修复前本包两项局部反例必须可复现；修复后用同样物理需求和扩展状态集证明无失控自由度、无定位件碰盘。不得删除反例或改小磨损预算。
- 实物：校准后全行程误差≤1°，重复性≤0.3°；真实线束 60 s 持姿漂移≤0.5°；邻轴寄生≤0.3°；至少1000次代表往返初筛。特别记录线缆拉力、插拔力、反转回差和加载浮动盘滑移。
- 电气：500 kbit/s、60 Hz、节点采样窗≤8 ms、G0完整批次严格<14 ms；≥30分钟健康台架完整新鲜率≥99.9%，陈旧/故障冒充正常为0。原始 END、总线 trace、USB序号/时间戳和诊断分层保存。
- 故障：逐节点掉线/重启、供电断线和受控短路（由具备条件的供应方执行）、JOIN消息丢失/重复/延迟；健康节点更新和恢复损失明确列出。
- 未执行为 NOT_RUN，缺少直接观测量为 NOT_OBSERVABLE，缺少依赖为 BLOCKED；不改成 PASS。

## 10. 只有用户需要决定的取舍

现阶段不需要放宽尺寸、质量、自由度或动作。普通结构、电路和工具实现由设计方选择并给证据。

只有在具体报价与合格样件证明原目标冲突时，再询问是否接受：超过质量目标/改变身高目标、改变直接掰动的方式、放弃原来明确要求的独立支撑姿态、增加显著成本的精密工序，或改变有明确用户用途的无线/控制器/传感器功能。不能把常规未完成设计推成用户二选一。

## 11. 源码与厂家来源

以下源码链接全部固定到审查提交。链接是审查定位依据，不是本地已下载完整仓库的证明。

- [Hardware/PoseDoll44/docs/REVIEW_REQUEST_REVO2.zh-CN.md](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/docs/REVIEW_REQUEST_REVO2.zh-CN.md)
- [Hardware/PoseDoll44/cad/revO2/compact_joint.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/cad/revO2/compact_joint.py)
- [Hardware/PoseDoll44/cad/revO2/check_assembly.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/cad/revO2/check_assembly.py)
- [Hardware/PoseDoll44/cad/revO2/export_joint.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/cad/revO2/export_joint.py)
- [Hardware/PoseDoll44/cad/revO2/audit_layout.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/cad/revO2/audit_layout.py)
- [scripts/study_revo2.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/scripts/study_revo2.py)
- [scripts/packaging_revo2.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/scripts/packaging_revo2.py)
- [scripts/build_revo2_electronics.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/scripts/build_revo2_electronics.py)
- [Firmware/PoseDollFullBody/revO2/main/main.c](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Firmware/PoseDollFullBody/revO2/main/main.c)
- [Firmware/PoseDollFullBody/revO2/main/pd41_session.c](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Firmware/PoseDollFullBody/revO2/main/pd41_session.c)
- [Firmware/PoseDollFullBody/revO2/main/pd41_session.h](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Firmware/PoseDollFullBody/revO2/main/pd41_session.h)
- [Firmware/PoseDollFullBody/revO2/main/CMakeLists.txt](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Firmware/PoseDollFullBody/revO2/main/CMakeLists.txt)
- [Firmware/PoseDollFullBody/main/pd41_core.c](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Firmware/PoseDollFullBody/main/pd41_core.c)
- [Tools/PoseDollHardwareBridge/pd41_protocol.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Tools/PoseDollHardwareBridge/pd41_protocol.py)
- [scripts/capture_metrics_revo2.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/scripts/capture_metrics_revo2.py)
- [scripts/revo2_evidence.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/scripts/revo2_evidence.py)
- [scripts/run_revo2.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/scripts/run_revo2.py)
- [scripts/report_revo2.py](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/scripts/report_revo2.py)
- [Hardware/PoseDoll44/verification/revO2/runs/o2_20260923_r1/status.json](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/verification/revO2/runs/o2_20260923_r1/status.json)
- [Hardware/PoseDoll44/verification/revO2/runs/o2_20260923_r1/mechanics_analysis.json](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/verification/revO2/runs/o2_20260923_r1/mechanics_analysis.json)
- [Hardware/PoseDoll44/verification/revO2/runs/o2_20260923_r1/electronics.json](https://github.com/fukawachan/PoseDollLab_Design/blob/239d4430cec49eecaf12c37f1ec4717055d3fbfe/Hardware/PoseDoll44/verification/revO2/runs/o2_20260923_r1/electronics.json)

厂家来源（2026-09-23 查阅）：
- [TI SN74LVC125A datasheet Rev. T, package/pinout, power sequencing and electrical characteristics](https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf)：Checked parsed text and screenshots pages 3 and 6; no VCC=0 Ioff rating inferred from IOZ.
- [Espressif ESP32-S3 Hardware Design Guidelines, PCB module layout](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)：Antenna clearance is tied to RF performance; not authorization to delete physical/electrical clearance.
