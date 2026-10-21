# O22 拼装教程包

直接打开 tutorials/assembly-o22/index.html 可阅读全部文字、打印盘编号图、26 张 CAD 装配图与接线图。ASSEMBLY.zh-CN.md 是相同内容的文字版。

如需旋转 CAD，在已安装 Python 的电脑上，进入本文件所在目录运行 `python start_preview.py`；它只监听本机 127.0.0.1:8772，并打开浏览器。用 Ctrl+C 结束。没有 Python 时仍可直接阅读 HTML 图片与清单。

按“打印盘找件 → G1–G5 通用装法 → S01–S25 关节 → S26 中央板 → 接线 → 分段上电”的顺序使用。912 件金属件、46 颗磁铁均已分配到具体步骤。诊断脚本只在你明确指定串口时读设备，不烧录、不输出 UE 动画，也不把局部原始诊断当已通过标定的测量。

本版打印工程位于上级 projects（Orca）和 crosscheck_bambu（拓竹），两套几何相同，只选一套打印。F01–F12 是主套，S01 是额外试件。彩色支撑识别、拆除说明与验证状态见上级 index.html。PCB 制造 Gerber 仍使用原 PoseDoll_O22_Engineering_Package.zip。

本教程不改变人偶设计；O11 配合和摩擦使用用户已通过的结论，O22 电子与整机实物项目仍须首件验证。
