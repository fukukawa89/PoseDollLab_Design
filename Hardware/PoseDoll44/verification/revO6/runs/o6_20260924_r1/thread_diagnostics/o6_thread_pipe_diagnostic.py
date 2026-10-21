from pathlib import Path
import sys,json,math
import cadquery as cq
R=Path.cwd();sys.path.insert(0,str(R/'Hardware/PoseDoll44/cad/revO3'))
from compact_joint import *
p=[(9.08,-.2),(9.4,-(.2-.32/math.sqrt(3))),(9.4,.2-.32/math.sqrt(3)),(9.08,.2)]
raw=ring(11,7.7,-11.2,0).cut(cyl(9.10,-11.21,-4));out=[]
for frenet in (True,False):
 z=-11.7;h=7.;path=cq.Wire.makeHelix(.5,h,9.24,center=(0,0,z));profile=cq.Workplane('XZ').polyline([(r,z+dz) for r,dz in p]).close()
 try:
  tool=profile.sweep(path,isFrenet=frenet).val()
  c=raw.cut(tool);i=raw.intersect(tool)
  row={'method':'pipe','frenet':frenet,'tool_volume':tool.Volume(),'valid':tool.isValid(),'cut_valid':c.isValid(),'raw':raw.Volume(),'cut':c.Volume(),'intersection':i.Volume(),'error':raw.Volume()-c.Volume()-i.Volume()}
  if frenet and tool.isValid():cq.exporters.export(tool,'.local/o6_pipe_female.step');cq.exporters.export(c,'.local/o6_pipe_cup.step')
 except Exception as e:row={'method':'pipe','frenet':frenet,'error':str(e)}
 print(row,flush=True);out.append(row)
large=ring(15.6,12.35,-14.8,0).cut(cyl(13.70,-14.81,-6.10));tool=thread_sweep([(13.68,-.24),(14.03,-(.24-.35/math.sqrt(3))),(14.03,.24-.35/math.sqrt(3)),(13.68,.24)]).translate((0,0,-1.4))
c=large.cut(tool);i=large.intersect(tool);row={'method':'O6_L6_current','tool_volume':tool.Volume(),'raw':large.Volume(),'cut':c.Volume(),'intersection':i.Volume(),'error':large.Volume()-c.Volume()-i.Volume()};print(row,flush=True);out.append(row)
Path('.local/o6_thread_pipe_diagnostic.json').write_text(json.dumps(out,indent=2))

