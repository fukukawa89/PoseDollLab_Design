# PoseDoll 人偶硬件设计

通用静态测姿人偶的独立设计仓库；Manny / Quinn 为软件适配目标。原来位于 `DollSimulation` UE 工程中的硬件、固件与硬件诊断工具已经迁入本目录；UE 插件、角色资产与完整 Python 模拟器留在原项目。

## 当前状态

**O18 已生成结构简化候选：188件/117种打印件，保留46路测量与USB直连。** 相比O17少14件半壳、28枚螺钉和28枚螺母。O17已冻结为 `5a5ac22` / `posedoll-o17-prototype-20260930`。整机既有干涉仍未解决，先验证Q001/Q002关节小样，不能制造放行。

- [O18设计与已知问题](Hardware/PoseDoll44/docs/DESIGN_REVO18.zh-CN.md)
- [O18简化设计包](Hardware/PoseDoll44/bench/revO18/PoseDoll_O18_Universal_Design.zip)
- [O18三维与外壳对照页](Hardware/PoseDoll44/tutorials/full-doll-o18/index.html)：本地服务 `/tutorials/full-doll-o18/index.html`。

### O17已保存基线

**O17简化候选已冻结：202件/124种打印件。** 保留设计包、三维页面、USB固件与验证报告的原始字节。

- [O17设计与已知问题](Hardware/PoseDoll44/docs/DESIGN_REVO17.zh-CN.md)
- [O17设计包](Hardware/PoseDoll44/bench/revO17/PoseDoll_O17_Universal_Design.zip)
- [O17三维页面](Hardware/PoseDoll44/tutorials/full-doll-o17/index.html)

### O16已保存基线

**O16 单一通用测姿人偶设计候选已冻结保存。** 实体型号收敛为一个，数字高度492.14 mm，46路原始测量；保留O15 Quinn机械几何，不再分别生成两种体型。相邻机构不干涉仍是硬要求，连续全域避碰、实物标定与O16双角色UE验收尚未完成。

- [O16完整设计说明](Hardware/PoseDoll44/docs/DESIGN_REVO16.zh-CN.md)
- [O16单人偶设计包](Hardware/PoseDoll44/bench/revO16/PoseDoll_O16_Universal_Design.zip)：一套打印、采购、线束、实体profile与离线测量参考。
- [O16三维查看页](Hardware/PoseDoll44/tutorials/full-doll-o16/index.html)：先运行下方本地服务，再访问 `/tutorials/full-doll-o16/index.html`。
- 复建与核验脚本：`Hardware/PoseDoll44/cad/revO16/`。本轮不含接触修正，不要求目标角色与实体几何重合。

### O15历史基线

**O15完整数字样机保留，等待实物验证。** 480 mm UE 参考、静态摆姿采集；整机无 1.2 kg 硬门槛，允许手托。采用 FDM 打印与现成金属小件，不需要定制机加工金属件。91 cm 方案继续保留为备用。

- [本次提交与审查入口](Hardware/PoseDoll44/docs/REVIEW_HANDOFF_O15.zh-CN.md)：先读此页，再查详细设计、证据和未验证项。
- [O15 详细审查请求](Hardware/PoseDoll44/docs/REVIEW_REQUEST_REVO15.zh-CN.md)；[数字结果汇总](Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1/FINAL_BATCH_SUMMARY.json)。
- [Quinn 统一测试包](Hardware/PoseDoll44/bench/revO15/PoseDoll_O15_Quinn_Prototype.zip) / [Manny 备选包](Hardware/PoseDoll44/bench/revO15/PoseDoll_O15_Manny_Prototype.zip)：只选一套，每套 214 种文件、273 件打印件。
- [中文装配与测试说明](Hardware/PoseDoll44/bench/revO15/guide.html)；[静态采集软件设置](Tools/PoseDollHardwareBridge/README_O15.zh-CN.md)。HTML 请下载打开或通过下方本地服务查看。

本次提交同时收录此前尚未提交的 O5—O14 迭代和 O15 使用的历史依赖。各轮已封存文件保留原字节，旧文档中的“当前”指该轮检查点。O15 的采样几何检查、切片、电路规则、固件构建和 UE 桥接已有数字证据；完整强度、保持力、耐久、带线运动和电子实测仍未完成。

