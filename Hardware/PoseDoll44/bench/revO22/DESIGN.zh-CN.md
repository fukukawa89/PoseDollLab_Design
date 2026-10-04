# O22 单人偶工程设计说明

2026-10-01。以已保存的 O21（5537190 / posedoll-o21-costdown-20261001）为基线，落实《分支 · 审查O21方案成本》的12项意见。**本版是可询价、可制作首件的工程候选，不是整机制造放行。** 正式状态见 [优化清单](optimization_tracker.json)。

## 功能与边界

一套 USB 人偶，25个关节模块、46路原始机械轴、41个语义自由度；不依赖摄像头、不加电机。保留 O20 的骨长、关节中心、腿杆走向及已经接受的双髋各16mm外移。A站姿最大实体高度491.716mm，低于600mm。根节点世界位移、根旋转、手指由UE编辑；脊柱/颈部细分属于已声明的派生映射，不伪称逐骨实测。目标角色的接触、贴地、蒙皮穿插由动画师后期调整。

O11的打印尺寸、螺钉垫片配合与可调摩擦已由用户于2026-09-30确认通过。本版不要求重复证明该摩擦原理，也不添加额外摩擦副。新测试只针对新传感板、安装、线束与读数。

## 已实现的优化

1. **限位诊断保留真实读数。** 容差为每轴独立标定误差上界加14bit半个计数，标定上界最高1.25°。限位附近标记`BOUNDARY_UNCERTAIN`，不把角度钳到限位；明显越界或多周解释不唯一则拒绝。
2. **120ms是总年龄。** 从最终一轮最早的通道采样到主机求值时刻计算，不把扫描时间与USB延迟分开各放宽120ms。500ms历史稳定窗口仍保留。
3. **默认A站姿。** 上臂约35°外展，所有原始轴距机械限位至少3°；只改变默认摆姿，不重定义机械零位或参考坐标。
4. **装好以后标定。** 支持有限行程的分段线性误差表及0/360°跨界。至少5个拟合点、相邻编码器跨度≤15°；独立验证角度至少4个、每角度正反向到达；不在未测区外推。独立参考不确定度≤0.1°，独立验证最大误差≤1°、正反向差≤0.3°。保留原始读数、原始USB包、标定内容与哈希。
5. **SOP8托架。** 34个可拆托夹与12个端轴安装位按12×10×1mm PCB、SOP8最大包络调整。元件面距服务坐标原点15.95mm，磁铁顶12.9mm；含焊接高度1.50–1.85mm与两个±0.10mm位置公差后，封装外壳至磁铁间隙为1.00–1.75mm。这不是芯片内部敏感面磁距的保证；磁状态和装后角度误差必须测量。
6. **线束实物模板。** 46根五芯线独立回中央板，三组14/16/16路。全部端口与载板位号对应。完整左臂10路包含锁骨、肩、肘、前臂与两个腕轴。新增`harness/routing_plan.json`列出实际安装坐标、固定骨段、234个离散姿势下的路径长度和松弛余量。最长预切750mm；46路每色合计22.75m，五色合计113.75m；另加两套750mm备件和加工损耗。折线路径只用于装配定位，必须弯成≥7mm半径；未证明动态无夹线或疲劳寿命。
7. **真正布线的中央板。** 80×94×1.6mm四层，外层35µm、内层17.5µm；地与SENSOR_3V45各占一内层。原两层细线方案的远端压降不足，因此改为四层。传感板与载板最终ERC、DRC、未连接和原理图一致性检查均零错误。Gerber、钻孔、坐标与BOM在`manufacturing/`。四层不等于SI、EMI、温升或波形已验证。
8. **电源料号和压降。** AP3429AW5-7，L1=74438357022，输入PTC=1206L110THR，输出保险丝=0467001.NR；R50/R51=316k/66.5k、0.1%、≤25ppm/K。电源标称3.451V，不能将它接入只允许3.3V的外部未知设备。按46×14mA加80mA逻辑、60°C铜阻、750mm AWG30、接触电阻、热态保险丝≤0.15Ω及电阻温漂计算，远端最低3.141V、空载上界3.532V。电源实际热阻、纹波及远端电压仍需验证。计算见`verification/power_budget.json`。
9. **UE可编辑闭环。** P21R原始包→CRC/新鲜度/稳定性→标定→机械FK→语义旋转→目标适配→Control Rig关键帧。Manny与Quinn分别保留目标Mesh的参考骨长；修复Quinn意外使用Manny初始骨变换的问题。4个姿势×2个角色通过保存和新进程重开；手腕编辑与撤销通过。全部证据标注合成输入，真实硬件仍待验收。

## 机械交付与限制

完整打印包150种、186件：185件在人偶上，1件XIAO板间距治具。X001–X081为本轮替换件，全部按实际装配实体导出、单实体检查，并做3MF数值回读；其余文件保持O20内容。不能把`mechanical/section/`或预览中的剖切模型当作打印文件。固定载板用4颗M2×6塑料自攻螺钉，盒盖用两条2.5mm扎带。XIAO两排针中心距15.24mm，板间净距4.0mm，继续使用P242治具。

