# O24D · A 字中立完整人偶

2026-10-24。以 bench/revO24D/REVIEW.html 和带当前几何指纹的验证文件为准。S1 通过仍是设计假设，H04 弱连接排除；旧 C/T1 未作为写入目录。本轮之前的 D 包保存在 revO24D_baseline_20261023_pre_integrated；更早基线仍保留。本版不是制造或切片放行。

## 当前输入与规则

双肩外展 45° 为 A 字默认中立及传感器零位，N 只作为冻结 UE 参考坐标。相邻与同一解剖段上的不同运动件必须通过；非相邻接触为姿态调整提示。保留全部 80 个原角度端点，不设旧版 15° 强制联动。

fullbody.py、closures.py、hand_model.py 和 D 内冻结输入生成实体；daily_poses.json、clavicle_route.json、sensor_layout.json 为当前布局输入。其余 *_search.py、proposal 和 history 文件仅为作者工具/历史候选，不是最终验收结果。station 搜索脚本依赖其记录的候选源几何，不能在最终模型上直接重复变换。

长左锁骨承力体是有材料标识的一体定制钢件。CSV 中的特征数不是物理零件数；stl_review_bodies 的 materials 字段说明实际材料。手掌是一体掌片和固定拇指，无新增自由度。背部有已布线主板、38 块传感器板、16 个固定耳及线束导向。

## 重建顺序

从 design 根目录运行 .venv/Scripts/python.exe -B Hardware/PoseDoll44/cad/revO24D/脚本：

1. fullbody.py：生成实体、GLB、装配、接口及 BOM；完成前不要运行读取 NPZ 的检查。
2. rom_cases.py --dense、joint_grids.py、plan_paths.py：逐轴范围、局部多轴网格、从 A 字到日常姿态的路径。三者可并行读取同一完整模型。
3. harness.py、standing.py、electrical_budget.py、integration_checks.py 先依次生成走线质量、地面支撑载荷、电子和新增连接证据，再执行 check_numeric.py：独立 FK、命名姿态、89 骨映射、实际轴线、五金、新质量/预紧/防脱、传感器理想可观测性与选定间隙。载荷复算必须在网格和路径完成后执行。
4. bone_alignment.py：从实际网格截面检查 9 根主连接管；ue_pose_reference.py：以原 UE 网格和权重离线重建 A 字参考；shoulder_conditioning.py 记录仍存在的肩外展 90° 机械奇异位形。
5. groups.py：所有材料审查体的核心连通检查，含单特征手掌；structural_links.py：钢支架与实际切槽固定座的载荷/刚度筛算；final_evidence.py：薄桥正负对照、附件连接、头支撑与 A 字接触记录。
6. rebuild_check.py：在内存独立重建并核对保存的实体，不覆盖模型。
7. wire_scene.py 生成独立走线导向与系统 GLB；Blender 后台运行 render.py，再运行 verify_blender.py，核对真实保存文件。原 UE A 字参考仅作视觉对齐参考，不是 UE 运行时结果。
8. preview.py：打包本地 WebGL；实际浏览器运行 browser_review.js、browser_playback.js 和 browser_local_assets.js，保存结果与截图。
9. delivery.py 初次审计保存文件；review.py（调用 review_A.py）生成当前中文说明；delivery.py --package 再次审计并生成含 SHA256 清单的 ZIP，复核 CRC。

每次几何或材料修改后复算相应证据。当前版本不承继旧 material_removal_proof 的碰撞结论。独立历史报告应移入 history，避免与当前顶层证据混淆。

## 边界

36 单轴和 2 只双轴腕的预紧及防脱使用明确的金属接口；材料、摩擦和工艺值是有条件设计输入，不是实测。有限采样不证明连续空间或任意全身组合。柔性线束在全姿态的实际避夹/疲劳、磁干扰、标定、磨损疲劳、UE 运行时仍待确认。

审查 STL 尚未完成生产分件、打印朝向、补偿或切片，球体合模件仍须分别制造。钢件不得当作打印件生产。预览不依赖外网；serve_review.py 只绑定 127.0.0.1。源码重建依赖原仓库 revO24/revE 辅助模块及冻结 Quinn 输入；模型、报告、图片和预览可独立审查。


原生电子源与走线源在 bench/revO24D/electronics 及 harness 中。electronics_carrier.py / electronics_sensors.py 会覆盖已布线文件，不应为查看模型而执行。它们与保存的 route_input.dsn / route.ses、electronics_route.py、sensor_route_import.py、electronics_finalize.py 构成电路再生流程。现有板已通过原生 ERC/DRC/连通检查；没有生产放行。

harness.py 导出的曲线是 A 字路由导向，实际成束包络参与 A 字实体检查。动态长度预算包含每段端点的最大分离距离与弯曲余量；不宣称全姿态柔性线束避碰或疲劳已验证。Blender 的 Harness A pose routing guides 只在第 1 帧显示；交互预览的随动线束仅作摆姿参考。
