"""Check printable layer growth of bed-connected portal fins independently of the part."""
import numpy as np,json,time

def check(fin,design):
 st=time.time();step=float(design.get('required_layer_height_mm',.2));initial=float(design.get('required_initial_layer_height_mm',.2));prev=fin.slice(initial/2);zprev=initial/2;rows=[];worst=0.;starts=[]
 for z in np.arange(initial+step/2,fin.bounding_box()[5]+step/2,step):
  cur=fin.slice(float(z));allowed=prev.offset(float(z-zprev)+.015,circular_segments=12);excess=max(0.,float((cur-allowed).area()));worst=max(worst,excess)
  for c in cur.decompose():
   if c.area()>.02 and (c^prev.offset(.015,circular_segments=12)).area()<.005:starts.append({'z_mm':float(z),'area_mm2':float(c.area()),'bounds':list(c.bounds())})
  if excess>.02:rows.append({'z_mm':float(z),'growth_outside_45_degree_envelope_mm2':excess})
  prev=cur;zprev=float(z)
 portals=[q for q in design['segments']if q.get('bed_connected_portal')]
 def dimension_ok(q):
  normal=q['blade_thickness_mm']>=3.2-1e-6 and q['minimum_base_leg_width_mm']>=3.2-1e-6 and(q['height_mm']<=25 or q['brace_count']>=1)
  wide_braced=q.get('wide_cross_braced_24mm_panel',False) and q['blade_thickness_mm']>=2.4-1e-6 and q['brace_count']>=2 and q.get('cross_brace_depth_mm',0)>=14-1e-6 and q['minimum_base_leg_width_mm']>=max(12,q['height_mm']/5)-1e-6
  low_compact=q.get('low_compact_passage_fin',False) and q['height_mm']<=12 and q['blade_thickness_mm']>=1.6-1e-6 and q['minimum_base_leg_width_mm']>=4-1e-6
  return normal or wide_braced or low_compact
 dimensions=all(dimension_ok(q)for q in portals)
 return {'method':'Every fin-only cross-section, without any body material as backing, must grow by no more than one layer height in XY plus 0.015 mm geometric tolerance. Every material island must overlap the preceding fin slice. All physical fin components separately must start at the bed. Ordinary portal panels are at least 3.2 mm thick. A specifically designated 2.4 mm panel requires two transverse buttresses at least 14 mm deep and every bed leg at least max(12 mm, height/5) wide. A compact passage fin may be 1.6 mm thick only below 12 mm height with a bed leg at least 4 mm wide. Fin-only growth and bed connectivity remain mandatory; this dimensional screen is not a strength simulation.','layer_height_mm':step,'initial_layer_height_mm':initial,'maximum_growth_excess_area_mm2':worst,'growth_violations':rows,'floating_fin_sections':starts,'portal_dimensions_passed':dimensions,'passed':not rows and not starts and dimensions,'elapsed_s':time.time()-st,'physical_strength_tested':False}
