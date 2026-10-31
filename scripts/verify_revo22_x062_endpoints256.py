"""Conservative chronological endpoint proof for residual native free paths."""
from pathlib import Path
import sys,json,numpy as np,shapely,hashlib
from shapely.geometry import LineString,Point
from o22_f3_gcode import extract_paths
from build_revo22_x062_open242 import S,put
import refine_revo22_f4_lateral104 as lateral
label=sys.argv[1];D=S/'candidates/X062'/label;d=json.loads((D/'verification/full_bead_contacts_v5.json').read_text());path=next((D/'projects').glob('*.3mf'));_,raw=extract_paths(path,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];lids=np.unique(a[:,6]);records=[];remaining=[]
lateral.O=S;controls=lateral.controls();assert controls['all_controls_passed']
for q in d['critical_external_runs']:
 cur=a[np.abs(a[:,5]-q['z_mm'])<.002];lid=cur[0,6];prev=a[a[:,6]==lids[np.searchsorted(lids,lid)-1]];g=LineString(q['xy_mm']);lines=shapely.linestrings(np.stack([cur[:,:2],cur[:,3:5]],axis=1));ids=np.flatnonzero(shapely.distance(lines,g)<.001);ids=[i for i in ids if lines[i].intersection(g.buffer(.001)).length>.003];idx=min(ids);starts=np.r_[0,np.flatnonzero(np.linalg.norm(cur[1:,:2]-cur[:-1,3:5],axis=1)>.005)+1];pa=int(starts[starts<=idx][-1]);width=float(np.mean(cur[ids,8]));pl=shapely.linestrings(np.stack([prev[:,:2],prev[:,3:5]],axis=1));near=shapely.STRtree(pl).query(g.buffer(3),predicate='intersects');prior=shapely.union_all(shapely.buffer(pl[near],prev[near,8]/2,quad_segs=8));back=prior.buffer(-.03);early=np.arange(pa);local=early[shapely.distance(lines[early],g)<width/2+float(cur[:,8].max())/2+.01];covers=[];sources=[]
 for i in local:
  rooted=lines[i].intersection(back)
  for p in getattr(rooted,'geoms',[rooted]):
   if p.geom_type=='LineString'and p.length>=.05:
    covers.append(p.buffer((float(cur[i,8])+width)/2-.025,quad_segs=8));sources.append(dict(segment_index=int(i),width_mm=float(cur[i,8]),prior_backed_xy_mm=np.asarray(p.coords).tolist()))
 earlier=shapely.union_all(covers);prior_contact=shapely.union_all(shapely.buffer(pl[near],(prev[near,8]+width)/2+.01,quad_segs=8));cover=shapely.union_all([prior_contact,earlier]);ends=[g.coords[0],g.coords[-1]];dist=[Point(p).distance(cover)for p in ends];anchors=sum(v<.003 for v in dist);accepted=q['length_mm']<=(3. if anchors==2 else 1.)
 records.append(dict(run=q,path_start_segment_index=pa,actual_endpoint_anchors=anchors,endpoint_distance_to_supported_beads_mm=dist,earlier_independently_prior_backed_segments=sources,accepted=accepted,screening_limit_mm=3. if anchors==2 else 1.))
 if not accepted:remaining.append(q)
result=dict(d,audit_schema='full-bead-v6-explicit-residual-endpoints-256',original_v5_critical_count=len(d['critical_external_runs']),endpoint_evidence=records,critical_external_runs=remaining,critical_external_count=len(remaining),native_review_resolved=not remaining and not d['external_islands'],endpoint_method='Re-evaluate the newly created ends of v5 residual runs against actual prior beads and earlier, independently prior-backed wall pieces. The unchanged limits remain 1 mm for zero/one anchor and 3 mm for two anchors. No recursively floating wall chain is accepted.',physical_print_tested=False)
assert hashlib.sha256(path.read_bytes()).hexdigest()==result['project_sha256'];put(D/'verification/native_final.json',result);print('NATIVE_FINAL256',label,result['native_review_resolved'],result['external_island_count'],result['critical_external_count'],[(q['run']['length_mm'],q['actual_endpoint_anchors'])for q in records],flush=True)
