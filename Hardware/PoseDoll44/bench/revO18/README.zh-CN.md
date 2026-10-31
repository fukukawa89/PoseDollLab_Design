# O18 一体单轴外壳简化版

O17已保存：5a5ac22 / posedoll-o17-prototype-20260930。O18单台188件、117种打印件，额外小样Q001/Q002不计入整机数量。保留46路测量，去掉14件半壳和56件壳体紧固件。

先读DESIGN.zh-CN.md、POWER_AND_USB.zh-CN.md和FIRST_PRINT.json。整机仍有已知干涉，不可把本轮增量回归通过当作整机放行。先验证关节小样。

source中的测量/USB引擎与固件沿用O17版本，P17R/1未变；profiles是O18配置，必须实测标定。

运行python serve_preview.py后打开http://127.0.0.1:8771/viewer/index.html。离线测试：python source/test_device.py、python source/test_usb.py。完整校验：python source/verify_package.py。这些测试不会连接或刷写实物。

CAD复建依赖设计仓库冻结的O15/O17输入，cad_source不是独立依赖全集。验证报告与网页截图见verification。
