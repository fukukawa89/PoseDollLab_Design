from pathlib import Path
import sys,json,math
import cadquery as cq
R=Path.cwd();sys.path.insert(0,str(R/'Hardware/PoseDoll44/cad/revO3'))
from compact_joint import *
p=[(9.08,-.2),(9.4,-(.2-.32/math.sqrt(3))),(9.4,.2-.32/math.sqrt(3)),(9.08,.2)]
raw=ring(11,7.7,-11.2,0).cut(cyl(9.10,-11.21,-4))
out=[]
for z,h in [(-11.2,6.6),(-11.7,7.0)]:
 tool=thread_sweep(p,z0=z,height=h,pitch=.5)
 c=raw.cut(tool);i=raw.intersect(tool)
 row={'z':z,'height':h,'tool_volume':tool.Volume(),'tool_valid':tool.isValid(),'tool_solids':len(tool.Solids()),'tool_bounds':bounds(tool),'raw_volume':raw.Volume(),'cut_volume':c.Volume(),'intersection_volume':i.Volume(),'conservation_error':raw.Volume()-c.Volume()-i.Volume()}
 out.append(row);print(row,flush=True)
Path('.local/o6_thread_diagnostic.json').write_text(json.dumps(out,indent=2))

