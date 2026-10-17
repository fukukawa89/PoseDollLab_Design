"""Refine native free paths using only earlier walls independently rooted in prior beads.
Each residual free segment retains the same 1 mm unanchored / 3 mm two-anchor screen.
No recursively unrooted chain and no experimental bridge-length relaxation is used.
"""
from pathlib import Path
import sys,json,numpy as np,shapely,concurrent.futures,traceback
from shapely.geometry import LineString
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_paths
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'

def lateral_remainder(q,cur,prev):
 g=LineString(q['xy_mm']);lines=shapely.linestrings(np.stack([cur[:,:2],cur[:,3:5]],axis=1));ids=np.flatnonzero(shapely.distance(lines,g)<.001);ids=[i for i in ids if lines[i].intersection(g.buffer(.001)).length>.003]
 if not ids:return [g],{'resolved':False,'reason':'Exact extrusion sequence not found'}
 idx=min(ids);starts=np.r_[0,np.flatnonzero(np.linalg.norm(cur[1:,:2]-cur[:-1,3:5],axis=1)>.005)+1];pa=int(starts[starts<=idx][-1]);width=float(np.mean(cur[ids,8]));plines=shapely.linestrings(np.stack([prev[:,:2],prev[:,3:5]],axis=1));near=shapely.STRtree(plines).query(g.buffer(3.),predicate='intersects');prior=shapely.union_all(shapely.buffer(plines[near],prev[near,8]/2,quad_segs=8))if len(near)else shapely.GeometryCollection();back=prior.buffer(-.03);early=np.arange(pa);local=early[shapely.distance(lines[early],g)<width/2+float(cur[:,8].max())/2+.01];covers=[]
 for i in local:
  rooted=lines[i].intersection(back)
  for piece in getattr(rooted,'geoms',[rooted]):
   if piece.geom_type=='LineString'and piece.length>=.05:covers.append(piece.buffer((float(cur[i,8])+width)/2-.025,quad_segs=8))
 leftover=g.difference(shapely.union_all(covers));pieces=[p for p in getattr(leftover,'geoms',[leftover])if p.geom_type=='LineString'and p.length>.0001];ev={'path_start_segment_index':pa,'earlier_independently_rooted_pieces':len(covers),'lateral_overlap_margin_mm':.025,'prior_layer_centerline_inset_mm':.03,'residual_free_lengths_mm':[float(p.length)for p in pieces],'residual_xy_mm':[np.asarray(p.coords).tolist()for p in pieces],'original_run_length_mm':float(g.length),'classification':'earlier_vertically_backed_wall_contact'};return pieces,ev

def controls():
 def seg(a,b,z):return [*a,z,*b,z,1,0,.45]
 prev=np.array([seg([0,0],[10,0],.2)]);root=seg([0,.15],[10,.15],.4);later=seg([1,.54],[3,.54],.4);cases=[]
 for name,cur,pre,xy,expected in [('earlier_rooted',[root,later],prev,[[1,.54],[3,.54]],0),('later_rejected',[later,root],prev,[[1,.54],[3,.54]],2),('unrooted_rejected',[root,later],np.array([seg([0,-1],[10,-1],.2)]),[[1,.54],[3,.54]],2),('recursive_chain_rejected',[root,later,seg([1,.93],[3,.93],.4)],prev,[[1,.93],[3,.93]],2),('insufficient_overlap_rejected',[root,seg([1,.59],[3,.59],.4)],prev,[[1,.59],[3,.59]],2)]:
  pieces,e=lateral_remainder({'xy_mm':xy,'anchors':0},np.array(cur),pre);actual=sum(p.length for p in pieces);assert abs(actual-expected)<1e-6,(name,actual,expected);cases.append({'case':name,'expected_residual_mm':expected,'actual_residual_mm':actual})
 for gap,want in [(.9,False),(2.,True)]:
  cu=np.array([seg([0,.15],[4,.15],.4),seg([4+gap,.15],[10,.15],.4),seg([1,.54],[9,.54],.4)]);pieces,e=lateral_remainder({'xy_mm':[[1,.54],[9,.54]],'anchors':0},cu,prev);critical=any(p.length>1 for p in pieces);assert critical==want,(gap,e);cases.append({'case':'partial_contact_gap_'+str(gap),'expected_critical':want,'actual_critical':critical,'residual_mm':e['residual_free_lengths_mm']})
 out={'all_controls_passed':True,'cases':cases,'scope':'Only earlier wall pieces whose centerlines lie 0.03 mm inside actual preceding-layer extrusion count; require 0.025 mm lateral bead overlap. Split residual gaps keep the preexisting 1 mm unanchored threshold.'};(O/'chronological_wall_controls104.json').write_text(json.dumps(out,indent=2));return out

def check(pid,label):
 folder=O/'candidates'/pid/label;d=refine(pid,label);exact=folder/'verification/full_bead_contacts_v4.json'
 if exact.exists():
  e=json.loads(exact.read_text())
  if e['project_sha256']==d['project_sha256']:d=e
 if not d['critical_external_runs']:return d
 _,raw=extract_paths(folder/'projects'/json.loads((folder/'verification/local_extrusion.json').read_text())['project'],arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];lids=np.unique(a[:,6]);ranges={};zm={}
 for lid in lids:
  ids=np.flatnonzero(a[:,6]==lid);ranges[lid]=(ids[0],ids[-1]+1);zm[round(float(np.median(a[ids,5])),3)]=lid
 records=[];critical=[];short=[]
 for q in d['critical_external_runs']:
  lid=zm[round(q['z_mm'],3)];pre=lids[np.searchsorted(lids,lid)-1];pieces,ev=lateral_remainder(q,a[slice(*ranges[lid])],a[slice(*ranges[pre])]);records.append({'run':q,'evidence':ev});g=LineString(q['xy_mm'])
  for p in pieces:
   if p.length<.15:continue
   anchors=q['anchors']if p.equals(g)else 0;row=dict(q,xy_mm=np.asarray(p.coords).tolist(),length_mm=float(p.length),bounds_mm=list(p.bounds),anchors=anchors,prior_length_mm=q['length_mm'],classification='critical_external_run'if p.length>(3 if anchors==2 else 1)else'short_external_gap',lateral_contact_screen_applied=True);(critical if row['classification']=='critical_external_run'else short).append(row)
 d.update(audit_schema='full-bead-v5-earlier-rooted-wall-104',additional_path_evidence=records,critical_external_runs=critical,critical_external_count=len(critical),additional_short_external_gaps=short,native_review_resolved=not critical and not d['external_islands'],validated_control_report='chronological_wall_controls104.json',physical_print_tested=False,additional_scope='Earlier same-layer walls are accepted only where independently backed by actual prior beads. All remaining unbacked pieces keep the unchanged conservative span limits. No unsupported recursive chain or bridge-length extension is permitted.');(folder/'verification/full_bead_contacts_v5.json').write_text(json.dumps(d,indent=2));print('LATERAL104',pid,label,'islands',d['external_island_count'],'critical',len(critical),'short',[q['length_mm']for q in short],flush=True);return d
if __name__=='__main__':
 controls()
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as p:
  for f in concurrent.futures.as_completed([p.submit(check,*s.split(':'))for s in sys.argv[1:]]):
   try:f.result()
   except Exception:traceback.print_exc()
