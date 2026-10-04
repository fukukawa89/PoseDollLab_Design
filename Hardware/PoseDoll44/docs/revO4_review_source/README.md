# 使用说明

先读 `REVIEW_O3_AND_O4_STATIC_PLAN.zh-CN.md`，把 `O4_Codex_START.txt` 交给本地 Codex。

`O4_static_contract.json` 是建议需求清单，不是直接可加载的固件配置。
`static_capture_reference.py` 是离线语义参考，不含硬件驱动或 UE 实现。

运行离线参考测试（标准 Python）：

```sh
python -m unittest discover -s tests -p "test_*.py" -v
```

运行局部 CAD 重建（需要 CadQuery/OCP）：

```sh
python tests/audit_backing_clearance.py
```

局部 CAD 只重建前背片所在截面和导槽，不是原工程全关节重建。报告中的0.65°是正向止挡几何空程，不是已测得的整机漂移或编码器误差。

包内结果来自本次实际运行；原仓库141项测试、七角色构建与整套CAD没有在此重新执行。所有新硬件/时间指标仍需实物验证。
