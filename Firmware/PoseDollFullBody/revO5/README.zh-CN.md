# Rev O5 请求式静态采集固件

本目录是 O5 独立后继，保留 A（14 芯跨肩）硬件拓扑，未改写旧 PD41 / O1–O4。G0 和 N1–N6 已通过 ESP-IDF 6.1 编译；**未烧录、未连接传感器，实际 SPI/CAN/USB 时序未测量**。

## A 路径

UE PDS1 request → 主机 `Tools/PoseDollHardwareBridge/bridge.py` → USB PDG5 → G0 的 PDC5 CAN 请求 → 区域 AS5048 诊断与角度读取 → G0 新扫描 → 主机 → PDS1 → UE。

每次扫描先清空 41 个测量槽和节点 boot；3 个根槽为 fixed。区域节点只在新 token 请求到达后读实际配置的 SPI 端口，不从旧周期缓存取值。G0 逐区查询；使用 G0 的首个发送前时刻与最后接收后时刻作为保守全扫描区间，区域时钟只提供 duration，不拼接为全局绝对时间。

约 10 Hz；单个区域查询最多 20 ms，全扫描仍受 100 ms 上限约束；3 s 采集事务截止。A 路径丢失/无效数据将终止采集，下一次需要新 UUID。没有以重复请求重置原采样时间。区域返回的故障字保留，缺节点/缺端口不补齐。最终稳定性和 Capture 仍由 UE 判断。以上是代码策略，不是实测时序保证。

`CONFIG_PD_BENCH_PORTS` 配置该区域前 K 个实接端口（默认 9，再限制到该区端口数）。局部台架只能使用主机 `--diagnostic`，禁止当作完整 41 轴姿势。配置端口掩码不是传感器存在性证明；完整扫描还必须逐槽通过实际读数/诊断校验。

## USB PDG5/1：220 字节，小端序

| 偏移 | 字段 |
|---|---|
| 0 / 4 / 5 / 6 | `PDG5` / version=1 / type / u16 length=220 |
| 8 / 16 | u64 device / G0 boot |
| 24 / 40 | UUID 原始 16 字节 / u64 scan |
| 48 / 56 / 64 | u64 request_start / scan_start / scan_end，单位 µs，均为 G0 时钟 |
| 72 | 6 × u64 区域 boot，N1…N6 |
| 120 | 44 × u16，固定槽 `0x4000`，角度 `<0x4000`，missing=`0xffff`，fault=0x8000 加诊断标志 |
| 208 / 216 | u64 本轮配置并读取端口掩码 / 前 216 字节的 CRC32 |

type：1 PROBE、2 HELLO、3 REQUEST、4 ACCEPTED、5 SCAN、6 CANCEL、7 ERROR、8 STOP。REQUEST/CANCEL/STOP 必须匹配 device/boot。重复当前 REQUEST 只确认相同 UUID 和原 request_start，ACK 的 scan/start/end 为 0。新的 UUID 才开始新事务。串口未完成帧 500 ms 超时；错误数据不会作为姿势解码。ESP 控制台使用 UART0，USB JTAG 单独承载此二进制协议。

## CAN PDC5/1

查询 ID=`0x600+node`，回复 ID=`0x610+node`，node=1…6。标准 CAN 每帧 8 字节：byte0 是片号，其余 7 字节数据，最后补零。请求 28 字节（4 片），回复 52 字节（8 片）；严格顺序、CRC32、100 ms 重组上限，任何错误按整次失败处理。

请求：version/op/node/reserved、G0 boot、token、预期区域 boot、CRC。回复：version/kind/node/count、G0 boot、token、区域 boot、duration、9 个角度/状态字、端口掩码、CRC。具体偏移见 `static_gateway.c`；USB 的完整固定轴序见桥接 `layout.json`。N1/N2/N3/N4/N5/N6 的起始槽分别为 3/6/12/28/21/37，数量 3/6/9/9/7/7。物理 CS 引脚沿用 `../main/pd41_config.h`，旧实时 deadline 常量未用于本实现。

## C 路径的恢复实验

`remote_runtime.*` 是 PDR4/1 编解码器外的有界运行时模型，尚未接 STM32 启动、SPI、UART、DE 或实际 RS485。线格式仍为 68/80 字节，不暗改版本。

一个事务缓存：采集中重复请求返回本地 WAIT（不新增 wire BUSY）；采集完成后，相同字节请求重放同一 80 字节回复，原测量 start/end 不变。100 ms 限制只约束该扫描的重试；下一次合法扫描可在 10 Hz 周期重新采样。已过期的重试使本次 capture 失败，需要更大的 capture_counter。复位必须用新的 boot/nonce/generation 重新绑定；外层入网握手仍须由驱动实现。主控端重试必须保留第一次发出请求的时刻；不能用收到缓存回复的时刻冒充新样本。

## 复算

从设计仓库根目录运行：

```powershell
scripts/Run-RevO5-GatewayTests.cmd "$PWD/.local/o5_gateway_new"
scripts/Run-RevO5-LinkTests.cmd "$PWD/.local/o5_link_new"
Firmware/PoseDollFullBody/revO5/build.ps1 -Role G0 -BuildRoot "$PWD/.local/o5_idf_new"
```

其他角色依次替换为 N1…N6。主机 C 测试 `/W4 /WX`；测试回调是模拟读数。IDF build 不等于实物通过。SDK/编译器本地路径集中在构建脚本中；未执行 flash。
