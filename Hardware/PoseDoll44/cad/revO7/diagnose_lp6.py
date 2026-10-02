from pathlib import Path
import json,sys,cadquery as cq
R=Path.cwd();H=R/'Hardware/PoseDoll44';d=H/'generated/revO7/runs/o7_20260924_r1/LP6_r1'
sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import bounds
m=json.loads((d/'manifest.json').read_text())
for h in m['nominal_intersections']:
 if any(x in h['a']+' '+h['b'] for x in ['preload','pcb_clamp']):
  a=cq.importers.importStep(str(d/(h['a']+'.step'))).val();b=cq.importers.importStep(str(d/(h['b']+'.step'))).val();v=a.intersect(b,tol=1e-5)
  print(h['a'],h['b'],v.Volume(),bounds(v),list(v.Center().toTuple()),flush=True)
