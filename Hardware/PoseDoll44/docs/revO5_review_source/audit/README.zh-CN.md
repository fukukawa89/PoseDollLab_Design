# 审查脚本范围

`source/` 内四个源文件从 GitHub 返回的文本重建，并用 Git blob SHA-1（含 blob 长度头）校验与固定提交一致，具体 identity 和 SHA256 见 source_identity.json。不是完整仓库克隆。

`python run_audit.py` 在 Linux + Python 3.10+ + GCC 环境运行。它不联网、不连接串口、不烧录，不调用 UE/CAD/KiCad。Windows 可由本地 Codex 在隔离目录使用原 MSVC 测试工具链重新编译；本包的 fopen_compat.h 仅为 Linux 执行原 Windows 测试的 fopen_s 兼容层。不得把没有工具时跳过当成通过。

C 编译保留原实现，GCC 只额外关闭一行式源码产生的 misleading-indentation 风格警告。原测试检查CRC、长度、宽时间字段与拒绝重放。test_lost_response.c 专门重现首次请求已接受后，相同编号重试被拒绝。

check_static_window.py 执行原 static_protocol.py，但其 Profile 是合成44槽，strict_json/uint64 是声明的局部辅助 shim；没有运行原完整 Profile/网络/UE。十项测试包括健康窗口、旧ID迟到、故障、boot变化、慢漂移、超时等。

注意：与缺陷相关的测试断言的是旧版本真实行为。它们通过意味着反例被重现，不表示已经修复。移植到O5回归时应改为正确行为断言，并保留本包旧结果作为审查快照。

check_connector_contract.py 只将选用AWG/绝缘外径与已核对的JST目录范围比较。范围相容不等于压接、温升、压降或寿命合格。

results/ 已包含本次真实执行结果。重跑会更新这个目录；需要保留本次原结果时，请先复制整个包到独立运行目录。
