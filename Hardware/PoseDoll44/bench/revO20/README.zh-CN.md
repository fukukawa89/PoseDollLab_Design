# O20 单台USB人偶：少10件，打印体积少2.8%

O19已保存：98c084a / posedoll-o19-leg-alignment-20260930。O20独立提供115种、186件单台打印清单，其中185件装在人偶上，1件为焊接治具。

合并两侧脚趾固定外壳，少2件打印件、4颗M3×20螺钉、4个M3螺母。14件骨架中23段芯孔及控制盒开孔使CAD打印实体少约16.845 cm³。按历史PETG实心口径合计约减29.35 g，非称重；实际值应对比相同切片设置。

双髋各外移16 mm按用户决定保留。远端部件相碰按姿势避让处理，相邻机构仍检查。O11配合与可调摩擦已由用户报告通过，不增加摩擦冗余。

W001–W017为新打印件，其余沿用；W016/W017用原肩轴和垫片。空心杆切片查看最大5 mm内腔桥接，避免无法取出的内部支撑。制造网格已回读验证；新杆加载刚度与UE端到端尚未实测。

运行python serve_preview.py，打开http://127.0.0.1:8771/viewer/index.html。完整性检查：python source/verify_package.py。已有采集/USB测试：python source/test_device.py、python source/test_usb.py。

详见DESIGN.zh-CN.md、PRINT_UNIVERSAL.csv、DESIGN_STATUS.json及verification。cad_source的正式构建入口为design.py、export.py；复建依赖仓库冻结历史输入，打印无需复建。
