# O24E 整机结构改版

从冻结的 O24D 制造网格派生；只写 `cad/revO24E` 与 `bench/revO24E`。原 D、T5、T6 不重建、不覆盖。

H：按用户决定接受 T5 实装与 T6 继承依据；W：用户实装认可。二者都不是本轮开工前置试验。T6 R 不接受；本版不得复制其轴向敞口固定芯。

运行入口：在 design 根目录以 `.venv/Scripts/python.exe -B -X utf8 Hardware/PoseDoll44/cad/revO24E/build.py` 构建。验证、制造输出和审查入口由以下脚本生成。状态与未完成项以新目录的实际验证结果为准，不承继旧 PASS。

交付入口为 `bench/revO24E/START_HERE.html`；离线交互三维为 `preview/index.html`。Blender和GLB使用实际连续生产件；原始建模特征只保留作审计，不等于打印件。46个打印体、1个钢体以及全部五金分开列明。打印工程针对A1 mini、0.4喷嘴、PLA、0.12层高；首件公差仍需核验。

再生成顺序（所有Python命令加 `-B -X utf8`）：

1. `build.py`，冻结旧D/T6输入，生成本版几何。
2. `production.py make` → `production.py validate` → `production.py printing`。截面检查未通过时禁止切片。
3. `verify.py motion`、`verify.py capture`、`verify.py kinematics`、`retention.py`、`sensor_checks.py`。再用 `verify.py capture --production`、`retention.py --production`、`sensor_checks.py --production` 检查实际生产分件；名义特征检查不能代替这三项。
4. `extended_checks.py rom`、`extended_checks.py paths`、`extended_checks.py grids`。冻结几何期间可并行运行这些独立检查，不能同时重建模型。
5. `electronics.py`，然后 `checks_system.py` → `extended_checks.py ue` → `protocol.py`。
6. Blender后台运行 `render.py`；再运行 `deliver.py`、`preview.py`，在浏览器核查三维、姿态和逐件动画。
7. `audit.py`、`deliver.py docs`、`deliver.py manifest`。ZIP包含文件指纹和来源源码。

本次最终运动报告还包含`delta_motion.py`的可追溯增量证据：`reference/motion_baseline_5a06`保存已完成全量运动扫描的几何和报告；骨链及未修改网格逐数组相等才允许复用其未变碰撞对，每个修改件涉及的碰撞对均在全部原采样点重新计算，并与完整检查器抽检对照。这个参考目录只证明运动检查来源，不能当作另一套已验收装配或打印版本。需要时可按第4步重新执行全量扫描。

Python依赖为numpy、scipy、manifold3d、trimesh、matplotlib；切片使用本机OrcaSlicer，渲染使用Blender。生成器依赖本设计仓库中冻结的D/T6几何及原D/T1辅助代码，因此源码须放回 `Hardware/PoseDoll44/cad/revO24E` 运行。交付的Blender、GLB、STL、3MF和离线HTML可以独立检查，不需要先运行生成器。

有限几何检查不能证明实际摩擦系数、打印批次强度、螺纹公差、板件标定或100次不补紧寿命。未烧录固件、未连接UE运行时；新腕采用Ry屈伸后Rx尺桡偏，旧腕标定无效。使用空白实测记录逐项验收；`manufacturing_release=false`保持到实物资格完成。
