# PoseDoll 小样实验室

> 2026-09-25 更新：此页保留为 O7 备选方案的实验教学。新发现的 2014 / 2016 多轴关节复用路线尚在数字恢复阶段，专用试片暂缓采购；下载包仍是 O7 原始资料，不是 TUT 关节制造包。见[复用评估](../../docs/TANGIBLE_2014_2016_REUSE.zh-CN.md)。

入口：[index.html](index.html)。用 Chrome、Edge 等现代浏览器双击打开即可；所有脚本、样件模型和样式均在本地，不依赖 CDN，不需要 npm 或联网。

五个章节依次介绍零件、碟簧压缩动画、摩擦试验动画、准备送检、结果交接。也可直接进入「准备与送检」，复制三类询价说明并下载 ZIP。页面不会发送消息或购买零件。

- 模型可以拖动、滚轮缩放；键盘方向键旋转、加减号缩放、Home 复位。提供俯视、自动旋转和暂停。
- 每个测试步骤可手动切换，动画可播放/暂停或拖动进度。默认不自动播放；切换章节、隐藏页面和启用减少动态效果时会暂停。
- 准备清单仅存当前浏览器的 localStorage。询价说明可编辑，页面内切换联系人时保留修改，刷新后恢复默认。文件与 HTTP 地址是不同的存储来源。
- 复制失败时弹出可手动复制的文本框；准备页可打印。下载的空白模板不会自动写入任何测试数据。
- 4 个试片网格提取自当前 O7 STEP，来源哈希见 assets/provenance.json；2 种碟簧按目录名义尺寸建模。材质颜色、光照、实验台架为教学示意，不是供应商照片、加工图或实验仿真。
- 动画进度不等于真实压缩量，60 秒停留演示经过加速。当前无实测数据；没有把小样验证当作整关节合格或制造放行。

## 文件与重建

本目录独立于 O7 已封存交付物，未修改其源文件。数据来自 ../../bench/revO7，双面保持预算由原 plan.json 读取到离线资源。

在 design 根目录，用已安装 CadQuery 运行：

```powershell
.venv/Scripts/python.exe -X utf8 Hardware/PoseDoll44/tools/run_cad.py Hardware/PoseDoll44/tutorials/first-bench/tools/build_assets.py
```

输出 assets/cad-data.js、assets/provenance.json 和 assets/bench-handoff.zip。Zip 包只含 O7 原始小样资料与本指南的 HANDOFF.zh-CN.md，不含整机制造文件。

验收脚本：tools/check_guide.cjs。脚本验证真实浏览器中的六个模型、分步动画、导航、复制降级、持久清单、资料链接及窄屏显示；报告仅证明页面功能，不是硬件测试。

