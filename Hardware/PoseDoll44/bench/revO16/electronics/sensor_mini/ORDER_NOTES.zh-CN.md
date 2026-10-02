# sensor_mini 委托加工说明

状态：数字样机加工候选；未上电验证。
每台人偶净数量 46 块；2 层，FR4 成品板厚 1.0 mm。常规阻焊，建议无铅表面处理。
请按随附 Gerber、独立 PTH/NPTH 钻孔、BOM 与双面贴装坐标核价；元件朝向由原理图/PCB共同确认，不能只凭坐标的角度字段。
所有电容 X7R；限流电阻88.7k必须1%；其余电阻建议1%。回填具体采购料号及替代清单，禁止替代AS5048A为AS5048B，禁止把TPS2553-1锁断型换成自动重试型。
12×10mm板，用夹边式打印支架；FFC厚0.20±0.03mm，6P，0.5mm间距。连接器在背面，芯片面对磁铁。
先在限流台式电源下做短路、供电与通信检查，再装电池。未授权工厂写磁编码器OTP。

## 每块板用料

| 位号 | 数量 | 参数/型号 | 封装 |
|---|---:|---|---|
| U1 | 1 | AS5048A-HTSP-500 | Package_SO:TSSOP-14_4.4x5mm_P0.65mm |
| J1 | 1 | FH19C-6S-0.5SH(10) | PoseDoll:Hirose_FH19C_6S_0.5SH |
| C1 | 1 | 100n X7R 16V | Capacitor_SMD:C_0603_1608Metric |
| C2 | 1 | 10u X7R 10V | Capacitor_SMD:C_0805_2012Metric |
| R1 | 1 | 33R | Resistor_SMD:R_0603_1608Metric |
| R2 | 1 | 10k | Resistor_SMD:R_0603_1608Metric |
