# O23C human-form structural candidate

The current design replaces free chest/collar spans with connected load-bearing
walls, relocates the collar axes and mounts a compact back case directly on the
chest. The user confirmed that the controller PCB has not been manufactured.
Its 64 x 60 mm double-sided placement keeps all original pad/net assignments.

This is a geometry and electrical-placement review, **not a manufacturing
release**. The PCB is unrouted. The whole-body motion and STL round-trip gates
still have failures. Read `bench/revO23/DESIGN.zh-CN.md` and its linked reports.

## Current sources

- `scripts/layout_revo23_carrier.py`: native KiCad placement, run with KiCad 10
  Python. Reads the final O22 PCB and schematic without changing them.
- `scripts/build_revo23_compact.py`: current shoulder/chest/case construction.
  Reads the pinned B2 geometry snapshot. The source now includes corrected
  lid boss positions and populated-board withdrawal clearance.
- `scripts/build_revo23.py`: common mesh, anatomy and kinematics library. Its
  old whole-body entry point is guarded for the current revision.
- `parameters.json`: scale, wall design values and controller-placement metadata.

The B2 long-support experiment is preserved at
`bench/revO23/history/O23B2_long_support_experiment_20261020/`. Its source hash is
pinned in the compact builder. It is a rejected appearance/clearance experiment.
The earlier B snapshot is also retained.

## Reproduction and checks

Run mechanical scripts with the repository `.venv/Scripts/python.exe`.
Regeneration overwrites the O23 candidate; preserve reviewed snapshots first.

1. Run `layout_revo23_carrier.py` with KiCad's Python.
2. Run `build_revo23_compact.py`.
3. Run `verify_revo23.py --suite quick`.
4. If the current contact report calls for wall relief, run `refine_revo23.py`
   then `repair_revo23.py`, each with `--keys frame/chest frame/clavicle_l
   frame/clavicle_r frame/clavicle_l.protract_frame frame/clavicle_r.protract_frame`.
   Retained interfaces are protected; disconnected functional lands must remain
   reported. Do not delete them just to obtain a connected mesh.
5. Recheck changed geometry. Run `verify_revo23.py --suite full` for the final
   model, plus `check_revo23_compact_access.py` and `loads_revo23.py`.
6. Run `package_revo23.py`, `export_revo23_3mf.py`, `summarize_revo23.py`, and
   `report_revo23_compact.py` after geometry-bound reports are current.
7. Run `present_revo23.py`; run `render_revo23.py` in a separate background
   Blender process. It saves `O23C_assembly.blend` and actual-model views.

`finish_revo23_compact_case.py` patched the first C prototype; do not apply it
after a fresh build with lid_boss_version 2. Old B/B2 fitters do not recreate C.

All final reports and previews identify the assembly SHA-256. Script completion
means a report was written, not that mechanical checks passed. Full checks
include relocated shoulder hardware and all downstream arm objects. Wrist
donor contacts outside the ankle donor's operating range are not excused as
inherited clearance. Explicit M2 self-tapping engagement has a bounded nominal
overlap allowance and still needs physical fit qualification.

## Motion and output scope

Raw channel order, nominal zeros and angle-table limits remain unchanged. Neutral
body frames and main bone-length proportions retain the Quinn reference, except
the intentionally shortened wrist endpoints. Body orientations are checked
numerically. Collar relocation changes shoulder translation during protraction
and elevation; the full old positional trajectory is not preserved. Current
wrist hardware still needs travel qualification and likely further redesign.

Sources generate indexed polygonal solids, not STEP/B-rep. Viewer and Blender
use the same assembly geometry. Part 3MFs preserve the vertex/index data exactly
and have illustrative bed placements; they contain no validated slicing project
or supports. STL welding failures remain explicit. Neither format is released
for batch printing.

The control-board package has native KiCad files, SVG drawings, ERC/DRC reports
and a pad/net equality audit. It has no new Gerber release. Routing, copper
distribution, thermal/electrical tests, wires, assembly, strength and pose
holding remain required.
