"""First O8 physical experiment: process/fit gauges, not production bearings."""
import json,hashlib,math
from pathlib import Path
import numpy as np
import cadquery as cq
from reference_assembly import OUT
from extend_forks import stl,topology
from fastened_core import tess

H=Path(__file__).resolve().parents[2];DEST=H/'bench/revO8/fit_gauges'

def main():
 DEST.mkdir(parents=True,exist_ok=True);parts={};dims={}
 gauge=cq.Workplane('XY').box(64,14,6,centered=(True,True,False)).cut(cq.Workplane('XY').box(2,3,8,centered=(True,True,False)).translate((-32,0,-1)))
 for x,d in zip((-24,-12,0,12,24),(4.,4.2,4.4,4.6,4.8)):
  gauge=gauge.cut(cq.Workplane('XY').center(x,0).circle(d/2).extrude(6))
 parts['hole_gauge_Z']=gauge.val();parts['hole_gauge_Y']=gauge.val().rotate((0,0,0),(1,0,0),90).translate((0,6,7))
 dims['hole_gauge_Z']={'holes_from_notch_mm':[4.,4.2,4.4,4.6,4.8],'hole_axis':'Z','hole_length_mm':6,'quantity':1}
 dims['hole_gauge_Y']={**dims['hole_gauge_Z'],'hole_axis':'Y','quantity':1}
 parts['pin_D4']=cq.Workplane('XY').circle(5).extrude(3).faces('>Z').workplane().circle(2).extrude(12).val();dims['pin_D4']={'shaft_diameter_mm':4,'shaft_length_mm':12,'grip_diameter_mm':10,'grip_height_mm':3,'quantity':3}
 g=cq.Workplane('XY').box(54,14,6,centered=(True,True,False)).cut(cq.Workplane('XY').box(2,3,8,centered=(True,True,False)).translate((-27,0,-1)))
 stations=[]
 for x,c in zip((-18,-6,6,18),(0,.2,.4,.6)):
  g=g.cut(cq.Workplane('XY').center(x,0).circle((1.8+c)/2).extrude(6));g=g.cut(cq.Workplane('XY').workplane(offset=5).center(x,0).circle((4+c)/2).extrude(1));g=g.cut(cq.Workplane('XY').center(x,0).polygon(6,(3.3+c)/math.cos(math.pi/6)).extrude(1.4));stations.append({'station_from_notch':len(stations)+1,'through_diameter_mm':1.8+c,'head_pocket_diameter_mm':4+c,'nut_pocket_af_mm':3.3+c})
 parts['fastener_gauge']=g.val();dims['fastener_gauge']={'quantity':1,'stations':stations,'head_pocket_depth_mm':1,'nut_pocket_depth_mm':1.4,'body_thickness_mm':6}
 rows=[];meshes={}
 for name,shape in parts.items():
  assert shape.isValid() and len(shape.Solids())==1,name
  cq.exporters.export(shape,str(DEST/(name+'.step')));t=tess(shape);meshes[name]=t;stl(DEST/(name+'.stl'),t);c=topology(t);assert c['boundary_edges']==0 and c['nonmanifold_edges']==0,name
  # Verify the exported STEP really reopens as one valid solid.
  reopened=cq.importers.importStep(str(DEST/(name+'.step'))).val();assert reopened.isValid() and len(reopened.Solids())==1
  assert abs(reopened.Volume()-shape.Volume())<1e-4
  rows.append({'part':name,**dims[name],'volume_mm3':shape.Volume(),'bounding_box_mm':[shape.BoundingBox().xlen,shape.BoundingBox().ylen,shape.BoundingBox().zlen],'mesh_topology':c,'step_roundtrip_volume_error_mm3':abs(reopened.Volume()-shape.Volume()),'files':{ext:{'path':name+ext,'sha256':hashlib.sha256((DEST/(name+ext)).read_bytes()).hexdigest()} for ext in ('.step','.stl')}})
 np.savez_compressed(DEST/'meshes.npz',**meshes)
 report={'status':'READY_FOR_PROCESS_FIT_EXPERIMENT','parts':rows,'process_candidate':'Unfilled PA12, SLS, same supplier/build batch as any subsequent core. Record actual resin/powder grade, build orientation, finishing and conditioning. Do not substitute FDM or resin silently.','scope':'Gauges characterize coarse printing/fit and nut antirotation. They do not prove ring geometry, friction coefficient, strength, creep or accuracy. Hole and pin manufacturing errors combine.','physical_tested':False,'manufacturing_released':False,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (DEST/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('Valid solid and STEP roundtrip:',len(rows),'files; physical pieces',sum(r['quantity'] for r in rows))
if __name__=='__main__':main()
