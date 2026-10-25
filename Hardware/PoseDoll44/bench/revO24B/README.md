# O24B 球面手腕研究包

先打开 [preview/index.html](preview/index.html)：旋转球体、拆解、对比 O24A / B、查看整臂。页面包含本地网格，支持离线直接打开，不依赖 CDN。

- [设计结论、尺寸、验证边界和实物门槛](DESIGN.zh-CN.md)
- [9 组机器人方案调研与一手来源](RESEARCH.zh-CN.md)
- [可编辑 Blender 装配，7 个离散检查姿态](O24B_spherical_wrist.blend)。时间轴跳转查看各姿态；连续运动请用网页，避免对不同关节的世界变换做插值而失真。
- [腕部 GLB](O24B_spherical_wrist.glb) / [整臂 GLB](O24B_hybrid_arm.glb)
- [候选零件表](BOM_candidate.csv)；`stl_layout/` 仅为几何布局，不是可直接打印使用的制造零件。

阶段：`SPHERICAL_WRIST_FEASIBILITY`。B 只更换手腕，保持 A 的肩、肘与前臂。没有完成实物、PCB、固件或 UE 实时测角验证；磁干扰和导向间隙仍是主要风险。O24A 保留。

复建在仓库根目录运行（先安装与 A 相同的 Python 依赖）：

```powershell
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24B/spherical_wrist.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24B/validate.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24B/design_checks.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24B/present.py
# Blender 的实际安装路径可自行替换
blender --background --python Hardware/PoseDoll44/cad/revO24B/render.py
blender --background Hardware/PoseDoll44/bench/revO24B/O24B_spherical_wrist.blend --python Hardware/PoseDoll44/cad/revO24B/verify_blend.py
```

源文件仍依赖仓库既有 O24A 和 UE 参考工具；独立审阅 ZIP 可直接看模型、网页和报告，复建需使用完整仓库。
