# O22 工程包入口

先打开 [设计说明](DESIGN.zh-CN.md)，再看 [12项审查状态](optimization_tracker.json)。

- 一套USB测姿人偶，46路原始轴，41个语义自由度；核心测量数量不减少。
- `print_batch/manifest.json`：整机完整打印清单（186件）；`physical_tests/sensor_coupon/`是另外两个可拆卸传感小样附件，不要重复采购O11原摩擦件。
- `manufacturing/`：Gerber、钻孔、贴片坐标、BOM和单套询价模板。
- `electronics/`：KiCad原理图及PCB。载板正式文件名为`PoseDoll_O22_SSI_Carrier.kicad_pcb`，4层；placement/route_input等是过程文件，不用于下单。
- `harness/routing_plan.json`：46路端口、实际骨段固定点、预切长度、完整左臂示例；首件前长度未放行。
- `physical_tests/ACCEPTANCE.zh-CN.md`：新传感小样、16路长支路、逐轴标定及46路→UE验收；空表都是真实未测状态。
- `source/`：PC侧采集/校准/导出与39项单元测试。
- `firmware_source/`、`firmware_binaries/`：沿用O21 P21R/1，原始文件哈希见SOURCE_INDEX。刷写请使用对应固件说明，不混用P17R。
- `ue/target_profiles/`、`ue/editor_scripts/`、`ue/plugin_source/`：双目标配置、回归脚本和对应插件源文件。把这些改动用于现有DollSimulation仓库并重新编译；不要把三个源文件当成独立完整插件。
- `cad_source/`：生成脚本副本，用于审计。重建CAD需完整设计仓库及SOURCE_INDEX列出的历史输入；加工文件已经独立导出，打印不要求运行旧CAD生成器。
- `verification/`：数字测试证据，所有合成输入均明确标注。没有硬件测试或供应商成交价。

ZIP保留`bench/revO22`和`tutorials/full-doll-o22`的相对目录。解压到任意空目录，在根目录运行：

```powershell
python bench/revO22/serve_preview.py
```

然后打开 http://127.0.0.1:8771/tutorials/full-doll-o22/index.html 。该服务仅绑定本机地址。

使用现有工程中的快捷采集脚本：在UE中打开含一个Control Rig的目标序列并停在需要的帧，执行：

```python
import sys, unreal
sys.path.insert(0, unreal.Paths.project_dir() + 'Scripts/O22')
import capture_file
capture_file.capture(r'C:\your_capture\capture.payload.json', 'quinn')
```

正式入口不使用synthetic覆盖开关。它创建可撤销关键帧，保存由编辑者决定；身体整体位置和动画修饰继续在UE中处理。

**目前不能据此宣称整机已无干涉、精度已达标或成本已压到1500元。** 数字工作已收敛为首件包；实测、正式询价以及旧有极限姿势干涉仍是放行条件。
