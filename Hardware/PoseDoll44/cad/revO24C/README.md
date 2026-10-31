# O24C compact arm

Read-only inputs: `bench/revO24`, `bench/revO24B`, their CAD modules, and original UE references. All new artifacts go to `bench/revO24C`. A/B fingerprints are checked before export and packaging.

Run from repository root:

```powershell
.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24C/solve_reach.py
.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24C/compact_arm.py
.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24C/validate.py
.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24C/clearance.py
.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24C/design_checks.py
.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24C/adapt_preview.py
.venv/Scripts/python.exe Hardware/PoseDoll44/cad/revO24C/present.py
& 'E:/SteamLibrary/steamapps/common/Blender/blender.exe' --background --python Hardware/PoseDoll44/cad/revO24C/render.py
& 'E:/SteamLibrary/steamapps/common/Blender/blender.exe' --background Hardware/PoseDoll44/bench/revO24C/O24C_compact_arm.blend --python Hardware/PoseDoll44/cad/revO24C/verify_blend.py
```

Then run the real-browser CLI review, `verify_web.py`, and `package.py`. Browser screenshots belong in repository `output/playwright`. No automated script issues a manufacturing release.

Names inherited from A such as `elbow_fork_14` are traceability IDs; dimensions come from `config.json` and actual meshes, not numeric substrings in part names. Units are millimetres. Wrist angles use B's `Rx(deviation) @ Ry(flexion)` order.

`validate.py` reuses A's independently written target FK and all-pair collision routines, injecting only C's output directory, poses and explicit B/C wrist order. It reads the actual exported meshes. Known contacts are not blanket-exempted; only parts on the same rigid frame family are excluded. The standalone clearance gate checks selected non-contact pairs; it is separate from all-pair overlap checks.
