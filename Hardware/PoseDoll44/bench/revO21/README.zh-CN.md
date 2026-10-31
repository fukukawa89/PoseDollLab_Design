# O21 单台低成本 USB 人偶：目标约 1500 元

本包是 **降本工程设计候选**，不是完整可下单的整机制造包。目标预算 ¥1482.50，按已有打印机、自行打印与机械总装、电子板和线束外包、包含必要备件与运费计算。0 份正式报价，较贵情形约 ¥2210；不含多轮开发失败或购买计量设备。

保留 O20 骨架、46 路原始测量、41 个语义旋转自由度、已获用户实测通过的 O11 摩擦原理和双髋各外移 16mm。新采集方案为 MT6701CT-STD-R＋3×16 路 DO 选择器＋XIAO USB 主控。新 P21R/1 固件、电路和线束不能与 O20/AS5048A 六针级联混装。

- **DESIGN.zh-CN.md**：完整设计、原厂依据、预算与精度边界。
- **RFQ.zh-CN.md / budget.json**：加工方询价清单与逐项预算，包含工程最低收费检查。
- **electronics/sensor**：12×10×1mm SOP8 单面元件小板，ERC/DRC 通过；没有磁场/机构配合实测。
- **electronics/carrier**：中央原理图和网表，ERC 通过；尚未布局布线或确认所有精确采购料号。
- **firmware_source / firmware_binaries**：编译通过的 ESP32-S3 工程候选；没有刷写或连接实物。
- **source**：USB 解码、可选实测周期误差表、机械 FK；保存原始包与标定，拒绝缺轴/过期/坏数据。
- **profiles**：46 路绑定；未标定的空模板，不得冒充已测标定。
- **verification**：本轮软件、电路、浏览器检查记录。
- **mechanical_baseline.json**：O20 版本与 ZIP 哈希。原机械打印文件在已保存的 O20 包中，本包不重复旧整机制造文件。

先运行 python serve_preview.py，打开终端提示的本地地址（viewer/index.html）。预算页也可直接离线打开。便携包中的“机械继承记录”是 O20 来源文件；完整可交互三维页在仓库 tutorials/full-doll-o20/index.html。

软件复核（安装 requirements-reference.txt 中依赖）：

    python source/test_device.py
    python source/test_o21.py
    python source/verify_package.py

本机固件可用 firmware_source/build.ps1 -BuildRoot <独立构建目录> 编译；脚本内记录了本次 ESP-IDF 6.1 的本地工具路径，异机需调整。source_build 中的生成脚本依赖完整设计仓库及其历史输入；它们用于追溯，不是脱离仓库的自动再造程序。KiCad 10 原生文件可独立打开，标准封装依赖 KiCad 10 库。

未完成：中央 PCB 布线/DFM，精确保险丝和连接器定料，新器件/控制盒/线束整机 CAD 集成，相邻机构出线避碰，磁场与全范围角度标定，供应商正式报价，生产 UE 适配及保存/重开验收。O11 已通过的摩擦配合不会因此被重新列为未通过。
