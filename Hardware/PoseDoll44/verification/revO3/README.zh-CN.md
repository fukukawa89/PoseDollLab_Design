# Rev O3 运行与证据范围

当前设计入口见 [START_HERE_REVO3.zh-CN.md](../../docs/START_HERE_REVO3.zh-CN.md)。正式状态以 [latest.json](latest.json) 和相应运行的 `run.json`、`status.json` 为准。

- `o3_20260924_r1`：七角色实际编译来源。其余整合步骤未完成，不作为最终检查结果。固件复用必须匹配源文件、公共核心、配置、构建脚本、工具摘要与完整产物；来源证明保存于消费运行的 `firmware_origin.json`。
- `o3_20260924_r2`：完成一次整合执行，实际检测到后装磁铁压片/螺钉被一体板托阻挡；`assembly.json` 为 FAIL，V1 为 FAIL_OR_BLOCKED。`PASS_EXECUTION_ONLY` 仅表示各检查器正常执行并锁定证据，绝非机械验收通过。
- `o3_20260924_r3`：改为裸轴预装磁铁组件、再径向合拢轴承盒后的重新整合运行。以该目录最终记录为准；运行未生成 `run.json` 前不得视为完成。

历史失败记录保持原样。更早的 `o3_dev_*` 调试目录已移入仓库忽略目录 `.local/revo3-dev-history`，避免与审查结果混在一起。91 cm 备用和 Rev O2 被审查输出仍在原位置，基线检查核对其哈希。

## 跨机器审查

生成目录中的 STEP、原生 KiCad 文件、HTML、固件等部分扩展名受既有 `.gitignore` 排除；本次提交已按 manifest 显式收录三个检查运行的 STEP、原生板、HTML、固件、日志及相关输入；没有只提交 JSON。构建工具、Python 环境和更早大型备用网格仍需另行准备。

C 宿主测试的原始编译输出位于 `.local/revo3/<run>/host`，因此另有 `portable/<run>_host_proof.zip` 与逐件 SHA-256 清单。该归档保存实际产物，不代表在另一机器执行过测试。仅需恢复证据时，在仓库根目录按 ZIP 内相对路径还原缺失文件，再核对 manifest；不要覆盖已有的不同文件。重新测试使用当前源码与本机可信工具链。

原始 `inputs.json` 的 `base_commit` 记录开发起点；未提交的本轮源码由同文件的 `source_sha256` 锁定。后续提交号应单独记录，不回写已经封存的运行。

本次交付的逐件大小和 SHA-256 见 [review_package.json](review_package.json)。清单覆盖三个运行及宿主归档，不包含自身，也不替代工程验收。原始 ESP-IDF 日志中的控制字符和空白保持原样，以维持封存哈希。
