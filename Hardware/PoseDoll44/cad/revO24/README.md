# O24 — UE 对齐单臂

以实际导出的 Quinn 参考骨架为尺寸源。56 cm 中立站姿参考身高；本目录的参数化源文件与 bench/revO24 下的装配、报告和预览共同构成 O24A 单臂数字设计。

保持 O23I 不变。新设计的打印配合、摩擦保持、线束寿命和实际 UE 输入标定须另行验证。

`tutorial.html`、`tutorial.css`、`tutorial-content.js` 和 `tutorial.js` 是本地动画教程源文件；`present.py` 将它们与原模型打包到 `bench/revO24/preview/`。使用原 124 个实体，不修改 CAD。教学展开路径不代表制造装配路径。

生成预览：从仓库根运行 `.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24/present.py`。浏览器验证脚本为 `tutorial_review.js` 和 `tutorial_portability_review.js`；保存报告后运行 `verify_tutorial.py` 比对原 Python 运动学，再运行 `package.py` 更新审阅包。
