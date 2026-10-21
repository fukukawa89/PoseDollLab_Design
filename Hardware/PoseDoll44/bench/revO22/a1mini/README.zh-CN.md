# O22 · 拓竹 A1 mini 多零件打印盘

整套人偶为 **A01–A10 共 10 盘、186 件**，每盘打印一次。其中 185 件装在人偶上，P242 是 XIAO 装配间距量规。`optional/T01_sensor_coupon.3mf` 是额外的两件传感器安装小样，不计入整机数量。

打开本文件旁的 `index.html` 可离线查看排盘、3D 预览和每件所属位置。离线页面的首个按钮会跳转到各盘文件；也可以直接使用 `plates` 文件夹。

## 使用方法

1. 解压完整压缩包，在 Bambu Studio 中选择 **Bambu Lab A1 mini** 和实际喷嘴，打开 `plates` 中的一份 3MF。每个文件已经是一盘，不要同时把十份文件叠放进同一个盘。
2. 如果提示导入模型/几何，选择导入模型；保持各件现有相对位置，比例 **100%**。不执行自动排列或自动摆正，不逐件重新居中。核对对象数量与本表一致、与编号图布局相符。
3. 使用 **按层打印**。这种密集排布没有为“逐件打印”的整颗打印头预留避碰空间。
4. 使用你在 O11 小样上验证过的材料与工艺。文件只存几何、名称、排布，不绑定耗材、喷嘴或 G-code。切片后查看支撑、裙边和首层预览。
5. 打完后按盘号装袋；每盘内部按编号图和下面的清单核对。左右按人偶自身区分。相同打印编号（例如 N003）的多件复制已放齐，不必额外补数量。

## 排盘原则与验证

- 打印机官方成型空间 180 × 180 × 180 mm。模型离平台边缘至少 6 mm，模型包围框之间至少 6 mm。
- 保留原单件贴床朝向。只做平移、绕 Z 轴转 0°/90°；无缩放、镜像、切割或合并实体。
- 150 种源文件展开为 186 个实际实例，逐件核对恰好出现一次。输出 3MF 的每个顶点和三角面已读回检查，与刚体变换后的源网格完全相同。
- 按身体部位分组做 700 组排序搜索。头颈盘利用余量放背盒盖；腿部按左右大腿/关节件和双侧小腿/脚掌骨架分三盘。10 盘是本次找到的排布，不声称是所有工艺条件下的理论最少盘数。
- **11/11 文件通过本机 Bambu Studio 02.08.02.61 的完整导入和切片**：对象数及名称对应、无网格修复、无切片警告。参考设置为 A1 mini / 0.4 mm 喷嘴 / Generic PLA / 纹理 PEI / 0.20 mm 层高 / 3 圈墙 / 20% 填充 / 普通自动网格支撑 / 30°支撑阈值 / 2 mm 外裙边 / 无环形裙线 / 按层打印。
- 参考设置只是排布检查，不替代 O11 已验证的实际材料与配合工艺。本轮未进行实物打印。使用更宽裙边、树状支撑或筏层时，重新检查支撑占位是否越界、是否靠近其他模型。
- 机器暖机和冷却的实际时间未计量，不给出虚构的节省时长。`verification` 中的耗材和时间是上述参考设置的切片估计，不是测量值或预算变更。

