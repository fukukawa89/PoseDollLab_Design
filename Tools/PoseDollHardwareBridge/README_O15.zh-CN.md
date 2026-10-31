# O15：46原始角度 → UE静态姿势

这是O15完整数字样机对应的新桥接入口：`o15_bridge.py`。旧O5/PD41工具继续保留，不能互换线协议。

先完成 `Hardware/PoseDoll44/bench/revO15/guide.html` 的电子配对和物理标定。默认BODY/G0固件对端MAC为零，禁止直接拿默认构建作为已配对硬件。BODY与G0用真实MAC生成各自的defaults，使用新的绝对BuildRoot编译。

从本仓库根目录运行一次诊断（COM7只是示例，换成实际G0端口；每次日志文件名必须不同）：

```powershell
.venv/Scripts/python.exe Tools/PoseDollHardwareBridge/o15_bridge.py --ue-root E:/UnrealProjects/DollSimulation --serial COM7 --mapping Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1/raw46_mapping_candidate.json --wiring Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1/raw46_wiring_candidate.json --diagnostic --log .local/o15_diagnostic_001.jsonl
```

诊断只输出原始扫描，不发布有效全身姿势。用它检查46个编号、方向、静态噪声、断线/掉电。零位和方向必须实测；CAD参考不是实测标定。

完整硬件标定完成后，将INCOMPLETE模板另存为 `raw_calibration_MEASURED.json`，填入真实BODY device id、46轴实测zero_deg/sign和证据。五个physical_tests必须是已经实际完成的项目；没有完成的保持false。不要为了让连接成功填假值。

```powershell
.venv/Scripts/python.exe Tools/PoseDollHardwareBridge/o15_bridge.py --ue-root E:/UnrealProjects/DollSimulation --serial COM7 --mapping Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1/raw46_mapping_candidate.json --wiring Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1/raw46_wiring_candidate.json --raw-calibration Hardware/PoseDoll44/bench/revO15/commissioning/raw_calibration_MEASURED.json --log .local/o15_capture_001.jsonl --port 39178
```

桥接器监听本机127.0.0.1:39178，供已有UE静态采集功能连接。41个测量语义轴+3个固定骨盆轴；六条链共用一个物理BODY。完整性、CRC、boot、请求身份、扫描年龄、标定绑定仍必须通过；降低采集频率不允许把缺失/故障填成正常角度。

当前真实运行过的是64项桥接测试和合成PDG15→生产BridgeCore→实际UE的正常/缺失/CRC/boot用例。没有真实ESP32、AS5048、USB或无线采集结果。
