# 给 GPT-6 Pro 的 Rev O3 审查请求

请固定到推送后的实际提交，先读 [START_HERE_REVO3.zh-CN.md](START_HERE_REVO3.zh-CN.md)，再审查本轮源码和 `o3_20260924_r3` 的原始证据。`inputs.json` 中的 `base_commit=239d443…` 是开发起点，不是本轮代码已包含在旧提交中的声明。

用户已明确取消整机 ≤1.2 kg 硬要求：它现在只是轻量化偏好。请继续检查真实质量、质心、支撑、各轴保持力和操作力，不要求为减重强制开发关节族或共享结构。480 mm 参考、完整实体 ≤500 mm 目标/≤600 mm 上限、41 测量轴和 44 槽语义均保留。

## 本次新增审查任务：静态摆姿采集

用户已明确人偶不做实时动捕，而是在摆好姿势之后采集。**请先审查本轮实际修改，再依据 [静态采集需求与架构比较任务](NEXT_REVIEW_STATIC_CAPTURE.zh-CN.md)，判断放宽持续 60 Hz、8 ms 和 14 ms 指标后，哪些采集板、跨肩线束、连接器、控制器和固件可以进一步简化。** 新频率和等待时间尚未冻结；不要把旧实时门槛直接照搬为新场景的产品要求。

当前 `r3` 仍是原时序条件下的工程检查点，本次提交没有通过删掉检查来伪装为低频方案已经通过。请保留数据完整/新鲜/稳定、错误隔离和合理超时，并明确协议字段及主机侧迁移方案。机械强度、精度、手感、尺寸与装配要求不随之取消。

## 实际修改

1. L6-R3 两侧传感板托与各自半盒一体，新增按本轮 BOM 生成的约束图。
2. 去除摩擦环内定位销，采用外耳钢背片；导槽贯通后端，使其确实具有装入路径。保留 0.6 mm 总磨损，增加非对称磨损、独立压缩、后盖离散锁定状态。
3. 完整扭矩链条件筛查；不为未定胶接/背面摩擦提供免费承载信用。
4. 接触激活后才求非负法向反力；无真实壳体的独立支撑工况不出定型反力/选簧。手托重力研究包括侧卧/俯卧的整体方向变换。
5. 明细覆盖移交约 56.44 g 共用紧固件/弹簧预算，其他分配保留。暂估约 1.656 kg，非完整成品质量。
6. 五种原生板候选含 J50 顶入/侧入对照；从真实 PCBA/器件坐标生成实体/目录包络、服务、线弯敏感性与 RF 区。
7. 逐节点有限快速尝试、指数退避、公平游标及超时清理；专用维护批仍公开计入损失。
8. USB 到 END 包络与节点 8 ms 分开；新增真实时间戳帧率、长暂停、单节点质量、显式重连分段。
9. 生产者整套文件锁定、消费前后核对及变异阻塞测试，取消固定零件数量作为完整性定义。

## 建议重点反证

### 结构

- 外耳槽根约 0.65 mm 剩余壁厚、被导槽中断的母螺纹，是否需要改变止转结构或根部尺寸？当前剩余螺纹圆周比例只是条件筛查，未做局部 FEA/拔脱。
- 摩擦层与钢背的结合工艺未定；应如何以最小样件建立温度、压力、剪切、剥离、蠕变和寿命证据？不要把几何无碰撞当作结合强度。
- 52 状态覆盖是否遗漏实际的受载偏摆、局部偏磨、压缩/预紧极值？0.15 mm 最小剩余厚度、0.02 mm 压缩等仍为待供应方认可的假设。
- 整体轴凸键在扭矩下的轴向阻力、反向回差和测角轴止推负载；条件模型的单键受力与摩擦假设是否合理？最大实际弹簧力尚未知。
- 输出接头、小螺钉工具、衬套保持和生产公差未完成。请区分已修复的板托/销碰盘几何与尚未完成的制造 P0。

### 载荷与多轴

- 明细覆盖移交是否重复、遗漏或错误归属？旧 S4/M6 仅作质量参考，全部 41 轴制造选型保持未定。
- 接触算法仅支持共面竖直法向；真实壳体接触、柔顺性、切向摩擦和六维平衡仍缺。手托骨盆的条件载荷是否过宽或遗漏实际使用工况？
- 在不以重量为重构理由的前提下，下一步如何落实胸肩真实轴偏置、N2/N3/N4 和完整单臂？当前尚未建成这套共同总装，请勿根据独立包络自动认可完整装入。

