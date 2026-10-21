"""Actual G-code external-contact audit using line-width contact graphs.
Internal solid/infill regions are explicitly excluded from missing-fin classification.
Whole floating bead components are found by graph connectivity, then exact local union.
"""
from pathlib import Path
import sys,json,hashlib,time,numpy as np,shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from shapely.geometry import LineString,Point,box
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
from build_revo22_fins import solid,union
from o22_cross_section_geometry import polygon
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def check(pid,label,root=None):
 st=time.time();p=(root or O)/'candidates'/pid/label;dest=p/'verification/native_external_contacts.json';native=json.loads((p/'verification/local_extrusion.json').read_text());sha=native['project_sha256']
 if dest.exists():
  d=json.loads(dest.read_text())
  if d['project_sha256']==sha and d.get('audit_schema')=='native-external-contact-graph-v2-parent-anchors':return d
 rep,raw,feat,names=extract_detailed(p/'projects'/native['project'],arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);feat=np.asarray(feat);mask=a[:,7]==0;a=a[mask];feat=feat[mask];starts=np.r_[0,np.flatnonzero(np.diff(a[:,6]))+1];ends=np.r_[starts[1:],len(a)];n=np.load(p/'parts'/f'{pid}.npz');it=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];s=union([solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(n[f])]).transform(np.c_[it['rotation_matrix'],it['translation_mm']]);prev=None;islands=[];free=[];checked=0;internal_path_count=0;allpaths=0
 for layer,(lo,hi) in enumerate(zip(starts,ends)):
  cur=a[lo:hi];fts=feat[lo:hi];z=float(np.median(cur[:,5]));lines=shapely.linestrings(np.stack([cur[:,:2],cur[:,3:5]],axis=1));pl=np.r_[0,np.flatnonzero(np.linalg.norm(cur[1:,:2]-cur[:-1,3:5],axis=1)>.005)+1];ph=np.r_[pl[1:],len(cur)];pathids=np.repeat(np.arange(len(pl)),ph-pl);allpaths+=len(pl)
  if prev is not None:
   pz=float(np.median(prev[:,5]));geo=polygon(s.slice(pz-(z-pz)/2)).buffer(.015);shapely.prepare(geo);ptree=shapely.STRtree(prevlines);maxpr=float(prev[:,8].max())/2;pairs=ptree.query(lines,predicate='dwithin',distance=cur[:,8]/2+maxpr+.026);ds=shapely.distance(lines[pairs[0]],prevlines[pairs[1]]);valid=ds<=(cur[pairs[0],8]+prev[pairs[1],8])/2+.025;backed=np.zeros(len(pl),bool);backed[pathids[pairs[0,valid]]]=True;unbacked=np.flatnonzero(~backed[pathids]);edge0=[];edge1=[]
   if len(unbacked):
    tree=shapely.STRtree(lines);pairs=tree.query(lines[unbacked],predicate='dwithin',distance=(cur[unbacked,8]+float(cur[:,8].max()))/2+.00001);src=unbacked[pairs[0]];dst=pairs[1];ds=shapely.distance(lines[src],lines[dst]);valid=ds<=(cur[src,8]+cur[dst,8])/2+1e-6;edge0=pathids[src[valid]];edge1=pathids[dst[valid]]
   _,labels=connected_components(coo_matrix((np.ones(len(edge0)),(edge0,edge1)),shape=(len(pl),len(pl))),directed=False);supported=np.bincount(labels,weights=backed.astype(int))>0;floating=np.flatnonzero(~supported)
   for comp in floating:
    ids=np.flatnonzero(labels[pathids]==comp);shape=shapely.union_all(shapely.buffer(lines[ids],cur[ids,8]/2,quad_segs=6))
    if shape.area<=.05:continue
    prev_ids=ptree.query(shape,predicate='dwithin',distance=maxpr+.026);back=shapely.union_all(shapely.buffer(prevlines[prev_ids],prev[prev_ids,8]/2+.025,quad_segs=6)) if len(prev_ids) else shapely.GeometryCollection()
    if shape.intersection(back).area>=.001:continue
    region=box(*shape.bounds);coverage=region.intersection(geo).area/max(region.area,1e-12);islands.append({'z_mm':z,'area_mm2':float(shape.area),'bounds_mm':list(shape.bounds),'inside_previous_solid_geometry':coverage>.995,'previous_solid_bbox_coverage':coverage})
   for x,y in zip(pl,ph):
    roles=sorted({names[int(v)] for v in fts[x:y]})
    if all(v in ['Sparse infill','Internal sparse infill','Gap infill'] for v in roles):continue
    g=LineString(np.r_[cur[x:x+1,:2],cur[x:y,3:5]]);checked+=1
    if geo.covers(g):internal_path_count+=1;continue
    w=float(np.mean(cur[x:y,8]));ids=ptree.query(g,predicate='dwithin',distance=maxpr+w/2+.011);back=shapely.union_all(shapely.buffer(prevlines[ids],(prev[ids,8]+w)/2+.01,quad_segs=6)) if len(ids) else shapely.GeometryCollection();air=g.difference(back)
    for parent in getattr(air,'geoms',[air]):
     if parent.geom_type!='LineString' or parent.length<.15:continue
     pxy=np.asarray(parent.coords);pa=sum(back.distance(Point(pt))<.003 for pt in [pxy[0],pxy[-1]]);parent_short=parent.length<=(3 if pa==2 else 1);outside=parent.difference(geo)
     for piece in getattr(outside,'geoms',[outside]):
      if piece.geom_type!='LineString' or piece.length<.15:continue
      xy=np.asarray(piece.coords);anchors=sum(back.distance(Point(pt))<.003 for pt in [xy[0],xy[-1]]);free.append({'z_mm':z,'feature':' / '.join(roles),'length_mm':float(piece.length),'anchors':anchors,'xy_mm':xy.tolist(),'bounds_mm':list(piece.bounds),'parent_free_run_length_mm':float(parent.length),'parent_anchors':int(pa),'classification':'critical_external_run' if not parent_short and piece.length>(3 if anchors==2 else 1) else 'short_external_gap'})
  prev=cur;prevlines=lines
  if layer and layer%200==0:print('NATIVE_GRAPH_PROGRESS',pid,label,layer,flush=True)
 critical=[q for q in free if q['classification']=='critical_external_run'];external=[q for q in islands if not q['inside_previous_solid_geometry']];d={'id':pid,'label':label,'audit_schema':'native-external-contact-graph-v2-parent-anchors','project_sha256':sha,'gcode_sha256':rep['gcode_sha256'],'method':'Actual extrusion centerline segments with recorded line widths; preceding-layer overlap and same-layer bead connectivity are computed using a spatial contact graph. Candidate floating components are checked by exact local bead union. External portions are partitioned against the preceding solid geometry before full-width backing assessment; internal infill is reported separately. This is geometric screening, not physical print or strength certification.','review_limits':{'two_ended_external_free_run_mm':3,'unanchored_or_one_ended_external_free_run_mm':1,'minimum_recorded_free_run_mm':.15,'floating_component_area_mm2':.05,'previous_bead_contact_margin_mm':.025},'all_contiguous_paths':allpaths,'checked_non_sparse_paths':checked,'paths_wholly_inside_previous_solid':internal_path_count,'islands':islands,'external_islands':external,'external_island_count':len(external),'external_free_runs':free,'critical_external_runs':critical,'critical_external_count':len(critical),'max_external_free_run_mm':max([q['length_mm'] for q in free],default=0),'native_review_resolved':not external and not critical,'physical_print_tested':False,'elapsed_s':time.time()-st};dest.write_text(json.dumps(d,indent=2));print('NATIVE_GRAPH',pid,label,'islands',len(external),'critical',len(critical),'seconds',round(time.time()-st,1),flush=True);return d
if __name__=='__main__':
 for spec in sys.argv[1:]:check(*spec.split(':'))
