O24E_LArm_Stock_R2 — 2026-10-27 单臂结构修正版
从 START_HERE.html 开始；STRUCTURE_REVIEW.html 是P007及全臂修改对照。
12个机械打印件，134件原规格标准五金，1个A1 mini 3MF盘。只有S2-P012可复用旧E-P019打印件，其余11件使用R2。
本次不装电路；electronics目录为安装空间、板型、角度绑定、走线约束的预留审查。电子附件支架、线束和PCB尚未发布生产版本，预留包络不是生产零件。
STL / Blender / GLB / 151步教程 / 计算验证 / 空白试装表均包含。
原O24D、O24E、T6和R1冻结文件未覆盖。防脱与装配为几何验证；P007均质弹性比较仅用于识别结构改善。保持力、真实A8曲线、PLA蠕变和100次循环待实装。
source需原仓库冻结输入及Python、Blender、Orca。重建顺序：build_stock → export_stock → validate_stock（默认、--joins、--cores）→ check_modules → check_stock（默认、--dense）→ structure_review → load_stock → print_stock → render_stock（Blender）→ section_stock → electronics_review → finish_r2 → 浏览器核对 → audit_stock。
