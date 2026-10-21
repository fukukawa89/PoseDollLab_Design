# O23I 人形承力骨架

当前参数与评审模型为 O23I。版本整理和未完成工作见 [修改记录](../../bench/revO23/CHANGELOG.zh-CN.md)，交付状态见 [设计说明](../../bench/revO23/DESIGN.zh-CN.md)。

当前几何、32 件封闭 STL 与动作检查通过；A1 mini / PLA 打印工程通过 23/32 件，完整新版 3MF 尚未发布。请勿将历史 `README_O23C.md` 中的旧构建流程直接用于当前模型。

主要入口为仓库 `scripts/revo23_unified.py`、`verify_revo23_i.py`、`export_revo23_i.py`、`print_revo23_i.py` 与 `publish_revo23_i_review.py`。源模型依赖 `bench/revO23/history/` 的冻结输入及 `design/` 中的逐零件覆盖文件；使用前需下载 Git LFS 文件。
