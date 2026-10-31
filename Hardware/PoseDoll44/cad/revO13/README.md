# O13 reproduction and scope

Use the repository `.venv/Scripts/python.exe -X utf8`. All commands below are relative to the repository root. O11/O12 evidence stays immutable. The added user observation lives under `bench/observations`, rather than changing the sealed historical O12 report.

Core and selected shoulder layout:

```
Hardware/PoseDoll44/cad/revO13/build_printed_core.py
Hardware/PoseDoll44/cad/revO13/build_braked_module.py
Hardware/PoseDoll44/cad/revO13/check_braked_module.py
Hardware/PoseDoll44/cad/revO13/check_stock_assembly.py
Hardware/PoseDoll44/cad/revO13/clavicle_trial.py --candidate -60,38,10
Hardware/PoseDoll44/cad/revO13/check_full_motion.py
```

`assemble_shoulders.py` is a library for `profile`, FK and paths; its inherited standalone staging entrypoint is not part of this pipeline. `continuous_forks.py` is retained for reference, not rerun: the exact O11 C01/C02 arrays and the original fork-only certificate are verified by `check_stock_assembly.py`.

Further experiments and outputs, in order:

```
Hardware/PoseDoll44/cad/revO13/build_compact_hinge.py
Hardware/PoseDoll44/cad/revO13/refine_compact_wrists.py
Hardware/PoseDoll44/cad/revO13/check_unilateral.py
Hardware/PoseDoll44/cad/revO13/back_reservation.py
Hardware/PoseDoll44/cad/revO13/refine_back_reservation.py
Hardware/PoseDoll44/cad/revO13/build_clavicle_carriers.py
Hardware/PoseDoll44/cad/revO13/verify_integrated_arms.py
Hardware/PoseDoll44/cad/revO13/integrated_loads.py
Hardware/PoseDoll44/cad/revO13/update_loads.py
Hardware/PoseDoll44/cad/revO13/export_core_prototype.py
Hardware/PoseDoll44/cad/revO13/test_methods.py
Hardware/PoseDoll44/cad/revO13/fullbody_stage.py
```

The broad arm endpoint audit includes all unlike module-body pairs; the many path samples use the narrower, inherited clavicle/shoulder relevance predicate. Path samples preserve each side's original stored four-angle allocation on a union of time grids; opposite arms can therefore have slightly different fractions. Neither check is continuous full-body acceptance. `Parts` reports a sum of per-piece intersection volumes; this is not necessarily a union volume.

Compact wrist sensor, rotor cup, board, connector and holder solids are reservations, not accepted attachment/electrical designs. The full-body registry retains 44 semantic output slots (41 measured plus 3 fixed); this is not a certification of the raw physical sensor count for a redundant four-angle mechanism. Anatomical body links are not print parts. Outer twist preload, carriers, full electronic/harness integration, physical accuracy and holding behavior remain separate work.

The selected empty rear board box is tested with a 0.5 mm axis-aligned expansion at endpoints. This does not prove that actual populated PCBs fit or that new carriers/torso structures clear it.

Existing source parameters, reports and NPZ files capture the final study. Development patch helpers under `output/o13_development_helpers` are historical editing aids, not a reproducible generation pipeline. Do not rerun those helpers on the final source.