历史入口：[O4](Hardware/PoseDoll44/docs/REVIEW_REQUEST_REVO4.zh-CN.md)、[O3](Hardware/PoseDoll44/docs/START_HERE_REVO3.zh-CN.md)、[O2](Hardware/PoseDoll44/docs/START_HERE_REVO2.zh-CN.md)、[O 初轮](Hardware/PoseDoll44/docs/START_HERE_REVO.zh-CN.md)。不要把历史制造说明与 O15 混用。

以下为备用版的历史基线：

- **机械基线为 Rev N1**：两款分别按 UE 人物参考比例设计，参考身高约 91 cm；胸前大挡板已取消，左肩局部刮碰已修正。
- **下一项为“局部采集 + 外置电源/USB 接口盒”**：方向已确定，新电路板、安装结构和线束尚未实施。
- **小型化仍待比较**：当前尺寸不是已证明的下限，不能直接缩放现有文件，也不能认定重新设计的小型关节必然昂贵。
- 44 个协议槽中，41 轴测量，骨盆 3 轴固定参考；整体位置和全部整体旋转在 UE 调整。
- 当前交付是数字原型候选，尚未实物鉴定。

## 阅读入口

0. [O15历史方案](Hardware/PoseDoll44/docs/REVIEW_HANDOFF_O15.zh-CN.md)。以下 Rev M/N 文档用于备用版。

1. [最新 Rev N1 设计入口](Hardware/PoseDoll44/START_HERE_REVN.zh-CN.md)
2. [胸部修订与设备外置方案](Hardware/PoseDoll44/docs/CHEST_AND_EXTERNAL_REVN.zh-CN.md)
3. [尺寸、磁铁和关节小型化评估](Hardware/PoseDoll44/docs/SIZE_REVIEW_BEFORE_EXTERNAL.zh-CN.md)
4. [制造说明](Hardware/PoseDoll44/docs/FABRICATION_REVM.zh-CN.md)、[装配说明](Hardware/PoseDoll44/docs/ASSEMBLY_REVM.zh-CN.md)、[测试和校准](Hardware/PoseDoll44/docs/BUILD_AND_CALIBRATE_REVM.zh-CN.md)
5. [迁移记录和验证](docs/MIGRATION.zh-CN.md)

Rev M 文档描述原完整基线，使用时应应用 Rev N1 的取消件和左肩修订。更早版本与 `planning/` 是历史依据，不能混作当前制造说明。

## 目录组织

| 路径 | 用途 |
|---|---|
| `Hardware/PoseDoll44/cad/` | 参数化机械模型，保留当前模型仍引用的历史模块 |
| `Hardware/PoseDoll44/electronics/` | 原生 KiCad 工程、符号/封装及板级 STEP 输入 |
| `Hardware/PoseDoll44/mechanical_manifest/` | 轴、接口、比例和网络定义 |
| `Hardware/PoseDoll44/docs/`、`verification/` | 设计说明、数字检查和原型验收依据 |
| `Hardware/PoseDoll44/generated/` | 总装、打印件、查看器、交付清单和本地 CAD 缓存 |
| `Hardware/PoseDoll44/reference/`、`references/` | UE 参考数据及元件资料 |
| `Hardware/PoseDoll44/harness/` | 两款线束与下料表 |
| `Firmware/PoseDollFullBody/` | 六节点完整固件与主机端 C 核心测试 |
| `Firmware/PoseDollHardware/` | 早期单关节固件，历史用途 |
| `Tools/PoseDollHardwareBridge/` | 诊断、校准、数据转换和测试 |
| `Tools/PoseDollSimulator/`、`Shared/` | 硬件需要的协议/运动学代码及配置快照，不含模拟器 GUI |
| `planning/` | 原始规划包副本，父目录中的原下载包也保留 |
| `scripts/` | 独立仓库的检查、构建和查看器入口 |
| `.local/` | 本机迁移清单、运行结果等，不入 Git |

保留 `Hardware/`、`Firmware/`、`Tools/` 层级，以保持已有相对路径及历史资料的可追溯性。协议快照来源与逐文件哈希见 [software_snapshot.json](docs/software_snapshot.json)。

## 环境与离线检查

在本目录打开 PowerShell。本机已经建立独立 `.venv`；新克隆可执行：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/check_repository.py
.\scripts\Build-Design.ps1 -Stage OfflineTests
```

离线检查包括协议配置、Python 测试、C 核心测试和 C/Python 数据帧一致性；不连接硬件或操作 UE。C 测试需要 Visual Studio C 工具链，`-VcVars` 可指定 `vcvars64.bat`。本机迁移后结果为 **81 个 Python 测试、9 个 C 场景通过，数据帧逐字节一致**。

## 打开三维查看器

O15 使用以下命令启动服务，然后访问 `http://127.0.0.1:8769/tutorials/full-doll-o15/index.html`（脚本原来的启动提示仍指向 O14，以此 URL 为准）：

