此包包含对 PoseDoll Rev O2 的独立审查和 O3 下一轮任务。
给 Codex：先读 O3_Codex_START.txt。
阅读报告：REVIEW_REVO2_AND_O3_PLAN.zh-CN.md。
局部复算：python audit_revo2_focused.py --output your_results.json
脚本使用标准库；局部CAD需cadquery，接触反例需numpy/scipy。缺库记NOT_RUN，不会假装通过。本次实际运行版本在focused_results.json中。
脚本重建部分源码几何并给出反例，不是原项目完整CAD运行，也不是强度、寿命或实物认证。资料包不含制造放行图纸或新固件。
