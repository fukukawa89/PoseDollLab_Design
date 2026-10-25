# O24C-T1 joint test kit

Current revision: **O24C-T1-S3**. Since S2, only W06/W07 STL changed: inward-open liner pockets remove an assembly obstruction. BOM, the other 24 base prints and all 12 fit options are unchanged. The 188-step offline tutorial covers all 133 assembly components. H/R preload bolt insertion now precedes floating-plate installation, with a verified small tilt past the braces.

Tutorial edition **2026-10-23, hardware face directions** requires no new prints. `tutorial_orientation.py` supplies 73 physical face directions (35 nuts, 38 washers) and pairs 29 screws with the required nut type. Blue marks the nylon exit ring; green marks a washer's smooth face. These are visual annotations on the unchanged CAD envelopes, not material or procurement colour requirements. Ordinary nuts are explicitly labelled as having no nylon insert. Wrist guide washers are metal-to-metal and have no mandatory front/back. Step numbers remain H64 / R64 / W60.

Previous S2 repair: Reprint H04/H05/R04/R05 only: continuous fixed-plate webs and wider shaft-clamp nut bosses with verified corner-clear lateral insertion. All other 22 base STLs, 12 fit options and the BOM are unchanged from S1. The wrist retains the S1 interface. D2.5 x 6 / M2 stock shoulder screw from the user image; six changed wrist prints and two added 5 x 2.2 x 0.5 steel washers. The original D3 vendor-specific part is no longer the purchasing target.

Source of the printable bench specimens in `Hardware/PoseDoll44/bench/revO24C_T1`.
The C arm files are read-only reference inputs. No printer or remote service is contacted.

Run from repository root with the existing Python environment:

```powershell
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/kit.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/connection_checks.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/validate.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/printing.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/assembly_checks.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/stock_guide_checks.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/hardware_alternatives.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/procurement_delta.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/guide_drawing.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/present.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/tutorial.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/tutorial_checks.py
& 'E:\SteamLibrary\steamapps\common\Blender\blender.exe' --background --python Hardware/PoseDoll44/cad/revO24C_T1/render.py
& .\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/package.py --prepare
# Refresh the Playwright browser audit described below before packaging.
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/verify_delivery.py
.\.venv\Scripts\python.exe Hardware/PoseDoll44/cad/revO24C_T1/package.py
```

Dependencies: numpy, scipy, trimesh, manifold3d; repository helper `cad/revO24/arm.py` (pure geometry helpers; its main is not run), and `scripts/verify_revo22_a1mini.py` for all-layer path bounds. The slicer resolves the existing O22F7 A1 mini template and uses locally installed OrcaSlicer. Diagnostic sliced output stays in `output/o24ct1-slicing`, outside the delivered ZIP.

Browser QA uses the Playwright CLI against a local server rooted at the generated bench folder on port 8777. Run `browser_review.js` via the CLI `run-code --filename ... --raw` and save its JSON to `output/playwright/o24ct1-browser.json`; inspect the screenshots there. The audit exercises UI ranges, exploded view, individual parts, local links, mobile width and offline opening, then independently compares its transforms with Python. `verify_delivery.py` also checks public HTML links (source templates excluded), CSV row widths, BOM counts, GLB metre scale and the unchanged C baseline.

`kit.py` is the authoritative geometry. Bearing allowance and liner radius are explicit parameters. STL exports already have the intended build orientation, in mm. Thread helices, bearing balls and elastic deformation are not simulated. Nominal body intersections are checked, including fasteners; mechanical contact at zero volume is permitted. Fixed vs moving pairs are checked over 981 poses, not merely by approximate spheres.

Physical quality is not inferred from closed meshes or slicer success. Manufacturing fit, torque, assembly tooling, PLA creep and wear remain measurements to be made using the included test plan.

S2 adds `connection_checks.py`: all 38 exported STLs receive a core/feature review; exact web and roof probes reject the old S1 defects. Intentional thin liners are reviewed separately. The geometry screen is not a physical stiffness or strength claim. `REPRINT_S2_1.3mf` contains just the four changed parts; it is an additional replacement plate, not additional assembly parts. Preserve user measurement CSVs.

The tutorial browser audit is `tutorial_browser_review.js`; save CLI raw JSON as `output/playwright/o24ct1-tutorial-browser.json`, then run `verify_tutorial_browser.py`. `s3_checks.py` uses preserved S2 files under `output/o24ct1-assembly-tutorial` for the regression; its published result and hashes are in verification. `s3_update_prints.py` only rebuilds/slices P3 and the new S3 repair plate, retaining valid audits for byte-identical other projects.

For tutorial-only maintenance, regenerate with `tutorial.py`, run `orientation_checks.py` and both `tutorial_checks.py` / `tutorial_checks.py --stock-washers`, then refresh the tutorial browser audit. `orientation_checks.py` identifies each locknut's exit from the actual screw head/tip diameters and probes the washer/plain-nut contact face against the named CAD mate. The browser audit checks rendered blue/green pixels and the opposite face for all 73 parts, plus face markers following tilted assembly paths. It binds all UI asset hashes. `package.py --prepare`, `verify_delivery.py`, `verify_tutorial_browser.py`, and `package.py` update the pages and offline package. Do not rerun geometry or slicer generation for annotation-only changes; preserve existing manufacturing files and user measurements.
