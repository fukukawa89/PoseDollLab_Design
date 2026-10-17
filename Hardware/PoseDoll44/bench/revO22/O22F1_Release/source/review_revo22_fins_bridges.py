import json,numpy as np
from build_revo22_fins import O,solid,md,polygon,shapely
out=[]
for row in json.loads((O/'verification/source_island_review.json').read_text())['parts']:
 n=np.load(O/'parts'/f"{row['id']}.npz");s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f'])
 for q in row['islands']:
  if q['role']!='part':continue
  z=q['z_mid_mm'];bb=q['bounds'];c=s.slice(z)^md.CrossSection.square([bb[2]-bb[0]+.002,bb[3]-bb[1]+.002]).translate([bb[0]-.001,bb[1]-.001]);shape=polygon(c)
  prev=polygon(s.slice(z-.2));fin=polygon(b.slice(z-.2)+b.slice(z-.4)+b.slice(z-.6));backing=shapely.union(prev,fin)
  if shape.is_empty:continue
  xx,yy=np.meshgrid(np.arange(bb[0],bb[2]+.15,.15),np.arange(bb[1],bb[3]+.15,.15));points=shapely.points(xx.ravel(),yy.ravel());points=points[shapely.covers(shape,points)]
  if not len(points):points=np.array([shape.representative_point()])
  dist=shapely.distance(points,backing)
  out.append({'id':row['id'],'first_layer_z_mm':round(z+.1,3),'area_mm2':shape.area,'minimum_xy_gap_to_previous_model_mm':shape.distance(prev) if not prev.is_empty else None,'minimum_xy_gap_to_fin_up_to_0_6mm_below_mm':shape.distance(fin) if not fin.is_empty else None,'sampled_max_xy_gap_to_available_backing_mm':float(dist.max()) if not backing.is_empty else None,'sample_pitch_mm':.15,'bounds_mm':bb})
result={'purpose':'Descriptive geometry review of new source cross-sections. Distances are not physical bridge qualification; interior hole roofs remain bridges. Uses fin sections 0.2/0.4/0.6 mm below the source section and previous-layer source geometry.','regions':out}
(O/'verification/remaining_bridge_geometry.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps([r for r in out if r['area_mm2']>1 and (r['sampled_max_xy_gap_to_available_backing_mm'] or 999)>3],indent=2))