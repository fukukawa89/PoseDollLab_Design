# 当前 O23E 检查

当前几何：`e9bd47cc6a64a2e92148e237acaccf98df93c1a4fdc1f8524e6df6613fbfaa8d`。

| 文件 | 检查内容 |
|---|---|
| geometry.json | 尺寸、封闭性、连通块、打印包络与身体运动学 |
| daily_motion.json | 408 个日常姿态的全部运动相邻实体 |
| edge_paths.json | 114 个加密过渡姿态 |
| fixed_interfaces.json / fixed_all_interfaces.json | 固定装配配合及原有自攻咬合 |
| magnet_seat_restoration.json | 磁铁托座空腔 |
| load_paths.json | 24 个结构件的几何连接截面筛查；非 FEA |
| continuous_walls.json | 最终实体保留原径向外壁及精密安装面的实际差集 |
| backpack_tool_access.json | 细杆工具与控制板取出 |
| export_formats.json | 3MF 索引保留及 STL 回读 |
| gravity_demand.json | 打印实体体积及静态重力估算 |
| delivery_audit.json | 当前模型、预览、渲染、导出的哈希一致性 |

线束几何报告在 `../harness/wire_fixture_verification.json`。髋中心、锁骨机构和右腕商业板报告按其运动学与源模块哈希绑定；其相关模块未在 E 版重新设计。

中间 trial、partial、progress 文件及旧版本报告不能代替当前报告。重新构建时先执行最终候选检查和 `finish_revo23_e.py --publish`，然后进行公开装配校核、`--engineering`、导出、`--notes`、预览渲染及交付审计。不得只修改报告中的几何哈希。
