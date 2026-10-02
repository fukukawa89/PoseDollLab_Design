# O17 简化小样候选

O16已保存为26255df / posedoll-o16-saved-20260930。O17为一台人偶，202件/124种打印件，46路测量、41个语义旋转自由度，USB直连，无摄像头。

先读DESIGN.zh-CN.md和POWER_AND_USB.zh-CN.md。原有整机干涉仍存在；禁止把增量回归通过当作整机无干涉或制造放行。先做FIRST_PRINT.json中的四件小样。

- print_batch与PRINT_UNIVERSAL.csv：净数量，STL/3MF二选一。
- electronics：C1-U装配，D1不装；裸板铜层沿用。
- source：离线FK、故障检查、USB参考工具；需实测标定。
- firmware_source与firmware_binaries：USB固件源代码及编译产物，未刷入实物。P17R与旧P15R不兼容。
- verification：实际检查结果与截图，含已有干涉配对。
- cad_source：复建源代码；依赖原设计仓库冻结输入。

用Python运行serve_preview.py，再打开http://127.0.0.1:8771/viewer/index.html。命令行可运行python source/test_device.py与python source/test_usb.py；这些离线测试不会连接或刷写硬件。运行python source/verify_package.py可核验全部文件及原ZIP的SHA-256。
