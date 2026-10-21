"""Additional G-code evidence: short near-straight bridges and lateral contact to an earlier vertically backed wall.
Never treats an unrooted same-layer chain as support. Retains v1 and v2 reports.
"""
from pathlib import Path
import sys,json,numpy as np,shapely,math
from shapely.geometry import LineString,Point
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_paths
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'

def inspect_run(q,cur,prev):
 g=LineString(q['xy_mm']);lines=shapely.linestrings(np.stack([cur[:,:2],cur[:,3:5]],axis=1));ids=np.flatnonzero(shapely.distance(lines,g)<.001)
 ids=[i for i in ids if lines[i].intersection(g.buffer(.001)).length>.003]
 if not ids:return {'resolved':False,'reason':'No exact extrusion sequence recovered'}
 idx=min(ids);starts=np.r_[0,np.flatnonzero(np.linalg.norm(cur[1:,:2]-cur[:-1,3:5],axis=1)>.005)+1];pa=starts[starts<=idx][-1];ends=starts[starts>idx];pb=ends[0] if len(ends) else len(cur);path=LineString(np.r_[cur[pa:pa+1,:2],cur[pa:pb,3:5]]);width=float(np.mean(cur[ids,8]));plines=shapely.linestrings(np.stack([prev[:,:2],prev[:,3:5]],axis=1));ptree=shapely.STRtree(plines);near=ptree.query(g.buffer(3.),predicate='intersects');previous=shapely.union_all(shapely.buffer(plines[near],prev[near,8]/2,quad_segs=8)) if len(near) else shapely.GeometryCollection();diag=float(np.linalg.norm(np.array(g.bounds)[2:]-np.array(g.bounds)[:2]));chord=float(np.linalg.norm(np.array(g.coords[-1])-g.coords[0]));evidence={'resolved':False,'current_width_mm':width,'path_start_segment_index':int(pa),'spatial_extent_mm':diag,'chord_to_path_length':chord/g.length}
 if q['anchors']==2 and diag<=3. and chord/g.length>=.9 and g.difference(path.buffer(.003)).length<.003:
  a=path.project(Point(g.coords[0]));b=path.project(Point(g.coords[-1]));a,b=min(a,b),max(a,b);prcover=shapely.union_all(shapely.buffer(plines[near],(prev[near,8]+width)/2+.01,quad_segs=8));anchor_lengths=[]
  for center,sign in [(a,-1),(b,1)]:
   length=0.
   for dist in np.arange(.01,.251,.01):
    pos=center+sign*dist
    if pos<0 or pos>path.length or not prcover.covers(path.interpolate(pos)):break
    length=float(dist)
   anchor_lengths.append(length)
  evidence['continuous_backed_length_at_ends_mm']=anchor_lengths
  if min(anchor_lengths)>=.2:evidence.update(resolved=True,classification='near_straight_bridge_spatial_extent_at_most_3mm_with_two_02mm_anchors');return evidence
 # Only earlier entire extrusion paths can qualify. Their centerlines must be inside actual prior-layer bead footprints by 0.03 mm.
 early=np.arange(pa);local=early[shapely.distance(lines[early],g)<width/2+float(cur[:,8].max())/2+.01];covers=[];counts=0;back=previous.buffer(-.03)
 for i in local:
  rooted=lines[i].intersection(back)
  for piece in getattr(rooted,'geoms',[rooted]):
   if piece.geom_type!='LineString' or piece.length<.05:continue
   covers.append(piece.buffer((float(cur[i,8])+width)/2-.025,quad_segs=8));counts+=1
 lateral=shapely.union_all(covers);unbacked=float(g.difference(lateral).length);evidence.update(earlier_vertically_backed_segment_pieces=counts,residual_path_without_earlier_backed_wall_mm=unbacked,lateral_bead_overlap_margin_mm=.025)
 if unbacked<.02:evidence.update(resolved=True,classification='continuous_lateral_overlap_with_earlier_vertically_backed_wall')
 return evidence

def check(pid,label):
 folder=O/'candidates'/pid/label;d=refine(pid,label);rep,raw=extract_paths(folder/'projects'/json.loads((folder/'verification/local_extrusion.json').read_text())['project'],arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];lids=np.unique(a[:,6]);ranges={};zmap={}
 for lid in lids:
  ids=np.flatnonzero(a[:,6]==lid);ranges[lid]=(ids[0],ids[-1]+1);zmap[round(float(np.median(a[ids,5])),3)]=lid
 records=[];pending=[]
 for q in d['critical_external_runs']:
  lid=zmap[round(q['z_mm'],3)];prevlid=lids[np.searchsorted(lids,lid)-1];ev=inspect_run(q,a[slice(*ranges[lid])],a[slice(*ranges[prevlid])]);records.append({'run':q,'evidence':ev})
  if not ev['resolved']:pending.append(q)
 d.update(audit_schema='full-bead-v3-earlier-rooted-wall-and-spatial-bridge',additional_path_evidence=records,critical_external_runs=pending,critical_external_count=len(pending),native_review_resolved=not pending and not d['external_islands'],previous_report='full_bead_contacts_v2.json',additional_scope='An existing <=3 mm compact-bridge criterion is applied to near-straight spatial spans only when each end has >=0.2 mm continuous actual bead backing. Separately, a free path may overlap an earlier same-layer wall by >=0.025 mm, only where that earlier wall centerline has at least 0.03 mm inward margin in the preceding layer bead footprint. This forbids recursive unsupported chains. Both are geometric screens, not load or adhesion calibration.');(folder/'verification/full_bead_contacts_v3.json').write_text(json.dumps(d,indent=2));print('CHRONOLOGICAL',pid,label,'islands',d['external_island_count'],'critical',d['critical_external_count'],'resolved',sum(q['evidence']['resolved'] for q in records),flush=True);return d
if __name__=='__main__':
 for spec in sys.argv[1:]:check(*spec.split(':'))
