"""Resolve half-bead screening flags using full bead footprints, preserving all evidence.
A contact is geometry evidence, not a print/strength certification.
"""
from pathlib import Path
import sys,json,time,hashlib
import numpy as np,shapely
from shapely.geometry import LineString,Point,box
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_paths
from o22_recover_native_flag_paths import recover
from build_revo22_fins import solid,union
from o22_cross_section_geometry import polygon
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def check(pid,label):
 start=time.time();folder=O/'candidates'/pid/label;r=json.loads((folder/'verification/local_extrusion.json').read_text());saved=folder/'verification/full_bead_contacts.json'
 if saved.exists():
  cached=json.loads(saved.read_text())
  if cached.get('project_sha256')==r['project_sha256']:return cached
 paths=recover(pid,label);path=folder/'projects'/r['project'];_,raw=extract_paths(path,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];starts=np.r_[0,np.flatnonzero(np.diff(a[:,6]))+1];ends=np.r_[starts[1:],len(a)];lids=a[starts,6];zmap={};ranges={}
 for lid,lo,hi in zip(lids,starts,ends):
  ar=a[lo:hi];zmap[round(float(np.median(ar[:,5])),3)]=lid;ranges[lid]=(lo,hi)
 n=np.load(folder/'parts'/f'{pid}.npz');it=json.loads((folder/'verification/plate_manifest.json').read_text())['items'][0];whole=union([solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(n[f])]).transform(np.c_[np.array(it['rotation_matrix']),np.array(it['translation_mm'])]);cached_lid=None;free=[];partial=[];internal=[];islands=[]
 def layer(z):
  nonlocal cached_lid,prev,lines,tree,geoprev
  lid=zmap[round(z,3)]
  if lid!=cached_lid:
   index=np.where(lids==lid)[0][0];pr=lids[index-1];prev=a[slice(*ranges[pr])];lines=shapely.linestrings(np.stack([prev[:,:2],prev[:,3:5]],axis=1));tree=shapely.STRtree(lines);pz=float(np.median(prev[:,5]));ppz=0. if index==1 else float(np.median(a[slice(*ranges[lids[index-2]])][:,5]));geoprev=polygon(whole.slice((pz+ppz)/2));cached_lid=lid
 prev=lines=tree=geoprev=None
 for q in paths['records']:
  layer(q['z_mm']);g=LineString(q['xy_mm']);w=q['mean_width_mm'];ids=tree.query(g,predicate='dwithin',distance=(float(prev[:,8].max())+w)/2+.02)
  cover=shapely.union_all(shapely.buffer(lines[ids],(prev[ids,8]+w)/2+.01,quad_segs=6)) if len(ids) else shapely.GeometryCollection();air=g.difference(cover);count=0
  for p in getattr(air,'geoms',[air]):
   if p.geom_type!='LineString' or p.length<.15:continue
   coords=np.array(p.coords);anchors=sum(cover.distance(Point(pt))<.003 for pt in [coords[0],coords[-1]]);inside=geoprev.buffer(.015).covers(p);d={'z_mm':q['z_mm'],'feature':q['feature'],'length_mm':float(p.length),'anchors':int(anchors),'xy_mm':coords.tolist(),'bounds_mm':list(p.bounds),'inside_previous_solid_geometry':bool(inside),'classification':('internal_infill_gap' if inside else 'critical_external_run' if (p.length>(3. if anchors==2 else 1.)) else 'short_external_gap')}
   (internal if inside else free).append(d);count+=1
  if count==0:partial.append({'z_mm':q['z_mm'],'length_mm':q['length_mm'],'max_centerline_distance_mm':q['max_centerline_distance_from_backing_mm'],'width_mm':w,'classification':'has_previous_layer_bead_overlap_along_recorded_path'})
 for q in r['detached_bead_regions']:
  layer(q['z_mm']);region=box(*q['bounds_mm']);coverage=region.intersection(geoprev.buffer(.015)).area/max(region.area,1e-12);islands.append(dict(q,inside_previous_solid_geometry=coverage>.995,previous_solid_bbox_coverage=coverage))
 critical=[q for q in free if q['classification']=='critical_external_run'];external_islands=[q for q in islands if not q['inside_previous_solid_geometry']]
 result={'id':pid,'label':label,'project_sha256':r['project_sha256'],'method':'Full bead contact recheck of all v2 half-bead flags: previous segment centerlines are buffered by (previous_width+current_width)/2 +0.01 mm. This identifies runs whose deposited bead has no overlap with preceding printed material. Paths lying entirely within the previous model solid are separately retained as internal infill gaps, not mislabeled as missing external fins. All original v2 flags remain available.','geometry_tolerance_mm':.01,'review_limits':{'unanchored_or_one_ended_external_free_run_mm':1.,'two_ended_external_free_run_mm':3.,'minimum_recorded_free_run_mm':.15},'limits_are_screening_not_physical_calibration':True,'partial_bead_paths':partial,'external_free_runs':free,'internal_infill_gaps':internal,'islands':islands,'critical_external_runs':critical,'external_islands':external_islands,'critical_external_count':len(critical),'external_island_count':len(external_islands),'max_external_free_run_mm':max([q['length_mm'] for q in free],default=0),'native_review_resolved':not critical and not external_islands,'physical_print_tested':False,'elapsed_s':time.time()-start};(folder/'verification/full_bead_contacts.json').write_text(json.dumps(result,indent=2));print('FULL_BEAD',pid,label,'critical',len(critical),'external_islands',len(external_islands),'max',round(result['max_external_free_run_mm'],3),'internal',len(internal),'s',round(time.time()-start,1),flush=True);return result
if __name__=='__main__':
 for spec in sys.argv[1:]:check(*spec.split(':'))
