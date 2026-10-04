# Rev O Desktop：当前主方案
日期：2026-09-23。状态：**第一轮数字设计研究，完整总装尚未完成，未实测、未制造放行。**

约 91 cm 的 Rev M/N1 已降为备用；源码、原报告、STEP、打印件与查看器保留在原位。独立分支为 `design/revO-desktop-external`。从提交 `458f3b0646f724f3b74769defc98f5f6e9ec45a8` 开始，与网页任务书评审版本相同。用户的软件项目原有 `Config/DefaultEditor.ini` 修改未动。

网页端独立审查从 [给 GPT-6 Pro 的审查说明](REVIEW_REQUEST_REVO.zh-CN.md) 开始，包含优先问题、源码/证据索引和复现边界。

## 这轮实际交付

- Manny / Quinn 各 420、450、480、520、550 mm：独立解剖配置、骨架与 PCBA 封装空间 STEP、逐项空间缺口。520/550 仅作比较，没有把主方案直接放大。
- S4、M6、L6 三档紧凑单轴关节：实际 BRep、STEP、零件清单、交叉检查；整合磁铁座，保留原尺寸 AS5048A 测角板和 Ø6×2.5 mm 磁铁。
- 3/6/7/9 路体内节点及零测量通道 G0 的原生 KiCad 原理图与布局。保留逐端口缓冲器，未以空矩形冒充可工作的电路板。
- 独立 G0 与 N1–N6 七种固件，七种均成功编译；G0 无本地传感器，N1 仍采三路腰轴。实际接收分发器经过主机故障场景测试，输出逐字节兼容旧 PD41 v1。
- 两个可打印的配合样片及本地交互查看器。不是整机打印包。

## 当前结论

**48 cm 仍是详细设计锚点，尚未选出已合格的最终尺寸。** 当前九路板为 40×66 mm；按肩/肘端部 18+14 mm 的探索预留，48 cm 的 Manny 左上臂缺约 24.6 mm、Quinn 缺约 26.4 mm。该失败只说明目前板位不成立；不能据此宣称 42/45/48 cm 的全新机构不可行。较大候选也未解决此板位，下一轮优先分板或重新布置在刚性躯干内。

全部三档关节的实际建模实体相交检查为 0 项，但每档两项维护保留区交叠仍有记录：后端工具空间穿过输出轴、插头保留区和连接器配合范围相交。必须改成合适的环形/双销工具并获取配合插头模型，不能忽略 `reservation` 后宣称装配通过。此外，当前一体式转轴的磁铁凸台/挡肩无法穿过整体轴承座孔（S4：8.4 mm 对 6 mm；M6/L6：9 mm 对 8 mm），轴向装配检查为 FAIL。必须设计可分体的轴承座或可拆且可靠防脱的挡肩，完成插入路径后才能制作 B 级样件。弹簧、最终磁铁防脱、板边夹持和加工公差也未完成。

质量**预算**为约 1.387 kg，超过 1.2 kg 目标约 187 g。它由约 762 g 的关节建模实体子集加 625 g 的具名未建模分配组成，不是完整 CAD 的精确质量，更不是实物称重。减重工作必须落实到实体和 BOM，不能只改预算数字。

48 cm Manny 的载荷分配模型在胸腰弯扭目标姿态下，腰俯仰轴保持力初估约 0.388 N·m（含假设线缆力矩及 1.5 倍裕量）。按假设摩擦系数低界计算，需要约 555 N 预紧，超过当前 L6 探索上界 350 N；锁骨抬升的 M6 也需复核。**旧预紧参数不能直接沿用；当前关节没有获得保持力或手感合格结论。**

完整本体真实高度、完整质量、六块板最终位置、背手/侧卧/俯卧带线轨迹、多轴磁干扰及完整装配通道仍为 NOT_RUN。图中的球点和灰杆是解剖参考，不能当作最终机械轴偏置。

## 验证与查看

```powershell
# 在 design 仓库运行
.\scripts\Start-Viewer.ps1
.\scripts\Start-Viewer.ps1 -Revision revN     # 91 cm 备用查看器
.\scripts\Build-RevO.ps1 -Stage OfflineTests
.\scripts\Build-RevO.ps1 -Stage CAD
.\scripts\Build-RevO.ps1 -Stage Electronics
.\scripts\Build-RevO.ps1 -Stage Firmware
```

`-Stage All` 重建当前研究成果，不生成可制造的整机。CadQuery 沿用本机 CQ-editor 2.7 / Python 3.13；KiCad 10 与 ESP-IDF 6.1 沿用现有安装。构建过程中不烧录、不打开串口。

- [状态总表](../verification/revO/status.json)
- [尺寸比较](../verification/revO/size_tradeoff.json)
- [关节实体及保留区检查](../verification/revO/joint_study.json)
- [板级检查](../verification/revO/electronics_placement.json)
- [七角色实际编译结果](../verification/revO/firmware/builds.json)
- [本轮离线回归](../verification/revO/offline/results.json)
- [备用原文件哈希清单](../verification/revO/fallback_91cm_inventory.json)
- [样件与测试说明](TEST_PLAN_REVO.zh-CN.md)
- [电源、通信和器件来源](WIRING_AND_POWER_REVO.zh-CN.md)

基线审计保护 5,748 个文件、约 5.16 GB 数据；这是原位冻结和校验，不是异地备份。新成果以 `revO` 路径隔离。审查提交包含轻量查看器、三档关节总成 STEP 和 A01/A02 样片 STEP/STL；十份体型布局 STEP、重复零件 STEP 及历史大型导出依赖源码重建或另行复制。

## 下一轮工作顺序

1. 将九路采集节点从失败的上臂整体板位改为可装配的分板或躯干方案，并导入真实配合插头/线尾。
2. 先重做可装入、可拆卸的轴承座/转轴结构，再从持姿与真实握持力反算碟簧和摩擦材料；解决轴向工具、板夹、磁铁防脱，同时减小实际金属与支座体积。
3. 完成肩/髋/腕嵌套机构，重新生成**真实**机械偏置 profile；保持 44 槽语义，不覆盖旧 Shared 快照。
4. 通过上述门槛后再做双角色完整总装、PCB 布线、电源保护、带线动作路径和完整制造资料。
5. 先做 A 级配合样片；B–F 逐级接入实物证据。尚不购买整机，也不打印备用 91 cm 版。

本轮未运行 UE 编辑器中的 Capture / Undo / Clutch 等交互回归，因为还没有可投入使用的新机械 profile，原 UE 软件未修改。旧 Python/C 和数据帧兼容通过不能替代这些交互验证。
