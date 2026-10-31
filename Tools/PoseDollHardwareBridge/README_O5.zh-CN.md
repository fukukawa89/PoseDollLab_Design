# O5 静态硬件桥接

A 拓扑的请求式 PDG5/1 → PDS1/1 桥接，与此目录旧 PD41 诊断/标定脚本并存。没有读取 PD41 周期缓存或把旧数据重新标成请求后采样。

数字测试已覆盖 native C 编解码向量、完整轴序、缺失/故障、启动身份、CRC、请求/扫描顺序、取消迟到和字节拆包；真实 UE 联调使用 **simulated** 原始 PDG5 字节。串口生产入口仅在打开实际串口后标记 **hardware**。该标记只说明数据来源，不能证明校准、机械精度或制造合格。

## 日后台架入口（本轮无硬件，未执行）

```powershell
python -m pip install -r Tools/PoseDollHardwareBridge/requirements-o5.txt
python Tools/PoseDollHardwareBridge/bridge.py --ue-root E:/UnrealProjects/DollSimulation --serial COM7 --diagnostic --log bench_new.jsonl
```

`--diagnostic` 请求一轮原始采集并输出缺失/故障，不发布 PDS1 FullBody hello。单轴、九轴台架使用此模式。输出日志必须是新文件，含方向、主机单调时钟和原始字节。COM7 是示例，不会由脚本自动选择/烧录设备。

41 个端口和 6 个节点具备条件后，省略 `--diagnostic` 可建立 loopback 39178 上的 UE 静态连接。仍要求所有读数完整有效，CRC/boot/profile/calibration/固定根槽/扫描年龄均通过。UE 端 500 ms 稳定窗口与一次性写入策略保持。

**当前 UE Shared 的 virtual profile / zero-pi 是软件参考，不是人偶实物标定。** 原始台架读数可以验证通信；具有物理意义的 Capture 必须先完成同一拓扑的零位、符号、传动比、真实轴偏置标定，并让两端加载同一审核后的 profile/calibration 文件及哈希。本轮没有生成实体标定，不能把模拟通过解读为角度准确度通过。

运行时上限：1 个活动请求；32 个已结束 ID，30 s 寿命；每连接最多 4096 个请求 ID；PDG5 收包最多 32 帧，残帧 500 ms 超时；3 s 采集截止。已知迟到回复仍先检查 CRC/身份/状态，再丢弃；未知 ID 和故障不会因“可能是旧包”被忽略。

## 数字复现

```powershell
$env:POSEDOLL_UE_ROOT='E:/UnrealProjects/DollSimulation'
python -m pytest Tools/PoseDollHardwareBridge/tests -q
```

`tests/pdg5_golden.bin` 是本轮主机 C 测试导出的 220 字节向量；独立 Python 解码并逐字节回编匹配。`layout.json` 检查全部 44 个槽，不仅检查数量。

`synthetic_ue_peer.py` 与 `run_ue_bridge_o5.py` 用于隔离 UE 项目的真实 TCP/Capture 联调，需设置 `POSEDOLL_DESIGN_ROOT`、`POSEDOLL_TEST_PYTHON`，并以 UnrealEditor-Cmd 的 ExecutePythonScript 运行后者。它会创建测试资产，应仅用于独立测试项目。正常输入写入一次；missing、CRC、boot 三种错误均写入零次。没有串口、ESP32 或 AS5048 的执行证据。
