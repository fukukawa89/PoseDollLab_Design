# 使用与复现

双击 `START_HERE.html` 即可阅读手册，`preview/index.html` 可离线查看三维装配，无需 Python、网络或账号。STL / 3MF 的单位是 mm。优先导入带既定摆放和配置的 3MF，首次先打印 P0。

`source` 是仓库 `Hardware/PoseDoll44/cad/revO24C_T1` 的镜像，便于追溯和修改。脚本使用仓库相对路径，重新生成时应放回原目录运行；本 ZIP 不冒充可脱离仓库运行的完整 Python 环境。`source_dependencies` 保存了直接复用的几何和路径审计辅助代码；完整仓库中的 UE 参考模块、O22F7 打印配置模板与已安装的切片器仍是复现依赖。手工打印已有文件不依赖这些脚本。

`test_records` 的测量值留空；重新打包脚本不会覆盖已存在的记录表。填过的记录请另存试件编号备份，避免与之后更新的设计包混淆。
