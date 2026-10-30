O24E R3 — 固定分件合并版
从 START_HERE.html 开始；MERGE_REVIEW.html 解释4组固定连接的去留。
相对R2，只需新打印S3-P010一体腕输出叉与手掌，替代S2-P010和S2-P011。其余10个R2打印件逐字节相同，可直接复用。编号P011撤销，P012不改号。
整臂11个打印件＋130件标准五金，减少M2×20一颗、W2两片、NL2一颗。旧R2分件若继续使用，仍需原4件掌部五金。
printing/R3_REPRINT_P010.3mf是单件升级盘；printing/STOCK_ARM_01.3mf是整臂11件盘，二选一。
assembly_guide/index.html是156步安装动画，R3_Assembly_Offline.html为内嵌单文件动画。preview/index.html提供七轴整臂检查及电子空间预留开关。
原R2、原R2教程和更早设计保留。H/W用户接受状态不变。几何、装配与切片已检查；实际保持力、配合、打印强度、蠕变与耐久未实测。电子附件仍未发布生产版本。
source可追溯，重建需原仓库冻结输入、Python、Blender、Orca。顺序：build_stock → export_stock → check_stock（默认、--dense）→ validate_stock（默认、--joins、--cores）→ check_modules → merge_review → load_stock → print_stock → render_stock（Blender）→ electronics_review → deliver_r3 → guide源码build/verify/docs → 浏览器实测 → package_guide → audit_r3。
