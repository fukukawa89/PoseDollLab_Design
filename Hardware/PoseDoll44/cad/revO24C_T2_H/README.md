# O24C-T2-H

New H-only disc-spring test specimen, created after the user's T1 H holding failure report (2026-10-24). All dimensions are millimetres. It is not a T1 drop-in repair or an O24D release. Preserve all T1 and user test records.

`spring_hinge.py` is the authoritative model. It reuses the existing O22/O12 D4×8 / M3 thread-length-6 shoulder screw and 8×4.2×0.4 disc springs. The three assembly prints are H2-01/02/03. H2-C01 is a separate fitting coupon. The main ordinary M3 nut is captured in a rear carrier; the primary clamp force returns through the metal reaction washer and continuous base web. The nut carrier is deliberately clear of the reaction washer.

Run within this repository using `.venv/Scripts/python.exe -X utf8`:

1. `spring_hinge.py`
2. `verify.py`
3. `print_projects.py`
4. Blender in background with `--python render.py`
5. `publish.py`
6. Serve the generated bench directory on localhost:8778. Run `browser_review.js` through the Playwright CLI and save the raw JSON to `output/playwright/o24ct2h-browser.json`.
7. `verify_delivery.py`
8. `publish.py --package`

Generators import geometry helpers from `cad/revO24C_T1`, `cad/revO24` and the existing A1 mini project writer/template. The copied source folder is a review copy; run generators at their repository locations. STL, editable 3MF, GLB, Blender, HTML, images and CSV records are standalone outputs.

The exact source meshes are used for WebGL and Blender. The thread helices are simplified, disc springs are represented at specified compressed heights, and no load/elastic/friction solver is used. Reported checks cover rigid nominal geometry, insertion paths, tool shanks, contact-chain existence, full nominal nut engagement and offline slicing. There are no measured force, wear, creep or strength results. Do not claim that a captive nut is an independent screw lock. The physical tests explicitly check screw rotation in both movement directions.

Only create an empty measurement CSV if absent; never replace a populated file. Rebuild and recheck viewer hashes after UI changes. No printer jobs or remote actions are sent.
