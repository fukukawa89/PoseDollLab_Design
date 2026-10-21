"""Audit deposited-bead footprints from real Bambu extrusion moves and widths."""
import json,sys,time,hashlib
import numpy as np
from pathlib import Path
from build_revo22_fins_v3 import O,R,md,solid
from o22_f2_gcode import extract_paths
import shapely
from shapely.geometry import box as box2

def check_project(path,plate,output_dir=None):
 report,raw=extract_paths(path,arc_tolerance_mm=.015,max_arc_segment_mm=.6);height_map={round(float(x['z_mm']),3):float(x['height_mm']) for x in report['layers']};a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];layers={};floaters=[];prev=None
 for lid in np.unique(a[:,6]):
  ar=a[a[:,6]==lid];z=float(np.median(ar[:,5]));xy=np.stack([ar[:,:2],ar[:,3:5]],axis=1);lines=shapely.linestrings(xy);radii=np.maximum(ar[:,8]/2,.0001);buffers=shapely.orient_polygons(shapely.buffer(lines,radii,quad_segs=3))
  contours=[np.round(np.asarray(g.exterior.coords)[:-1],4) for g in buffers if not g.is_empty];cs=md.CrossSection(contours);parts=cs.decompose();entry={'parts':parts,'tree':shapely.STRtree([box2(*g.bounds()) for g in parts]),'inflated':[g.offset(.025,circular_segments=16) for g in parts]};layers[round(z,3)]=entry
  if prev is not None:
   for g in parts:
    if g.area()<=.05:continue
    bb=g.bounds();probe=box2(bb[0]-.026,bb[1]-.026,bb[2]+.026,bb[3]+.026);hits=prev['tree'].query(probe);area=sum((g^prev['inflated'][k]).area() for k in hits)
    if area<.001:floaters.append({'z_mm':z,'area_mm2':g.area(),'bounds_mm':list(bb)})
  prev=entry
 teeth=[];roots=[]
 for it in plate['items']:
  rr=json.loads((O/'design'/f"{it['id']}.json").read_text());M=np.array(it['rotation_matrix']);tr=np.array(it['translation_mm'])
  n=np.load(O/'parts'/f"{it['id']}.npz");tooth_solid=solid(n['teeth_v'],n['teeth_f']).transform(np.c_[M,tr]);tooth_sections={}
  for j,t in enumerate(rr['teeth']):
   bb=t['bounds_mm'];corners=np.array([[x,y,z] for x in [bb[0],bb[3]] for y in [bb[1],bb[4]] for z in [bb[2],bb[5]]])@M.T+tr;lo=corners.min(0);hi=corners.max(0);region=md.CrossSection.square([hi[0]-lo[0],hi[1]-lo[1]]).translate(lo[:2]);window=box2(lo[0],lo[1],hi[0],hi[1]);checks=[]
   for z,entry in layers.items():
    if lo[2]-.001<=z-height_map[z]/2<=hi[2]+.001:
     if z not in tooth_sections:tooth_sections[z]=tooth_solid.slice(z-height_map[z]/2)
     exact=region^tooth_sections[z];section_area=float(exact.area())
     if section_area<1e-6:continue
     hits=entry['tree'].query(window);area=sum((entry['parts'][k]^exact).area() for k in hits);checks.append({'z_mm':z,'tooth_section_mm2':section_area,'printed_overlap_mm2':float(area),'minimum_required_overlap_mm2':min(.02,section_area*.25)})
   missing=[x for x in checks if x['printed_overlap_mm2']<x['minimum_required_overlap_mm2']]
   teeth.append({'object_name':it['object_name'],'tooth':j+1,'layers':checks,'continuous_printed_stack':bool(checks) and not missing})
  n=np.load(O/'parts'/f"{it['id']}.npz")
  if len(n['fin_f']):
   from build_revo22_fins_v3 import polygon
   b=solid(n['fin_v'],n['fin_f']).transform(np.c_[M,tr])
   for j,c in enumerate(b.decompose()):
    region=c.slice(.1);entry=layers[.2];hits=entry['tree'].query(box2(*region.bounds()));area=sum((entry['parts'][k]^region).area() for k in hits);roots.append({'object_name':it['object_name'],'component':j+1,'first_layer_printed_mm2':float(area)})
 result={'project_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tooth_probe':'Actual tooth cross-section intersected with its design bounds at each slice midpoint; not a bounding-box-only test.','footprint_boolean_engine':'Manifold CrossSection / Clipper','numerical_grid_mm':.0001,'project':str(path.name),'deposited_bead_assumptions':'Uses G-code LINE_WIDTH and path centerlines; 2D rounded bead footprint, not actual melt-flow or strength simulation. Arc chord <=0.015 mm; predecessor allowance 0.025 mm.','gcode_out_of_bed_segments':report['out_of_bed_segment_count'],'layer_heights_mm':sorted(set(height_map.values())),'layers':len(layers),'floating_printed_components':floaters,'fin_bed_roots':roots,'teeth':teeth,'teeth_missing_printed_layer':sum(not t['continuous_printed_stack'] for t in teeth)}
 dest=(output_dir or O/'verification')/f"{plate['id']}_extrusion_contacts.json";dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(plate['id'],'floating_printed',len(floaters),'maxarea',max([x['area_mm2'] for x in floaters],default=0),'teeth',len(teeth),'missing',result['teeth_missing_printed_layer'],flush=True)
 return result
if __name__=='__main__':
 for pid in sys.argv[1:]:
  plate=json.loads((R/'.local/o22-fins-v2'/pid/'manifest.json').read_text());check_project(O/'projects'/f'{pid}_O22F2_PLA_fins.3mf',plate)