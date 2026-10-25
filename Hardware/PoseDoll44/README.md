# PoseDoll Manny / Quinn hardware design

[Repository README](../../README.md) · [O24C-T6 test kit](bench/revO24C_T6/START_HERE.html) · [O24D handoff](docs/HANDOFF_O24D.zh-CN.md)

Latest arm test candidate (2026-10-25): O24C-T6. H, R and the two-axis wrist use captured M3 nylon-insert locknuts, retaining all seven O22 shoulder screws. Reprint H6-01/R6-01/W6-01; C6-01 is a recommended fit coupon. Digital checks pass; the 100-cycle no-retightening target remains physically untested. See the repository README for full revision history and the kit for STL, 3MF, assembly and purchasing details.

Historical Rev N1 context: [entry](START_HERE_REVN.zh-CN.md) · [size review](docs/SIZE_REVIEW_BEFORE_EXTERNAL.zh-CN.md). Rev N1 was based on Rev M full body, with the chest facade removed and left shoulder clearance corrected. Its status below is historical and does not describe T6.

CAD source: `cad/revM/final_model.py` plus `cad/revN/chest_clearance.py`. Historical revisions remain because current code and input provenance refer to them. Use revision manifests rather than mixing standalone exports.

This is a digital prototype candidate, not a manufacturing release or a physically qualified product. See the repository README for the migrated layout, toolchain, ignored local exports, offline checks and viewer startup.
