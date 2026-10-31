# O24E 左臂机械试装子集

按用户选择提取左肩关节到手掌的 7 个自由度。固定输入为 E-P003；不含锁骨两轴、胸部、PCB、磁铁、线束或其专用紧固件。9 个实际打印体完全复用 O24E 的 STL，不重新切割、缩放或合并材料；一体传感器安装位留空。

输出目录：`Hardware/PoseDoll44/bench/revO24E_LArm_Mech`。先打开 `START_HERE.html`。原 O24E 输出保持不变。

从 design 根目录运行：

1. `.venv/Scripts/python.exe -B -X utf8 Hardware/PoseDoll44/cad/revO24E_LArm_Mech/extract_arm.py extract printing preview docs`
2. Blender 后台运行同目录 `render_arm.py`。
3. 检查离线 `preview/index.html` 中 7 轴、逐件动画和固定输入端。
4. 再运行 `extract_arm.py audit docs package`，仅将最终文件打包。

原始几何依赖冻结 O24E 生产数据及其只读坐标辅助函数。打印工程复用本仓库原生 A1 mini / PLA / 0.4 喷嘴配置。源码须在原设计仓库中运行；已导出的 STL、3MF、Blender、GLB 和 HTML 可独立检查。

保留原 O24E 的已接受 H/W 状态；防脱与运动证据按完全相同的生产体继承，明确标记为继承证据，不宣称新做过实物试验。保持力目标仍沿用完整 O24E 的条件计算，不是拧紧扭矩。用空白 `TRIAL_LOG.csv` 记录这只新打印左臂的实际表现；重新生成文档不会覆盖已有试装记录。
