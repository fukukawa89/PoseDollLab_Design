"""Order-aware explanation of prior-layer-only flags; all old flags are retained."""
from pathlib import Path
import sys,json,time,hashlib
import numpy as np,shapely
from shapely.geometry import LineString,Point,box
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
from build_revo22_fins import md,solid,union
from o22_cross_section_geometry import polygon
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def check(pid,label):
 st=time.time();folder=O/'candidates'/pid/label;rep=json.loads((folder/'verification/local_extrusion.json').read_text());path=folder/'projects'/rep['project'];meta,raw,feat,names=extract_detailed(path,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);feat=np.array(feat);keep=a[:,7]==0;a=a[keep];feat=feat[keep];flagz={round(r['z_mm'],3) for r in rep['unresolved_spans']+rep['detached_bead_regions']};n=np.load(folder/'parts'/f'{pid}.npz');it=json.loads((folder/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);whole=union([solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(n[f])]).transform(np.c_[M,t]);prev=None;prev_z=None;out=[]
 for lid in np.unique(a[:,6]):
  mask=a[:,6]==lid;ar=a[mask];ff=feat[mask];z=round(float(np.median(ar[:,5])),4);xy=np.stack([ar[:,:2],ar[:,3:5]],axis=1);buf=shapely.orient_polygons(shapely.buffer(shapely.linestrings(xy),np.maximum(ar[:,8]/2,.001),quad_segs=3));cs=md.CrossSection([np.round(np.asarray(g.exterior.coords)[:-1],4) for g in buf if not g.is_empty])
  if prev is not None and round(z,3) in flagz:
   back=polygon(prev.offset(.025,circular_segments=12));geoprev=polygon(whole.slice(prev_z-(z-prev_z)/2));tree=shapely.STRtree(buf);segline=shapely.linestrings(xy);shapely.prepare(back);valid=shapely.covers(back,segline);starts=np.r_[0,np.flatnonzero(np.linalg.norm(ar[1:,:2]-ar[:-1,3:5],axis=1)>.005)+1];ends=np.r_[starts[1:],len(ar)]
   for lo,hi in zip(starts,ends):
    roles=sorted({names[int(x)] for x in ff[lo:hi]});role=' / '.join(roles);line=LineString(np.vstack([ar[lo,:2],ar[lo:hi,3:5]]));dif=line.difference(back);piece_results=[]
    for g in getattr(dif,'geoms',[dif]):
     if g.geom_type!='LineString' or g.length<=.25:continue
     q=np.asarray(g.coords);anchors_prev=[back.distance(Point(p))<.002 for p in [q[0],q[-1]]];anchors=[];evidence=[]
     for ap,p in zip(anchors_prev,[q[0],q[-1]]):
      ids=tree.query(Point(p),predicate='dwithin',distance=.002);ids=ids[(ids<lo)&valid[ids]];anchors.append(bool(ap or len(ids)));evidence.append([int(i) for i in ids[:6]])
     extent=float(np.linalg.norm(np.array(g.bounds)[2:]-np.array(g.bounds)[:2]));w=float(np.mean(ar[lo:hi,8]));dist=float(np.max(shapely.distance(shapely.line_interpolate_point(g,np.linspace(0,g.length,max(3,int(g.length/.1)+1))),back)));chord=float(np.linalg.norm(q[-1]-q[0]));old='unresolved'
     if sum(anchors_prev)==2 and extent<=3:old='compact_gap'
     elif sum(anchors_prev)==1 and g.length<=.5:old='short_edge'
     classification='unresolved'
     if sum(anchors)==2 and extent<=3:classification='compact_gap_with_existing_anchors'
     elif sum(anchors)>=1 and g.length<=.5:classification='short_anchored_edge'
     elif geoprev.buffer(.015).covers(g) and sum(anchors)==2 and g.length<=6:classification='internal_skin_bridge_over_infill'
     # This stays conservative: adjacent parallel unbacked walls are never counted as vertical support.
     rr={'z_mm':z,'feature':role,'length_mm':g.length,'extent_mm':extent,'max_distance_mm':dist,'width_mm':w,'previous_anchors':int(sum(anchors_prev)),'ordered_anchors':int(sum(anchors)),'prior_printed_anchor_segments':evidence,'inside_previous_solid':bool(geoprev.buffer(.015).covers(g)),'classification':classification,'xy_mm':q.tolist(),'bounds_mm':list(g.bounds),'path_start_segment':int(lo),'path_end_segment':int(hi)};piece_results.append(rr)
     if old=='unresolved' and not all(x in ['Sparse infill','Internal sparse infill','Gap infill'] for x in roles):out.append(rr)
    if all(r['classification']!='unresolved' for r in piece_results):valid[lo:hi]=True
  prev=cs;prev_z=z
 unresolved=[r for r in out if r['classification']=='unresolved'];res={'id':pid,'label':label,'method':'Each v2 candidate path is re-evaluated in extrusion order. End anchors may touch earlier same-layer beads only when those paths were previously backed or satisfied the stated short-gap rule. Earlier parallel floating walls are not treated as vertical support. Prior-layer-only records are preserved separately. Internal skin bridges require exact previous-solid coverage, both anchors, and <=6 mm actual path length.','screening_not_physical_certification':True,'project_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'records':out,'unresolved':unresolved,'unresolved_count':len(unresolved),'original_v2_unresolved':rep['unresolved_count'],'detached_bead_regions':rep['detached_bead_regions'],'elapsed_s':time.time()-st};(folder/'verification/ordered_contacts.json').write_text(json.dumps(res,indent=2));print('ORDERED',pid,label,'unresolved',len(unresolved),'of',rep['unresolved_count'],'islands',len(rep['detached_bead_regions']),round(time.time()-st,1),flush=True);return res
if __name__=='__main__':
 for spec in sys.argv[1:]:check(*spec.split(':'))
