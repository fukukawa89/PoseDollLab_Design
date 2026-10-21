# O19 腿杆对齐优化

O18已保存：08e8f8b / posedoll-o18-prototype-20260930。O19仍为一台188件、117种打印件，替换L001至L004四件腿杆；原端部与46路测量不变。

O11小样的配合和可调摩擦已获用户实测通过，不增加摩擦冗余。髋中心各外移16mm与既有整机干涉仍保留，详见DESIGN.zh-CN.md和DESIGN_STATUS.json。

运行python serve_preview.py，打开http://127.0.0.1:8771/viewer/index.html。完整性检查：python source/verify_package.py。采集/USB测试：python source/test_device.py、python source/test_usb.py。

四件新STL与3MF见print_batch/L001至L004；旧件按同目录单台清单使用。verification含数字几何检查、用户O11报告及未采用的髋零偏移试算。四轴分解插值不等同于连续机构轨迹证明。

CAD复建依赖仓库内冻结旧版输入；cad_source中experiment/search脚本是探索记录，不是正式打印件生成器。正式构建入口为design.py、export.py。USB固件与电子件未改动；原标定仍需与实物传感器对应。
