# central_c1 委托加工说明

状态：数字样机加工候选；未上电验证。
每台人偶净数量 1 块；4 层，FR4 成品板厚 1.2 mm。常规阻焊，建议无铅表面处理。
请按随附 Gerber、独立 PTH/NPTH 钻孔、BOM 与双面贴装坐标核价；元件朝向由原理图/PCB共同确认，不能只凭坐标的角度字段。
所有电容 X7R；限流电阻88.7k必须1%；其余电阻建议1%。回填具体采购料号及替代清单，禁止替代AS5048A为AS5048B，禁止把TPS2553-1锁断型换成自动重试型。
XIAO 两列排针和模块后焊，模块PCB底面与控制板上表面相距4mm；先检查裸板，再装模块。
先在限流台式电源下做短路、供电与通信检查，再装电池。未授权工厂写磁编码器OTP。

## 每块板用料

| 位号 | 数量 | 参数/型号 | 封装 |
|---|---:|---|---|
| U1 | 1 | Seeed XIAO ESP32S3; 2x 1x7 P2.54 male pin strips | PoseDoll:XIAO_ESP32S3_2x7_PTH |
| D1 | 1 | SS14 / 1A 40V | Diode_SMD:D_SMA |
| J7 | 1 | 5V INPUT ONLY / JST PH 2 | Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical |
| J8 | 1 | Pololu D24V22F3 harness: GND, VIN5, VOUT3V3 | Connector_JST:JST_PH_B3B-PH-SM4-TB_1x03-1MP_P2.00mm_Vertical |
| R1,R2,R106,R206,R306,R406,R506,R606 | 8 | 100k | Resistor_SMD:R_0603_1608Metric |
| C1,C2 | 2 | 10u X7R 10V | Capacitor_SMD:C_0603_1608Metric |
| J1 | 1 | CHAIN1 GND,3V3,SCK,MOSI,MISO,CS | Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal |
| U100,U200,U300,U400,U500,U600 | 6 | TPS2553DBVR-1 / latched-off | Package_TO_SOT_SMD:SOT-23-6 |
| R100,R200,R300,R400,R500,R600 | 6 | 88.7k 1% | Resistor_SMD:R_0603_1608Metric |
| C100,C102,C103,C104,C105,C200,C202,C203,C204,C205,C300,C302,C303,C304,C305,C400,C402,C403,C404,C405,C500,C502,C503,C504,C505,C600,C602,C603,C604,C605 | 30 | 100n X7R 10V | Capacitor_SMD:C_0603_1608Metric |
| C101,C201,C301,C401,C501,C601 | 6 | 1u X7R 10V | Capacitor_SMD:C_0603_1608Metric |
| R101,R108,R109,R110,R201,R208,R209,R210,R301,R308,R309,R310,R401,R408,R409,R410,R501,R508,R509,R510,R601,R608,R609,R610 | 24 | 47k | Resistor_SMD:R_0603_1608Metric |
| Q1,Q2,Q3,Q4,Q5,Q6 | 6 | 2N7002 | Package_TO_SOT_SMD:SOT-23 |
| R102,R107,R202,R207,R302,R307,R402,R407,R502,R507,R602,R607 | 12 | 10k | Resistor_SMD:R_0603_1608Metric |
| U101,U102,U103,U104,U201,U202,U203,U204,U301,U302,U303,U304,U401,U402,U403,U404,U501,U502,U503,U504,U601,U602,U603,U604 | 24 | SN74LVC1G125DBVR | Package_TO_SOT_SMD:SOT-23-5 |
| R103,R104,R105,R203,R204,R205,R303,R304,R305,R403,R404,R405,R503,R504,R505,R603,R604,R605 | 18 | 100R | Resistor_SMD:R_0603_1608Metric |
| TP1 | 1 | P1_FAULT_N | TestPoint:TestPoint_Pad_D1.0mm |
| J2 | 1 | CHAIN2 GND,3V3,SCK,MOSI,MISO,CS | Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal |
| TP2 | 1 | P2_FAULT_N | TestPoint:TestPoint_Pad_D1.0mm |
| J3 | 1 | CHAIN3 GND,3V3,SCK,MOSI,MISO,CS | Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal |
| TP3 | 1 | P3_FAULT_N | TestPoint:TestPoint_Pad_D1.0mm |
| J4 | 1 | CHAIN4 GND,3V3,SCK,MOSI,MISO,CS | Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal |
| TP4 | 1 | P4_FAULT_N | TestPoint:TestPoint_Pad_D1.0mm |
| J5 | 1 | CHAIN5 GND,3V3,SCK,MOSI,MISO,CS | Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal |
| TP5 | 1 | P5_FAULT_N | TestPoint:TestPoint_Pad_D1.0mm |
| J6 | 1 | CHAIN6 GND,3V3,SCK,MOSI,MISO,CS | Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal |
| TP6 | 1 | P6_FAULT_N | TestPoint:TestPoint_Pad_D1.0mm |
