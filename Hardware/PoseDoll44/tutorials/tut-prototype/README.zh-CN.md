# PoseDoll O8 真实核心与配合小样指南

用浏览器打开 `index.html`，不需要 npm、CDN 或联网。页面展示真实 STL、原件与 2 mm 改型比较、五段装配路径、量规和标准紧固件外形。任意角度预览不自动判定碰撞。

下载包将首批 6 件量规放在 A_first_fit，后续核心参考件放在 B_core_reference。首批只做 A；阅读包内 START_HERE，不能把标准螺钉模型拿去打印。

`tools/build_assets.py` 从当前完整网格生成 WebGL 数据，`tools/build_handoff.py` 打包并校验归档内容，`tools/check_guide.cjs` 使用本机 Chrome / Playwright 检查交互与布局。模型显示四舍五入到 0.00001 mm，仅供可视化；数字报告使用完整精度输入。

`verification` 是页面验证，不是机械实测。当前无硬件、无制造放行；后续还需真实尺寸、阻力、保持、受载与完整装配验证。
