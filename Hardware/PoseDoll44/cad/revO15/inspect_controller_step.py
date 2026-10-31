from pathlib import Path
import cadquery as cq
import json
src=Path(__file__).resolve().parents[2]/'references/revO15/seeed_xiao/controller.step'
s=cq.importers.importStep(str(src)).val();b=s.BoundingBox()
rows=[]
for i,v in enumerate(s.Solids()):
 bb=v.BoundingBox();rows.append({'index':i,'valid':v.isValid(),'volume':v.Volume(),'bounds':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]})
d={'bounds':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax],'solids':rows,'source':str(src)}
src.with_name('step_inspection.json').write_text(json.dumps(d,indent=2),encoding='utf8');print(json.dumps(d,indent=2))