### 电气与时序（以下数值为当前实现，不自动成为下一轮静态模式门槛）

- J50 侧入不保证整体板件更薄，其余传感器口仍可能顶入；目录包络、KiCad 板面规范化和精确配合公差还需核验。厂家申请 STEP 所需的个人/公司信息没有代填或提交。
- 仍未布线，也未闭合 LVC125A 失电隔离、完整电源保护和实际动作线束；4/12 mm 仅为半径敏感性候选。
- 单节点持久缺失的健康节点采样机会模型约 99.66%，仍低于 99.9%；所有节点正常时无维护帧。请检查退避重置、丢失 JOIN_OK、延迟消息与公平性，不把逻辑模拟当台架通过。
- 若继续保留 60 Hz 模式，取消专用维护帧需用可测的驱动时间/队列模型设计跨帧握手；当前 4 ms 阻塞发送不能自动塞进 2.667 ms 间隙。静态模式应重新评估是否还需要这套调度。
- 只有 USB 数据不能观测原始节点 delay/span。原始 END、USB 序号和共享时钟关联应怎样冻结为台架采集协议？

## 直接审查入口

| 范围 | 源码 | 原始结果 |
|---|---|---|
| 关节 | [compact_joint.py](../cad/revO3/compact_joint.py)、[export_joint.py](../cad/revO3/export_joint.py) | [joint.json](../verification/revO3/runs/o3_20260924_r3/joint.json)、[STEP](../generated/revO3/runs/o3_20260924_r3/joint/L6_R3_assembly.step) |
| 装配 / 寿命 | [check_assembly.py](../cad/revO3/check_assembly.py)、[check_lifecycle.py](../cad/revO3/check_lifecycle.py) | [assembly.json](../verification/revO3/runs/o3_20260924_r3/assembly.json)、[lifecycle.json](../verification/revO3/runs/o3_20260924_r3/lifecycle.json) |
| 质量 / 力矩 | [study_revo3.py](../../../scripts/study_revo3.py) | [质量明细](../verification/revO3/runs/o3_20260924_r3/mass_properties_revO3.json)、[受力](../verification/revO3/runs/o3_20260924_r3/mechanics_analysis.json) |
| PCBA | [build_revo3_electronics.py](../../../scripts/build_revo3_electronics.py)、[audit_layout.py](../cad/revO3/audit_layout.py) | [electronics.json](../verification/revO3/runs/o3_20260924_r3/electronics.json)、[pcba_geometry.json](../verification/revO3/runs/o3_20260924_r3/pcba_geometry.json) |
| 包装 | [packaging_revo3.py](../../../scripts/packaging_revo3.py) | [packaging.json](../verification/revO3/runs/o3_20260924_r3/packaging.json) |
| 恢复调度 | [Rev O3 firmware](../../../Firmware/PoseDollFullBody/revO3/) | [host_C.txt](../verification/revO3/runs/o3_20260924_r3/host_C.txt)、[七角色](../verification/revO3/runs/o3_20260924_r3/firmware_builds.json) |
| 统计 | [capture_metrics_revo3.py](../../../scripts/capture_metrics_revo3.py) | [test_revo3.py](../../../scripts/tests/test_revo3.py) |
| 证据 | [revo3_evidence.py](../../../scripts/revo3_evidence.py)、[report_revo3.py](../../../scripts/report_revo3.py) | [run.json](../verification/revO3/runs/o3_20260924_r3/run.json)、[artifacts](../verification/revO3/runs/o3_20260924_r3/artifacts/) |

七角色在 `r1` 实际完成编译，`r3` 验证复用同一固件输入/工具/产物；参见 [firmware_origin.json](../verification/revO3/runs/o3_20260924_r3/firmware_origin.json)。`r1` 其余整合结果不用于当前门槛。查看器、原生板、截图及原始日志用于审查；没有烧录、采购、实物测量或制造放行。

完整执行摘要见 [VALIDATION_REVO3.zh-CN.md](VALIDATION_REVO3.zh-CN.md)。
