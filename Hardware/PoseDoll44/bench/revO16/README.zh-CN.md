# PoseDoll O16 Universal

一个实体型号，46路原始测量，25个模块，数字中立高度492.14 mm。

先读 DESIGN.zh-CN.md 与 DESIGN_STATUS.json。本包是数字设计候选，不是整机制造放行。连续全域避碰、带线实测、标定、保持力及O16的Manny/Quinn端到端UE验证尚未通过。

本轮保留O15 Quinn机械几何，取消第二体型；新建目标无关的实际机械模型与采集参考实现。不是重新优化后的另一套关节STL。完整打印数量见 PRINT_UNIVERSAL.csv：214种、273件；同一编号的STL/3MF不要重复打印。

查看三维：解压后在本目录运行 `python -m http.server 8771 --bind 127.0.0.1`，打开 http://127.0.0.1:8771/viewer/index.html 。页面不依赖互联网库。

完整性检查：`python source/verify_package.py`，仅用标准库。
测量参考测试：安装独立环境的NumPy后运行 `python source/test_device.py`。

profiles/calibration_INCOMPLETE.json必须保持未标定状态，直到填写真实证据；measurement_SYNTHETIC.json只是格式示例。source/device.py是离线参考，未接入生产串口或UE。target_adapter_contract.json是适配任务契约，不是已完成的角色配置。

historical_o15/仅提供原装配/采购工艺参考；原文中的Quinn指本版几何来源，不代表还需要第二台人偶。电子和固件使用原型号名称以保持可追溯。默认固件未绑定真实MAC，不直接作为已配对硬件。

原工作区可用 cad/revO16/build.py 复建配置、清单与查看器，用package.py重建本包；完整机械重建仍需要工作区内的历史CAD依赖。