背盒外尺寸86×100×27mm。打印实体体积从585.50增至599.36cm³，增加13.86cm³；按1.24g/cm³实心换算约17.2g，但不是切片耗材或实物重量。**本轮没有减少整机打印件，也不宣称整机减重。**

74个离散姿势中，O22改动没有增加被检查的相邻运动件相交；4个UE示例姿势的相邻检查为零。报告仍保留旧版极限姿势接触：如肩原始r0约−170°、肘−90°、前臂扭转约106°及145°、腕屈伸145°、胸侧摆45°。这些位置不能当作已经放行的无干涉工作范围，也不能因为“旧版就有”而忽略。原始传感器限位仅为读数诊断范围，不是可用机械空间的证明。没有连续、多轴组合全范围证明；首件需测定实际可用范围后再放行。骨盆与胸部之间隔着腰段，属于用户允许通过姿势避让的非相邻碰撞，独立记录。

## 使用顺序

先看[实物验收](physical_tests/ACCEPTANCE.zh-CN.md)。加工方先做少量电子首件；用已通过的O11小样加两个新测试支架验证磁距和读数，再做16路长支路及完整左臂。通过后装46路，完成真实标定与Manny/Quinn保存重开。`physical_tests/`的空表全部保持未测试，不自动填通过。

主机安装`requirements-reference.txt`。从本目录运行：

```powershell
python source/calibrate_axis.py measured_axis.json --output axis_result.json
python source/assemble_calibration.py --profile profiles/device_profile.json --device-id REAL_USB_ID --axis-dir measured_axes --tests physical_tests/test_manifest_INCOMPLETE.json --output calibration_MEASURED.json
python source/usb_capture.py --port COM实际端口 --profile profiles/device_profile.json --calibration calibration_MEASURED.json --output capture.record.json
python source/ue_export.py --profile profiles/device_profile.json --record capture.record.json --output capture.payload.json
```

UE插件增加`SolveMeasuredPose22`和`CaptureMeasuredPose22`；Python入口为`unreal.PoseDollEditorLibrary.capture_measured_pose22(sequence, rig, frame, payload_path, target_profile_path, False)`。调用前在Sequencer打开指定序列并刷新绑定；要求单个Control Rig段、目标Mesh匹配、可写且无时间变换。正式入口拒绝未完成实物资格的数据；`allow_synthetic_for_testing=True`只用于明确的数字测试。写入作为可撤销事务，保存由用户编辑流程执行。详见`ue/editor_scripts/`和插件补丁。

固件仍使用O21的P21R/1线协议和46路顺序，二进制按哈希原样继承；协议兼容不是新电路已上电的证据。

## 成本状态

[budget.json](budget.json)分项合计1482.50元，余17.50元；高价情景2220元，正式供应商报价0份。现有打印机、自行打印/机械装配，外包贴片、压接和板端焊接，计入备件、最小订单、工程费与运费。不要把LCSC美元参考价当国内含税到手价。外部计量仪器若需购买或付费借用，必须补入实际报价；当前精度门槛不能通过免费的假设放宽。询价与返价核算见[RFQ](manufacturing/RFQ.zh-CN.md)。

## 主要器件依据

- [MT6701 Rev1.9中文手册，2024.05](https://atta.szlcsc.com/upload/public/pdf/source/20260616/FEB700C1922508565884FF0A90656B50.pdf)：电源、SSI、SOP8尺寸与精度限值；14bit分辨率不等于14bit绝对精度。
- [JST SH官方图册](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf)：BM05B-SRSS-TB、SHR-05V-S、SSH-003T-P0.2-H及线径配合。
- [AP3429官方手册](https://www.diodes.com/datasheet/download/AP3429.pdf)、[74438357022电感](https://www.we-online.com/components/products/datasheet/74438357022.pdf)：电源额定条件与电感下方禁铜要求。
- [Littelfuse 467](https://www.littelfuse.com/assetdocs/fuse-467-datasheet?assetguid=4a59f034-1cca-460e-a5ba-e1e66247c76d)、[1206L](https://www.littelfuse.com/assetdocs/littelfuse-ptc-1206l-datasheet?assetguid=2b6a1515-d4ee-4c83-8bd4-152b4901b8f5)：额定值；典型冷态电阻不能代替热态上限。
- [Vishay TNPW e3](https://www.vishay.com/docs/28758/tnpw_e3.pdf)、[Murata 22µF参考规格](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR61A226ME51-01A.pdf)：电阻等级与电容额定值；供应商必须补DC偏压曲线与实际AVL。
- [MT6701CT-STD-R公开价格](https://www.lcsc.com/product-detail/C3003196.html)：2026-10-01所见30+档US$1.0355；50颗US$51.775，以7.00仅作预算换算。