官方尺寸：[A1 mini Quick Start Guide](https://cdn1.bambulab.com/documentation/quick-start-f507128172bdf/Quick%20start%20guide%20-%20A1%20mini-EN.pdf)。

## 每盘一览

| 盘号 | 部位 | 件数 | 最高模型 | 文件 |
|---|---|---:|---:|---|
| A01 | 头颈与背盒盖 | 20 | 72.6 mm | [A01_head.3mf](plates/A01_head.3mf) |
| A02 | 躯干 1/2 | 13 | 107.8 mm | [A02_torso_1.3mf](plates/A02_torso_1.3mf) |
| A03 | 躯干 2/2 | 15 | 69.5 mm | [A03_torso_2.3mf](plates/A03_torso_2.3mf) |
| A04 | 左臂 1/2 | 11 | 92.3 mm | [A04_left_arm_1.3mf](plates/A04_left_arm_1.3mf) |
| A05 | 左臂 2/2 | 26 | 58.4 mm | [A05_left_arm_2.3mf](plates/A05_left_arm_2.3mf) |
| A06 | 右臂 1/2 | 14 | 91.7 mm | [A06_right_arm_1.3mf](plates/A06_right_arm_1.3mf) |
| A07 | 右臂 2/2 | 23 | 51.5 mm | [A07_right_arm_2.3mf](plates/A07_right_arm_2.3mf) |
| A08 | 左大腿与左腿关节小件 | 27 | 109.2 mm | [A08_left_leg.3mf](plates/A08_left_leg.3mf) |
| A09 | 右大腿与右腿关节小件 | 27 | 109.2 mm | [A09_right_leg.3mf](plates/A09_right_leg.3mf) |
| A10 | 双侧小腿与脚掌骨架 | 10 | 84.6 mm | [A10_lower_legs.3mf](plates/A10_lower_legs.3mf) |
| T01 | 可选：O22 传感器安装小样 | 2 | 110.0 mm | [T01_sensor_coupon.3mf](optional/T01_sensor_coupon.3mf) |

## 每件核对清单

编号对应 SVG 排布图中的数字和 3MF 对象名。勾选清单只是装袋/装配辅助，不是额外要打印的标签。

### A01 · 头颈与背盒盖

- [ ] 01 · X081 · `o22/controller_lid` × 1
- [ ] 02 · X050 · `frame/head` × 1
- [ ] 03 · P035 · `head/C14` × 1
- [ ] 04 · P033 · `head/C01` × 1
- [ ] 05 · P034 · `head/C02` × 1
- [ ] 06 · X045 · `head/P_case_plus` × 1
- [ ] 07 · X049 · `head/D_case_plus` × 1
- [ ] 08 · P036 · `head/C15` × 1
- [ ] 09 · X005 · `head/C01_sensor_cassette` × 1
- [ ] 10 · X006 · `head/C02_sensor_cassette` × 1
- [ ] 11 · P040 · `head/P_magnet_cap` × 1
- [ ] 12 · P045 · `head/D_magnet_cap` × 1
- [ ] 13 · N003 · `head/C01_magnet_cartridge` × 1
- [ ] 14 · N003 · `head/C02_magnet_cartridge` × 1
- [ ] 15 · X043 · `head/P_pcb_clip_-14` × 1
- [ ] 16 · X044 · `head/P_pcb_clip_+14` × 1
- [ ] 17 · X047 · `head/D_pcb_clip_-14` × 1
- [ ] 18 · X048 · `head/D_pcb_clip_+14` × 1
- [ ] 19 · P039 · `head/P_radial_pad` × 1
- [ ] 20 · P044 · `head/D_radial_pad` × 1

### A02 · 躯干 1/2

- [ ] 01 · X046 · `frame/chest` × 1
- [ ] 02 · X042 · `frame/waist` × 1
- [ ] 03 · P002 · `waist/C14` × 1
- [ ] 04 · P018 · `chest/C14` × 1
- [ ] 05 · P001 · `waist/C01` × 1
- [ ] 06 · P017 · `chest/C01` × 1
- [ ] 07 · X041 · `chest/P_case_plus` × 1
- [ ] 08 · X040 · `chest/P_pcb_clip_+14` × 1
- [ ] 09 · X039 · `chest/P_pcb_clip_-14` × 1
- [ ] 10 · X036 · `waist/P_pcb_clip_+14` × 1
- [ ] 11 · X035 · `waist/P_pcb_clip_-14` × 1
- [ ] 12 · P012 · `waist/P_radial_pad` × 1
- [ ] 13 · P028 · `chest/P_radial_pad` × 1

### A03 · 躯干 2/2

- [ ] 01 · X038 · `frame/pelvis` × 1
- [ ] 02 · X037 · `waist/P_case_plus` × 1
- [ ] 03 · P003 · `waist/C15` × 1
- [ ] 04 · P019 · `chest/C15` × 1
- [ ] 05 · X004 · `chest/C02_sensor_cassette` × 1
- [ ] 06 · X001 · `waist/C01_sensor_cassette` × 1
- [ ] 07 · X003 · `chest/C01_sensor_cassette` × 1
- [ ] 08 · X002 · `waist/C02_sensor_cassette` × 1
- [ ] 09 · P242 · `fixture/xiao_spacing_gauge` × 1
- [ ] 10 · P013 · `waist/P_magnet_cap` × 1
- [ ] 11 · P029 · `chest/P_magnet_cap` × 1
- [ ] 12 · N003 · `waist/C01_magnet_cartridge` × 1
- [ ] 13 · N003 · `waist/C02_magnet_cartridge` × 1
- [ ] 14 · N003 · `chest/C01_magnet_cartridge` × 1
- [ ] 15 · N003 · `chest/C02_magnet_cartridge` × 1

### A04 · 左臂 1/2

- [ ] 01 · X054 · `frame/clavicle_l` × 1
- [ ] 02 · W005 · `frame/clavicle_l.protract_frame` × 1
- [ ] 03 · H004 · `frame/elbow_l` × 1
- [ ] 04 · P051 · `upperarm_l/C14` × 1
- [ ] 05 · X058 · `frame/upperarm_l` × 1
- [ ] 06 · X051 · `upperarm_l/P_pcb_clip_-14` × 1
- [ ] 07 · X056 · `upperarm_l/D_pcb_clip_+14` × 1
- [ ] 08 · X055 · `upperarm_l/D_pcb_clip_-14` × 1
- [ ] 09 · X052 · `upperarm_l/P_pcb_clip_+14` × 1
- [ ] 10 · P061 · `upperarm_l/P_radial_pad` × 1
- [ ] 11 · P066 · `upperarm_l/D_radial_pad` × 1

### A05 · 左臂 2/2

- [ ] 01 · H006 · `frame/hand_l.flex_frame` × 1
- [ ] 02 · P050 · `upperarm_l/C02` × 1
- [ ] 03 · W004 · `frame/forearm_l` × 1
- [ ] 04 · P191 · `frame/hand_l` × 1
- [ ] 05 · N004 · `clavicle_l.elevate/magnet_cartridge` × 1
- [ ] 06 · X008 · `upperarm_l/C02_sensor_cassette` × 1
- [ ] 07 · X007 · `upperarm_l/C01_sensor_cassette` × 1
- [ ] 08 · P052 · `upperarm_l/C15` × 1
- [ ] 09 · X053 · `upperarm_l/P_case_plus` × 1
- [ ] 10 · X020 · `clavicle_l.elevate/sensor_cassette` × 1
- [ ] 11 · N004 · `hand_l.deviate/magnet_cartridge` × 1
- [ ] 12 · N004 · `forearm_l.twist/magnet_cartridge` × 1
- [ ] 13 · X022 · `forearm_l.twist/sensor_cassette` × 1
- [ ] 14 · P049 · `upperarm_l/C01` × 1
- [ ] 15 · X024 · `hand_l.deviate/sensor_cassette` × 1
- [ ] 16 · X057 · `upperarm_l/D_case_plus` × 1
- [ ] 17 · N004 · `hand_l.flex/magnet_cartridge` × 1
- [ ] 18 · X021 · `elbow_l.flex/sensor_cassette` × 1
- [ ] 19 · N004 · `clavicle_l.protract/magnet_cartridge` × 1
- [ ] 20 · N004 · `elbow_l.flex/magnet_cartridge` × 1
- [ ] 21 · X023 · `hand_l.flex/sensor_cassette` × 1
- [ ] 22 · X019 · `clavicle_l.protract/sensor_cassette` × 1
- [ ] 23 · P067 · `upperarm_l/D_magnet_cap` × 1
- [ ] 24 · P062 · `upperarm_l/P_magnet_cap` × 1
- [ ] 25 · N003 · `upperarm_l/C01_magnet_cartridge` × 1
- [ ] 26 · N003 · `upperarm_l/C02_magnet_cartridge` × 1

### A06 · 右臂 1/2

- [ ] 01 · H008 · `frame/clavicle_r.protract_frame` × 1
- [ ] 02 · W002 · `frame/forearm_r` × 1
- [ ] 03 · H010 · `frame/elbow_r` × 1
- [ ] 04 · X062 · `frame/clavicle_r` × 1
- [ ] 05 · X066 · `frame/upperarm_r` × 1
- [ ] 06 · P071 · `upperarm_r/C01` × 1
- [ ] 07 · X061 · `upperarm_r/P_case_plus` × 1
- [ ] 08 · X065 · `upperarm_r/D_case_plus` × 1
- [ ] 09 · P073 · `upperarm_r/C14` × 1
- [ ] 10 · X032 · `hand_r.deviate/sensor_cassette` × 1
- [ ] 11 · X030 · `forearm_r.twist/sensor_cassette` × 1
- [ ] 12 · X028 · `clavicle_r.elevate/sensor_cassette` × 1
- [ ] 13 · X009 · `upperarm_r/C01_sensor_cassette` × 1
- [ ] 14 · X031 · `hand_r.flex/sensor_cassette` × 1

### A07 · 右臂 2/2

- [ ] 01 · H012 · `frame/hand_r.flex_frame` × 1
- [ ] 02 · X027 · `clavicle_r.protract/sensor_cassette` × 1
- [ ] 03 · X029 · `elbow_r.flex/sensor_cassette` × 1
- [ ] 04 · N004 · `forearm_r.twist/magnet_cartridge` × 1
- [ ] 05 · X010 · `upperarm_r/C02_sensor_cassette` × 1
- [ ] 06 · N004 · `elbow_r.flex/magnet_cartridge` × 1
- [ ] 07 · P074 · `upperarm_r/C15` × 1
- [ ] 08 · N004 · `clavicle_r.protract/magnet_cartridge` × 1
- [ ] 09 · P072 · `upperarm_r/C02` × 1
- [ ] 10 · N004 · `hand_r.flex/magnet_cartridge` × 1
- [ ] 11 · N004 · `clavicle_r.elevate/magnet_cartridge` × 1
- [ ] 12 · N004 · `hand_r.deviate/magnet_cartridge` × 1
- [ ] 13 · P084 · `upperarm_r/P_magnet_cap` × 1
- [ ] 14 · P185 · `frame/hand_r` × 1
- [ ] 15 · P089 · `upperarm_r/D_magnet_cap` × 1
- [ ] 16 · N003 · `upperarm_r/C01_magnet_cartridge` × 1
- [ ] 17 · N003 · `upperarm_r/C02_magnet_cartridge` × 1
- [ ] 18 · X063 · `upperarm_r/D_pcb_clip_-14` × 1
- [ ] 19 · X059 · `upperarm_r/P_pcb_clip_-14` × 1
- [ ] 20 · X064 · `upperarm_r/D_pcb_clip_+14` × 1
- [ ] 21 · X060 · `upperarm_r/P_pcb_clip_+14` × 1
- [ ] 22 · P083 · `upperarm_r/P_radial_pad` × 1
- [ ] 23 · P088 · `upperarm_r/D_radial_pad` × 1

### A08 · 左大腿与左腿关节小件

- [ ] 01 · X073 · `frame/thigh_l` × 1
- [ ] 02 · P095 · `thigh_l/C14` × 1
- [ ] 03 · P093 · `thigh_l/C01` × 1
- [ ] 04 · P094 · `thigh_l/C02` × 1
- [ ] 05 · X069 · `thigh_l/P_case_plus` × 1
- [ ] 06 · X072 · `thigh_l/D_case_plus` × 1
- [ ] 07 · P096 · `thigh_l/C15` × 1
- [ ] 08 · X012 · `thigh_l/C02_sensor_cassette` × 1
- [ ] 09 · X016 · `foot_l/C02_sensor_cassette` × 1
- [ ] 10 · X025 · `calf_l.flex/sensor_cassette` × 1
- [ ] 11 · X015 · `foot_l/C01_sensor_cassette` × 1
- [ ] 12 · X011 · `thigh_l/C01_sensor_cassette` × 1
- [ ] 13 · X026 · `ball_l.flex/sensor_cassette` × 1
- [ ] 14 · N004 · `calf_l.flex/magnet_cartridge` × 1
- [ ] 15 · N004 · `ball_l.flex/magnet_cartridge` × 1
- [ ] 16 · P106 · `thigh_l/P_magnet_cap` × 1
- [ ] 17 · P111 · `thigh_l/D_magnet_cap` × 1
- [ ] 18 · N003 · `thigh_l/C01_magnet_cartridge` × 1
- [ ] 19 · N003 · `thigh_l/C02_magnet_cartridge` × 1
- [ ] 20 · N003 · `foot_l/C01_magnet_cartridge` × 1
- [ ] 21 · N003 · `foot_l/C02_magnet_cartridge` × 1
- [ ] 22 · X068 · `thigh_l/P_pcb_clip_+14` × 1
- [ ] 23 · X067 · `thigh_l/P_pcb_clip_-14` × 1
- [ ] 24 · X071 · `thigh_l/D_pcb_clip_+14` × 1
- [ ] 25 · X070 · `thigh_l/D_pcb_clip_-14` × 1
- [ ] 26 · P105 · `thigh_l/P_radial_pad` × 1
- [ ] 27 · P110 · `thigh_l/D_radial_pad` × 1

### A09 · 右大腿与右腿关节小件

- [ ] 01 · X080 · `frame/thigh_r` × 1
- [ ] 02 · P117 · `thigh_r/C14` × 1
- [ ] 03 · P115 · `thigh_r/C01` × 1
- [ ] 04 · P116 · `thigh_r/C02` × 1
- [ ] 05 · X076 · `thigh_r/P_case_plus` × 1
- [ ] 06 · X079 · `thigh_r/D_case_plus` × 1
- [ ] 07 · P118 · `thigh_r/C15` × 1
- [ ] 08 · X013 · `thigh_r/C01_sensor_cassette` × 1
- [ ] 09 · X014 · `thigh_r/C02_sensor_cassette` × 1
- [ ] 10 · X017 · `foot_r/C01_sensor_cassette` × 1
- [ ] 11 · X018 · `foot_r/C02_sensor_cassette` × 1
- [ ] 12 · X033 · `calf_r.flex/sensor_cassette` × 1
- [ ] 13 · X034 · `ball_r.flex/sensor_cassette` × 1
- [ ] 14 · N004 · `calf_r.flex/magnet_cartridge` × 1
- [ ] 15 · N004 · `ball_r.flex/magnet_cartridge` × 1
- [ ] 16 · P013 · `thigh_r/P_magnet_cap` × 1
- [ ] 17 · P126 · `thigh_r/D_magnet_cap` × 1
- [ ] 18 · N003 · `thigh_r/C01_magnet_cartridge` × 1
- [ ] 19 · N003 · `thigh_r/C02_magnet_cartridge` × 1
- [ ] 20 · N003 · `foot_r/C01_magnet_cartridge` × 1
- [ ] 21 · N003 · `foot_r/C02_magnet_cartridge` × 1
- [ ] 22 · X074 · `thigh_r/P_pcb_clip_-14` × 1
- [ ] 23 · X075 · `thigh_r/P_pcb_clip_+14` × 1
- [ ] 24 · X077 · `thigh_r/D_pcb_clip_-14` × 1
- [ ] 25 · X078 · `thigh_r/D_pcb_clip_+14` × 1
- [ ] 26 · P012 · `thigh_r/P_radial_pad` × 1
- [ ] 27 · P125 · `thigh_r/D_radial_pad` × 1

### A10 · 双侧小腿与脚掌骨架

- [ ] 01 · W006 · `frame/calf_r` × 1
- [ ] 02 · W007 · `frame/calf_l` × 1
- [ ] 03 · P130 · `foot_l/C14` × 1
- [ ] 04 · P130 · `foot_r/C14` × 1
- [ ] 05 · W003 · `frame/ball_l` × 1
- [ ] 06 · W001 · `frame/ball_r` × 1
- [ ] 07 · W016 · `frame/foot_l` × 1
- [ ] 08 · W017 · `frame/foot_r` × 1
- [ ] 09 · P131 · `foot_l/C15` × 1
- [ ] 10 · P131 · `foot_r/C15` × 1

### T01 · 可选：O22 传感器安装小样

- [ ] 01 · T001 · `sensor_coupon/sensor_bridge` × 1
- [ ] 02 · T002 · `sensor_coupon/magnet_bridge` × 1
