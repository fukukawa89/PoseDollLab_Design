O24E_LArm_Stock — O22 / T6 常见五金左臂试装
从 START_HERE.html 开始。新目录不覆盖原 O24E 或旧单臂。
12个打印件，134件标准五金，1个A1 mini 3MF盘。无电路。
先看 HARDWARE.html 核实规格及库存；旧55件加工项见 CHANGES.html。
STL / Blender / GLB / 逐件教程 / 计算验证 / 空白试装表均包含。
防脱与装配为几何验证，保持力、真实A8曲线、PLA蠕变和100次循环待实装。
source为可追溯脚本，需原仓库中的冻结 O24E/T6/O22 输入及 Python、Blender、Orca。
重建顺序：build_stock → export_stock → validate_stock（默认、--joins、--cores）→ check_modules → check_stock（默认、--dense）→ load_stock → print_stock → render_stock（Blender）→ section_stock → deliver_stock → 浏览器核对 → audit_stock。
