# O17 USB 与 C1-U 接线

状态：数字装配候选；未连接实物验证。完整设计和放行条件见 DESIGN.zh-CN.md。

```text
电脑 USB ── XIAO USB-C ── 主控3.3V / 数据
                           │ 六路带保护SPI
                           └── 46块编码器
独立稳压5V USB电源 ── J7 ── 原3.3V降压器 ── 六路传感器供电
                         D1 = 不装；禁止桥接到主控USB 5V
所有 GND 共地；两个正电源保持分开。
```

- C1-U 沿用 C1 裸板铜层，BOM 和 placement.csv 不含 D1。不要把 Gerber 的焊盘理解为必须装元件。旧板需先拆掉 D1。
- J7-1 = VIN_5V，J7-2 = GND。J8-1 = GND，J8-2 = VIN_5V，J8-3 = SENSOR_3V3。核对原理图与实物针序后接线，不凭线色。
- 只用稳定 5V 输入，电源额定至少 2A；此为设计余量，实际功耗、电压降与温升待测。禁止 PD 升压触发线。
- XIAO 使用普通 ESP32S3 版，不装摄像头扩展板，不接天线，O17 程序不启动射频。
- USB 数据线接 XIAO 本体；胸部上沿开口和扎带槽用于出线及应力释放。保留后方松弛线环，测试整个人偶姿势时检查线缆是否牵动关节。
- 先限流上电；分别断开两路电源检查反灌、关机轨电压与 GPIO 回灌，再接电脑做采集。C1-U 尚无新的上电合格记录。

P17R/1 与旧 P15R 固件不同。保留六条 SPI 链的顺序 6 / 4 / 10 / 10 / 8 / 8。不得以接收到46个字为依据跳过实际轴号、方向、零位和磁场诊断验证。

参考工具在 source/usb_capture.py，需要 NumPy 与 pyserial。指定端口、O17 profile、实测标定及新的输出文件：

```powershell
python source/usb_capture.py --port COM7 --profile profiles/device_profile.json --calibration my_measured_calibration.json --output capture_001.json
```

COM7 只是语法示例，不会自动寻找或刷写设备。附带 calibration_INCOMPLETE.json 不能产生合格硬件测量。原始字节和坏帧也要保留；拒绝结果不能转成角色零姿势。此工具尚未连接实际硬件或新的 UE 适配器。
