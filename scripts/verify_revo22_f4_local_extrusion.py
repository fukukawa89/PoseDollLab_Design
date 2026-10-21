"""Local G-code span audit. Both detached and side-connected overhangs are retained."""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np,shapely
from shapely.geometry import LineString,Point,box as box2
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
from build_revo22_fins import md
from o22_cross_section_geometry import polygon

def check(path,dest):
 start=time.time();rep,raw,feature,names=extract_detailed(Path(path),arc_tolerance_mm=.025,max_arc_segment_mm=1.)
 a=np.asarray(raw).reshape(-1,9);feature=np.asarray(feature);mask=a[:,7]==0;a=a[mask];feature=feature[mask];prev=None;records=[];islands=[];checked=0;layers=[]
 print('GCODE_PARSED',Path(path).name,len(a),flush=True)
 for lid in np.unique(a[:,6]):
  mask=a[:,6]==lid;ar=a[mask];feat=feature[mask];z=float(np.median(ar[:,5]));xy=np.stack([ar[:,:2],ar[:,3:5]],axis=1)
  buffers=shapely.orient_polygons(shapely.buffer(shapely.linestrings(xy),np.maximum(ar[:,8]/2,.001),quad_segs=3))
  contours=[np.round(np.asarray(g.exterior.coords)[:-1],4) for g in buffers if not g.is_empty];cs=md.CrossSection(contours)
  if prev is not None:
   backing_cs=prev.offset(.025,circular_segments=12);backing=polygon(backing_cs)
   for g in cs.decompose():
    if g.area()>.05 and (g^backing_cs).area()<.001:islands.append({'z_mm':z,'area_mm2':float(g.area()),'bounds_mm':list(g.bounds())})
   starts=np.r_[0,np.flatnonzero((np.linalg.norm(ar[1:,:2]-ar[:-1,3:5],axis=1)>.005))+1];ends=np.r_[starts[1:],len(ar)];lines=[];metas=[]
   for lo,hi in zip(starts,ends):
    roles=sorted({names[int(x)] for x in feat[lo:hi]});role=' / '.join(roles)
    if all(x in ['Sparse infill','Internal sparse infill','Gap infill'] for x in roles):continue
    line=LineString(np.vstack([ar[lo,:2],ar[lo:hi,3:5]]));lines.append(line);metas.append((role,float(np.mean(ar[lo:hi,8]))))
   checked+=len(lines)
   if lines:
    line_array=np.array(lines,dtype=object);shapely.prepare(backing);not_fully_covered=~shapely.covers(backing,line_array);differences=np.empty(len(lines),dtype=object);differences[:]=shapely.GeometryCollection();differences[not_fully_covered]=shapely.difference(line_array[not_fully_covered],backing)
    for line,geo,meta in zip(lines,differences,metas):
     for g in getattr(geo,'geoms',[geo]):
      if g.geom_type!='LineString' or g.length<=.25:continue
      q=np.asarray(g.coords);length=float(g.length);anchors=sum(backing.distance(Point(p))<.002 for p in [q[0],q[-1]]);chord=float(np.linalg.norm(q[-1]-q[0]));straight=chord/max(length,1e-9)
      # Screening limits only, deliberately more conservative than uncalibrated long bridging.
      sample_distances=np.linspace(0,g.length,max(3,int(np.ceil(g.length/.1))+1));sample_points=shapely.line_interpolate_point(g,sample_distances);max_backing_distance=float(shapely.distance(sample_points,backing).max());classification='unresolved';extent=float(np.linalg.norm(np.array(g.bounds)[2:]-np.array(g.bounds)[:2]))
      if anchors==2 and extent<=3.0:classification='compact_gap_with_both_ends_anchored'
      elif anchors==1 and length<=.5:classification='sub_linewidth_edge_extension'
      records.append({'z_mm':z,'feature':meta[0],'mean_width_mm':meta[1],'length_mm':length,'max_centerline_distance_from_backing_mm':max_backing_distance,'chord_mm':chord,'straightness':straight,'unsupported_footprint_diagonal_mm':extent,'anchors_in_previous_layer':int(anchors),'bounds_mm':list(g.bounds),'classification':classification})
  prev=cs;layers.append({'z_mm':z,'extrusion_segments':len(ar)})
  if len(layers)%150==0:print('SPAN_PROGRESS',Path(path).name,len(layers),flush=True)
 unresolved=[r for r in records if r['classification']=='unresolved']
 result={'audit_schema':'local-extrusion-v2-preserve-nested-islands','project':str(Path(path).name),'project_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'gcode_sha256':rep['gcode_sha256'],'method':'Every geometrically contiguous extrusion path (not split when only the slicer feature label changes); wholly sparse/gap-infill paths are excluded. Each remaining path is clipped against preceding-layer actual bead coverage expanded only 0.025 mm. Thus centerline needs approximately half bead support; side-connected unsupported portions are not ignored. Sparse infill is assessed as internal infill, not removable support. Whole-layer detached bead regions are checked separately.','screening_limits':{'two_ended_unbacked_footprint_diagonal_mm':3.,'one_ended_extension_mm':.5,'record_minimum_span_mm':.25,'detached_bead_region_area_mm2':.05},'limits_are_screening_not_physical_calibration':True,'layer_count':len(layers),'checked_contiguous_paths':checked,'detached_bead_regions':islands,'unresolved_spans':unresolved,'all_recorded_spans':records,'unresolved_count':len(unresolved),'max_unresolved_span_mm':max([x['length_mm'] for x in unresolved],default=0),'elapsed_s':time.time()-start,'print_reliability_certified':False}
 Path(dest).parent.mkdir(parents=True,exist_ok=True);Path(dest).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('NATIVE_LOCAL',Path(path).name,'islands',len(islands),'unresolved',len(unresolved),'max',result['max_unresolved_span_mm'],'s',round(time.time()-start,1),flush=True);return result
if __name__=='__main__':check(sys.argv[1],sys.argv[2])
