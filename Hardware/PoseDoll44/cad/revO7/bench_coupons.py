"""Coupon specimens only. A calibrated laboratory fixture must hold the ears/plates."""
from pathlib import Path
import json,hashlib,sys,math
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44';O=H/'bench/revO7/coupons';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import ring,cyl,box,bounds
sys.path.insert(0,str(H/'cad/revO6'));from small_joint import spring
rows=[]
for family,ro,ri,t,plate_r,plate_ri,mount_r,hole_r in [('LP6',14,6,.6,17,3.05,15.5,1.1),('M4',7.4,2.6,.4,10,1.55,8.9,.85)]:
 s=ring(ro,ri,0,t)
 for theta in [0,120,240]:s=s.fuse(box(1.6,2,t,(ro+.7,0,t/2)).rotate((0,0,0),(0,0,1),theta))
 plate=ring(plate_r,plate_ri,-3,0)
 for theta in [45,135,225,315]:plate=plate.cut(cyl(hole_r,-3.1,.1).translate((mount_r*math.cos(math.radians(theta)),mount_r*math.sin(math.radians(theta)),0)))
 for role,shape in [('PEEK_coupon',s),('metal_counterface',plate)]:
  p=O/(family+'_'+role+'.step');assert shape.isValid() and len(shape.Solids())==1;cq.exporters.export(shape,str(p));rows.append({'file':p.name,'family':family,'role':role,'contact_radii_mm':[ri,ro],'thickness_mm':t if role=='PEEK_coupon' else 3,'bounds_mm':bounds(shape),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 data={'family':family,'units':'mm','polymer':'Traceable unfilled PEEK first candidate; no catalog friction transfer guarantee','liner_contact_ID_OD_thickness_mm':[2*ri,2*ro,t],'external_ears':{'count':3,'spacing_deg':120,'radial_size_mm':1.6,'tangential_size_mm':2,'center_radius_mm':ro+.7},'counterface_OD_ID_thickness_mm':[2*plate_r,2*plate_ri,3],'fixture_holes':{'count':4,'radius_mm':mount_r,'diameter_mm':2*hole_r,'first_angle_deg':45},'preparation':'Lab/shop to specify actual alloy, finish, flatness and measured thickness before cutting; record those values. Clamp ears outside contact annulus. Measure fixture drag separately. Not a complete fixture drawing.','nominal_geometry_only':True}
 (O/(family+'_dimensions.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
(O/'manifest.json').write_text(json.dumps({'schema':'o7-material-coupon-specimens-v1','parts':rows,'laboratory_fixture_supplied':False,'manufacturing_released':False,'input_sha256':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),H/'cad/revO3/compact_joint.py',H/'cad/revO6/small_joint.py']}},indent=2)+'\n',encoding='utf-8');print('coupon STEP specimens',len(rows))
