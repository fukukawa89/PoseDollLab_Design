# O11 reproduction

Run from the design repository using `.venv/Scripts/python.exe -X utf8`.
O10 outputs are immutable; every new generator writes only to O11 paths.

1. `Hardware/PoseDoll44/cad/revO11/build_printed_core.py`
2. `Hardware/PoseDoll44/cad/revO11/build_braked_module.py`
3. `Hardware/PoseDoll44/cad/revO11/check_braked_module.py`
4. `Hardware/PoseDoll44/tools/run_cad.py Hardware/PoseDoll44/cad/revO11/continuous_forks.py`
5. `Hardware/PoseDoll44/cad/revO11/clavicle_trial.py --candidate -60,38,10`
6. `Hardware/PoseDoll44/cad/revO11/update_loads.py`
7. `Hardware/PoseDoll44/cad/revO11/build_printed_bench.py`
8. `Hardware/PoseDoll44/cad/revO11/check_assembly.py`
9. `Hardware/PoseDoll44/cad/revO11/export_print_pack.py`
10. `Hardware/PoseDoll44/cad/revO11/summarize.py`
11. Run the local page smoke check, then `scripts/seal_revo11.py` (or `--verify` for an existing seal).

Optional research steps: `audit_reference.py` reads the provided local ToddlerBot
3MF and the public published BOM. `search_layout.py` compares the 16 recorded
layout candidates before the full chosen-layout check. Their results are not
hardware observations. No ToddlerBot part geometry or G-code is copied.

The inherited O9 mesh core and O7/O8 kinematics remain source dependencies.
`build_finite_twist.py` supplies the revised O11 short printed housing concept.
The copied frame helpers preserve the existing convention; they do not establish
anatomical or full-body acceptance. Retained forearm modules are historical CAD
inputs, not automatically converted or approved by this iteration.

Use a new run directory for later changes after sealing. The printed material,
friction, creep, full torso/carriers/electronics/wiring and one explicit Quinn
pose collision remain unqualified; see the Chinese design report.