```powershell
python scripts/serve_posedoll_tutorials.py --port 8769
```

提交资料可在新克隆中用 Python 标准库复核：

```powershell
python scripts/verify_o15_review.py
```

以下命令与说明保留为旧版查看器入口：

```powershell
.\scripts\Start-Viewer.ps1
```

默认根据 `verification/revO3/latest.json` 打开 Rev O3 查看器，当前为 `http://127.0.0.1:8874/generated/revO3/runs/o3_20260924_r3/review.html`；通过 `-Revision revN` 打开 91 cm 备用版，仅绑定本机。`-NoBrowser` 只启动服务；端口冲突时可用 `-Port` 指定另一端口，不会自动终止其他进程。

Rev O3 的当前及历史检查运行、HTML、网格、STEP、原生 KiCad 板件、固件产物与原始日志随本次审查提交收录；宿主 C 编译产物通过逐件哈希的 portable ZIP 保存。Rev O 第一轮的 HTML、轻量网格、布局数据及三档关节 STEP 也保留。十份体型布局 STEP 下载需先用 `Build-RevO.ps1 -Stage CAD` 重建。91 cm 备用查看器仍依赖未纳入 Git 的大型网格，需复制旧输出或重建。

## CAD、电路和固件

- CAD：CadQuery 2.7。现有 `Hardware/PoseDoll44/tools/run_cad.py` 可使用本机 CQ-editor 2.7 的环境，需要 CQ-editor 保持开启、Python 版本匹配；也可自行安装常规 CadQuery 环境。
- 电路：KiCad 10，打开 `electronics/` 中对应 `.kicad_pro`。搬迁前已打开的 CQ-editor/KiCad 文件，应从新目录重新打开，避免保存回原路径。
- 固件：ESP-IDF 6.1、ESP32-S3。旧构建缓存已保留，但含旧绝对路径；不要直接在其中增量构建。
- 布线工具：Freerouting 2.4.1 JAR 保留在本机 `Hardware/PoseDoll44/tools/vendor/`，不入 Git；许可证与说明保留。

```powershell
.\scripts\Build-Design.ps1 -Stage CAD
.\scripts\Build-Design.ps1 -Stage Firmware
```

CAD 阶段生成/复核 Rev M 完整基线，耗时较长。Rev N1 的修订脚本位于 `cad/revN/`，依赖 Rev M 完整输出及其复核结果，不是上述命令自动生成的另一套角色。当前源码与必要 CAD 输入纳入 Git。

新构建入口使用本仓库 `.venv`。Firmware 阶段会把检测到旧工程路径的节点缓存移入 `.local/legacy-firmware-builds/` 后重新构建，不删除缓存、不烧录。旧脚本中的 CQ-editor、KiCad、ESP-IDF 安装盘符仍是本机配置；换电脑须配置工具路径，历史工具可参考 `local_toolchain.example.json`。UE 参考重新导出需要原 UE 工程及插件，但导出脚本现在将数据写到本设计仓库。

## Git 与本地成果

Git 收录设计源码、KiCad 工程、固件、必要板级 STEP/角色参考输入、协议快照、说明、交付元数据和检查记录。`.gitattributes` 保留原行尾，避免检出时破坏来源文件的字节哈希。

大型总装 STEP、查看器大网格、CAD 缓存、ESP-IDF 构建目录、Python 环境和第三方工具二进制保留在磁盘，由 `.gitignore` 排除；没有启用 Git LFS。Rev O 审查快照额外收录三档单关节总成 STEP、两个 A 级配合样片 STEP/STL、轻量查看器与本轮原始编译/ERC/DRC 日志，Rev O3 本次另显式收录三个检查运行及其可追溯产物，仍未放开其他版本的整个生成目录。其他机器如需完整本地成果，应另外复制 `Hardware/PoseDoll44/generated/`。**推送 Git 不等于备份全部 6.87 GB 本地成果。**

现有验证报告保留为历史快照，迁移后的路径修复和检查另列记录；没有把迁移当成新一轮全身工程验证。本轮提交由使用者推送到远端；审查应指定 `design/revO-desktop-external` 分支和所读取的完整提交号。
