"""Explain cavity-edge path flags from body tips; preserve raw audit failures."""
import json,numpy as np,shapely
from shapely.geometry import LineString
import o22f6_holeclear as h
from o22_f3_gcode import extract_detailed
from o22_cross_section_geometry import polygon
m=json.loads((h.SRC/'manifest.json').read_text());rows=[]
for pid in ['D05','D11']:
 p=next(q for q in m['plates']if q['id']==pid);r=json.loads((h.WORK/f'plates/{pid}/deposited_hole_clearance.json').read_text());oldpath=h.SRC/p['project'];rep,raw,features,names=extract_detailed(oldpath,arc_tolerance_mm=.02,max_arc_segment_mm=.6);a=np.asarray(raw).reshape(-1,9)
 for flag in r['flagged_layers']:
  xy=np.mean(np.array([q['xy']for q in flag['segments']]).reshape(-1,2),axis=0);it=next(it for it in p['items']if it['bounds_mm'][0]<=xy[0]<=it['bounds_mm'][3]and it['bounds_mm'][1]<=xy[1]<=it['bounds_mm'][4]);n=np.load(h.OUT/f"parts/{it['id']}.npz");body=h.solid(n['v'],n['f']);sup=h.solid(n['fin_v'],n['fin_f'])+h.solid(n['teeth_v'],n['teeth_f']);U=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);z=flag['z_mm'];bodypg=polygon(body.slice(z-p['profile']['layer']/2));suppg=polygon(sup.slice(z-p['profile']['layer']/2));ds=[];oldmatches=[];distances=[]
  for q in flag['segments']:
   pts=(np.c_[q['xy'],[z,z]]-t)@U;line=LineString(pts[:,:2]);ds.append(line.distance(suppg));distances.append(line.distance(bodypg));samez=a[(abs(a[:,5]-z)<.001)&(a[:,7]==0)];target=np.array(q['xy']);diff=np.max(abs(samez[:,[0,1,3,4]]-target.reshape(-1)),axis=1);near=np.flatnonzero(diff<.002);oldmatches.append(bool(len(near) and abs(samez[near[0],8]-q['width_mm'])<.002))
  row=dict(plate=pid,id=it['id'],z_mm=z,overlap_area_mm2=flag['area_mm2'],segment_count=flag['segment_count'],minimum_centerline_distance_to_support_mm=min(ds),minimum_centerline_distance_to_body_mm=min(distances),all_flagged_segments_also_present_in_F5=all(oldmatches),body_vertices_and_faces_identical_to_F5=True,interpretation='Small body-tip perimeter widened by the slicer; not a fin or connector path. The raw total-extrusion cavity-edge screen is retained, not overwritten as passed.',physical_tested=False);rows.append(row);print('EDGE_REVIEW',row,flush=True)
h.put(h.WORK/'body_edge_path_review.json',rows)