"""Conservative one-generation contact from earlier short, prior-anchored bridges."""
import json,sys,numpy as np,shapely,hashlib
from shapely.geometry import LineString,Point
from search_revo22_f5_orientation268 import O,put
from o22_f3_gcode import extract_paths

def lineparts(g):return[p for p in getattr(g,'geoms',[g])if p.geom_type=='LineString'and p.length>1e-5]
def qualified_path(g,prior):
 # Every gap independently needs two distinct roots on the actual preceding layer.
 back=prior.buffer(-.03);free=lineparts(g.difference(back));rows=[]
 for p in free:
  ends=[Point(p.coords[0]),Point(p.coords[-1])];anchored=all(q.distance(back)<.003 for q in ends)and ends[0].distance(ends[1])>.5
  ok=anchored and p.length<=3.
  if not ok:return False,[]
  rows.append(dict(length_mm=p.length,xy_mm=np.array(p.coords).tolist(),two_distinct_prior_roots=True))
 return bool(rows),rows

def controls():
 from shapely.geometry import box
 pr=shapely.union_all([box(-1,-1,.2,1),box(2.4,-1,3.5,1)])
 good=LineString([[-.3,0],[2.9,0]]);long=LineString([[-.3,0],[4.5,0]]);island=LineString([[.3,0],[2.3,0]])
 assert qualified_path(good,pr)[0];assert not qualified_path(long,pr)[0];assert not qualified_path(island,pr)[0];assert not qualified_path(good,box(-1,-1,.2,1))[0]
 return dict(two_prior_anchors_pass=True,one_anchor_rejected=True,floating_segment_rejected=True,overlong_bridge_rejected=True,no_recursion=True)
def run(pid,label):
 folder=O/'candidates'/pid/label;vp=folder/'verification';report=json.loads((vp/'native_final.json').read_text());native=next((folder/'projects').glob('*.3mf'));_,raw=extract_paths(native,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];lids=np.unique(a[:,6]);records=[];remaining=[]
 for q in report['critical_external_runs']:
  cur=a[abs(a[:,5]-q['z_mm'])<.002];lid=cur[0,6];prev=a[a[:,6]==lids[np.searchsorted(lids,lid)-1]];g=LineString(q['xy_mm']);lines=shapely.linestrings(np.stack([cur[:,:2],cur[:,3:5]],1));ids=np.flatnonzero(shapely.distance(lines,g)<.001);ids=[i for i in ids if lines[i].intersection(g.buffer(.001)).length>.003]
  if not ids:remaining.append(q);continue
  idx=min(ids);starts=np.r_[0,np.flatnonzero(np.linalg.norm(cur[1:,:2]-cur[:-1,3:5],axis=1)>.005)+1];pa=int(starts[starts<=idx][-1]);pw=np.stack([prev[:,:2],prev[:,3:5]],1);pls=shapely.linestrings(pw);ni=shapely.STRtree(pls).query(g.buffer(8),predicate='intersects');prior=shapely.union_all(shapely.buffer(pls[ni],prev[ni,8]/2,quad_segs=8));width=float(cur[ids,8].mean());evidence=[];covers=[]
  for j,st in enumerate(starts):
   en=int(starts[j+1])if j+1<len(starts)else len(cur)
   if en>pa:break
   ar=cur[st:en]
   if np.min(shapely.distance(lines[st:en],g))>width+float(ar[:,8].max()):continue
   path=LineString(np.r_[ar[:1,:2],ar[:,3:5]]);ok,ev=qualified_path(path,prior)
   if ok:
    covers+=list(shapely.buffer(lines[st:en],(ar[:,8]+width)/2-.025,quad_segs=8));evidence.append(dict(start=int(st),end=en,independent_bridge_gaps=ev))
  additional=shapely.union_all(covers);pieces=lineparts(g.difference(additional));rootedprior=shapely.union_all(shapely.buffer(pls[ni],(prev[ni,8]+width)/2+.01,quad_segs=8));allowed=shapely.union_all([rootedprior,additional]);res=[]
  for p in pieces:
   anchors=sum(Point(e).distance(allowed)<.003 for e in[p.coords[0],p.coords[-1]]);limit=3. if anchors==2 else 1.
   if p.length>limit:res.append(dict(q,xy_mm=np.array(p.coords).tolist(),length_mm=p.length,anchors=anchors,bounds_mm=list(p.bounds)))
  if not evidence:res=[q]
  remaining+=res;records.append(dict(run=q,earlier_paths=evidence,residual_critical_count=len(res)))
 out=dict(report,audit_schema='full-bead-v7-independent-earlier-short-bridge',v6_critical_count=len(report['critical_external_runs']),independent_short_bridge_evidence=records,critical_external_runs=remaining,critical_external_count=len(remaining),native_review_resolved=not remaining and not report['external_islands'],bridge_controls=controls(),bridge_proof_scope='Only previously completed paths whose every free gap is at most 3 mm long and anchored at both distinct ends directly in preceding-layer beads qualify. No chain of floating or previously accepted bridges is used. Residual gaps retain 1 mm / 3 mm thresholds.')
 assert hashlib.sha256(native.read_bytes()).hexdigest()==out['project_sha256'];put(vp/'native_v7.json',out);print('BRIDGE_PROOF',pid,label,len(report['critical_external_runs']),'=>',len(remaining),'islands',report['external_island_count'],flush=True);return out
if __name__=='__main__':run(*sys.argv[1:3])
