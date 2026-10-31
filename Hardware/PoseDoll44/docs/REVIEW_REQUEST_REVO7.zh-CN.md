# Rev O7 审查入口

先读 [O7说明](O7_DIGITAL_AND_BENCH.zh-CN.md) 与 [小样任务书](../bench/revO7/README.zh-CN.md)。本轮没有UE/生产固件修改。用户授权推进到需要硬件测试的节点；目前没有硬件。

## 当前输入

- CAD生成器：`cad/revO7/pancake_joint.py`。
- 当前实体：`generated/revO7/runs/o7_20260924_r1/LP6_current/`。
- 单关节检查：`cad/revO7/verify_lp6.py`，当前报告对应同名 `verification/.../LP6_current/`。
- 双臂：`generated/.../bilateral_current/` 与 `verification/.../bilateral_current/`。
- 背盒路径：`cad/revO7/check_back_paths.py` 与 `verification/.../back_paths/back_paths.json`。
- 力与手感：`scripts/analyze_revo7_loads.py`、`scripts/prepare_revo7_bench.py`。
- 证据：`verification/.../results.json` 与 `verification/revO7/delivery/DELIVERY_MANIFEST.json`。

保留480 mm主线、91 cm备用、静态采集与无1.2 kg硬门槛。不要把材料目录值、STEP零碰撞、哈希验证或单面试片推算当成制造放行。

## 希望重点审查

1. LP6分体/轴向装配顺序是否仍有漏项；前后板受力挠曲是否可能改变轴承/测角基准。
2. 三个周向弹簧站点的力不均、三销导向冗余约束和浮动盘带扭矩滑动，哪些必须先测、哪些应先改结构。
3. 磨损向下取整降低保持力的影响；生产限位、实际最大力和紧固件强度仍未闭合。
4. 当前双臂45/102失败，如何在材料实测后做真正的共用多轴支架；不要仅复制LP6模块。
5. 48×48×12 mm是经过1,700个采样路径状态的空空间目标。中央板架构及PCBA/插头/线束/RF尚未放入，如何安排后续链路台架与排板。
6. 首批材料/弹簧小样是否足以决定下一步尺寸与预紧窗口；暂定手感线不是已确认的用户标准。

## 快速复核

在设计仓库根目录执行：

```powershell
.venv/Scripts/python.exe -X utf8 scripts/summarize_revo7.py --verify
.venv/Scripts/python.exe -X utf8 scripts/seal_revo7.py --verify
```

完整CAD命令见汇总的输入文件清单及各脚本 `--help`。不要重新生成到已封存目录；新运行应使用新目录。旧失败模型和调试程序不参与当前通过项，历史标记说明其失效原因。
