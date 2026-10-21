# 设计与验证脚本

这些脚本用于审阅和在原 O22 仓库内继续修改，不是独立安装程序。标准打印入口是 ../projects/ 中的最终 3MF。

依赖：Python 3.13、NumPy 2.5.3、manifold3d 3.3.2、Shapely 2.1.2；切片使用本机 Bambu Studio 02.08.02.61。软件路径和本地依赖目录见源码。

需要原工程的 print_batch、a1mini/manifest.json、a1mini_supports/design 保护区与面选择、原生支持项目模板，以及 .local/o22-easy-support/S00/manifest.json。脚本应放回原仓库 scripts 目录运行，不能直接在本交付目录运行。

流程：定义鳍方向、分段、保护区；生成连续触底的薄鳍；独立逐层检查；针对原件新层区域添加定点鳍；裁掉不可打印的层边缘；重新核对触底、碰撞和退出路径；写入原生项目、切片并检查实际路径。任何修改后必须重新进行这些检查，不能沿用本次报告。

最终几何在 3MF 内以普通子零件保留：原件、FIN_BODY、BREAKAWAY_TEETH。原件不被布尔修改；颜色查看数据来自最终几何。输入文件散列见 ../verification/source_inputs.json。
