O24E R4 — 根据R3实际装配反馈修改
从 START_HERE.html 开始；新动画在 assembly_guide/index.html（201步）。
R3升级：替换重打P005、P007、P012，另打印J001托叉和J002导向针各1；其余8件STL逐字节复用。
printing/R4_REPRINT_3_PLUS_2.3mf为5件升级盘；printing/STOCK_ARM_01.3mf为11个整臂零件＋2个工装的完整盘，二选一。
压盖复用原M3×16和W3，反向安装后用12颗普通M3（AF5.5×2.4）对顶；原6颗压盖NL3留作备件。关节的11颗NL3继续保留。
准备两把5.5薄开口扳手、3mm有效直杆至少120mm内六角、2.5mm内六角，以及软口台钳／桌夹。
托叉只承托散件，不用于压簧；肩钉捕获后抽出托叉，再预紧。定位筋只负责临时留片；8面必须在开放台面先压入并轻翻转不掉片，再合叉。
逐步路径、指腹与工具包络、防脱、850姿态、打印工程、浏览器已核对；新实物配合／留片力／双螺母保持／疲劳未实测。已接受T6 H/W的状态不变。电子预留保留，附件仍未发布生产版。
完整重建：build_stock → export_stock → tooling → check_stock（默认及--dense）→ validate_stock --cores → check_r4 → load_stock → electronics_review → print_stock → render_stock（Blender）→ guide build/verify_r4 → deliver_r4 → guide build/verify_r4/docs → 浏览器核对 → guide package_r4 → audit_r4。依赖原仓库冻结输入及Python/Blender/Orca。
旧R3与旧动画均保留。
