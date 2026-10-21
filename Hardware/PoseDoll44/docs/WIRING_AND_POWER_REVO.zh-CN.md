# Rev O 电源与通信设计状态

## 固件已实施的部分
`Firmware/PoseDollFullBody/revO/` 为独立项目。G0 用显式编译角色选择；不初始化 SPI，不自动标记 N1 在线，BOOT/ACK/END/PAIR 接收涵盖 N1–N6。未修改旧固件、共享协议快照或 UE 项目。
41 个轴仍占协议槽 3–43；前三槽保持 PD_FIXED，缺失保持 PD_MISSING，故障保持 PD_FAULT 与诊断位，正常零角度仍可测得。G0 从不占用第七个测量数组元素。新鲜批次失去 N1 时三路腰槽必须缺失。

## 电气实现程度
G0、3/6/7/9 路板均有原生 KiCad 原理图和真实库封装布局。原理图 ERC 通过不等于 PCB 完成；板未布线，仍有未连接项与工艺规则问题。0.2 mm 的 MCU 热焊盘孔与当前 0.3 mm 工艺规则不匹配，需要明确制造工艺后处理，不以忽略 DRC 消除失败。
体内板取消日常 USB，保留每端口 SN74LVC125APWR 缓冲和独立六芯传感器接口。G0 保留数据专用 USB 的隔离拓扑。每种板的准确元件身份、网络和封装见同目录 connectivity.json / layout.json。
布局导出的 XY 使用真实库 courtyard；Z 高度、配合插头和线尾使用保守探索包络，**并非全部厂家 STEP**。因此还不能声称完整 PCBA 包络已认证或能够装入任意腔体。

## 电源候选
本轮实际原理图保持 **5 V 输入**，12 V 只进入计算比较。它保留与旧器件基线的边界，没有把旧板认定为 12 V 可用。初始分析比较 24/26/28 AWG 的 1 m 电源对，在 -5% 电源容差及恒功率负载下求解压降；6 MCU、41 传感器、收发器和缓冲器的电流均为工程分配值，非实测。
[计算记录](../verification/revO/power_budget.json) 也列出尚未完成的六路内部支路保护、浪涌/TVS、USB 回灌与线束温升。初始 5 V / 24 AWG 只是后续设计基线，不是全套接线指导。
外接复合线需要 CAN_H、CAN_L、V+、GND。普通 USB 插头不可承载自定义 CAN/电源。骨盆接口最终型号、针序、低矮弯头和左右方向尚未冻结；不能据此自接 12 V 线束。

## CAN
候选电气线性顺序：G0 → N1 → N5 → N6 → N2 → N3 → N4；两端各 120 Ω。折返需要进出对线，不能改成无约束星形或保留第三个端接。
30 帧/批 × 135 bit × 60 Hz / 500 kbit/s = 48.6%。解析调度例约 11.49 ms，在假设每轴读取 700 µs、无错误且回调立即调度时成立。它未覆盖驱动/系统延迟、epoch/BOOT/ACK 突发、错误与重试；14 ms 批次截止和 8 ms 采样窗仍需真实台架验证。

## 一手规格核对
2026-09-23 读取：
- [Espressif ESP32-S3-WROOM-1/1U datasheet v1.8](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)：WROOM-1 的模块尺寸 18×25.5×3.1 mm；此尺寸不包括 PCB、接头与维护空间。
- [TI TPS6216x datasheet](https://www.ti.com/lit/ds/symlink/tps62162.pdf)：稳压器输入范围不等于整块旧板的输入认证；保护和被动器件必须逐项审查。
- [Infineon AS5048A](https://www.infineon.com/part/AS5048A)：继续采用轴上角度传感方案，不能由型号直接推断当前气隙的磁场/精度。
- [TI CAN Physical Layer Requirements](https://www.ti.com/lit/an/slla270/slla270.pdf)：线性总线与端接约束。
- [SCHNORR 弹簧目录](https://www.schnorr-group.com/fileadmin/4_Downloads/Brochures/SCHNORR_Produktbroschuere_EN_2024-02.pdf)：后续碟簧选型来源；本轮尚未将目录载荷当成新关节实测保持能力。

供应方报价、板级温升、磁场、串扰、关节力矩和电缆手感均待验证，无已获得的制造价格。
