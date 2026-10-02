"""Analytic STEP companions for the isolated material experiment."""
import sys,json,hashlib
from pathlib import Path
import cadquery as cq
H=Path(__file__).resolve().parents[2];dest=H/'bench/revO10'
def cyl(r,z,h):return cq.Workplane('XY').workplane(offset=z).circle(r).extrude(h)
def box(x0,y0,z0,x1,y1,z1):return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0,centered=False).translate((x0,y0,z0))
def main():
 base=box(-15,-15,0,15,15,8).cut(cyl(2.2,-.1,8.2))
 for x in (-10,10):base=base.cut(cyl(2.2,-.1,8.2).translate((x,-10,0)))
 lever=cyl(6,8.5,3).union(box(4,-5,8.5,105,5,14.5)).cut(cyl(6,11.5,3.1)).cut(cyl(2.15,8.4,6.2)).cut(cyl(1.5,8.4,6.2).translate((100,0,0)))
 records=[]
 for name,s in [('aluminium_base',base),('PA12_lever',lever)]:
  assert s.val().isValid() and len(s.solids().vals())==1
  path=dest/(name+'.step');cq.exporters.export(s,str(path));back=cq.importers.importStep(str(path));error=abs(back.val().Volume()-s.val().Volume());assert error<1e-6
  records.append({'part':name,'volume_mm3':s.val().Volume(),'roundtrip_volume_error_mm3':error,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 (dest/'step_export.json').write_text(json.dumps({'parts':records,'scope':'Nominal analytic parts for an isolated experiment; finish and purchased stack confirmation still required.'},indent=2)+'\n');print(records)
if __name__=='__main__':main()
