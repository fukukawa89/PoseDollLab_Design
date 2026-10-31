from pathlib import Path
import sys,json
import cadquery as cq
R=Path.cwd();sys.path.insert(0,str(R/'Hardware/PoseDoll44/cad/revO3'));from compact_joint import ring,cyl
sys.path.insert(0,str(R/'Hardware/PoseDoll44/cad/revO6'));from thread_geometry import thread_sweep
from math import sqrt
base=ring(15.6,12.35,-14.8,0).cut(cyl(13.70,-14.81,-6.10));tool=thread_sweep([(13.68,-.24),(14.03,-(.24-.35/sqrt(3))),(14.03,.24-.35/sqrt(3)),(13.68,.24)]).translate((0,0,-1.4))
out=[]
for angle,tol in [(17,None),(45,None),(0,1e-5),(17,1e-5),(0,.001)]:
 t=tool.rotate((0,0,0),(0,0,1),angle);c=base.cut(t,tol=tol);i=base.intersect(t,tol=tol)
 row={'angle':angle,'tol':tol,'base':base.Volume(),'tool':t.Volume(),'cut':c.Volume(),'intersection':i.Volume(),'valid':c.isValid(),'error':base.Volume()-c.Volume()-i.Volume()};out.append(row);print(row,flush=True)
Path('.local/o6_thread_phase_diagnostic.json').write_text(json.dumps(out,indent=2))

