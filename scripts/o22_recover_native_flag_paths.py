"""Recover exact XY polylines for existing v2 flags, without rescreening every path."""
from pathlib import Path
import sys,json,time
import numpy as np,shapely
from shapely.geometry import LineString,box
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
from build_revo22_fins import md
from o22_cross_section_geometry import polygon
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def recover(pid,label):
 folder=O/'candidates'/pid/label;dest=folder/'verification/native_flag_paths.json'
 rep=json.loads((folder/'verification/local_extrusion.json').read_text())
 if dest.exists():
  d=json.loads(dest.read_text())
  if d['project_sha256']==rep['project_sha256']:return d
 st=time.time();_,raw,feat,names=extract_detailed(folder/'projects'/rep['project'],arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];lids=np.unique(a[:,6]);layers={};zs={}
 for lid in lids:
  ar=a[a[:,6]==lid];layers[lid]=ar;zs[round(float(np.median(ar[:,5])),3)]=lid
 records=[];cache={};prev_cache={}
 for r in rep['unresolved_spans']:
  lid=zs[round(r['z_mm'],3)]
  if lid not in cache:
   cache.clear()
   ar=layers[lid];prev=layers[lids[np.where(lids==lid)[0][0]-1]];xy=np.stack([prev[:,:2],prev[:,3:5]],axis=1);buf=shapely.orient_polygons(shapely.buffer(shapely.linestrings(xy),np.maximum(prev[:,8]/2,.001),quad_segs=3));cs=md.CrossSection([np.round(np.asarray(g.exterior.coords)[:-1],4) for g in buf if not g.is_empty]);back=polygon(cs.offset(.025,circular_segments=12));starts=np.r_[0,np.flatnonzero(np.linalg.norm(ar[1:,:2]-ar[:-1,3:5],axis=1)>.005)+1];ends=np.r_[starts[1:],len(ar)];lines=[LineString(np.vstack([ar[lo,:2],ar[lo:hi,3:5]])) for lo,hi in zip(starts,ends)];shapely.prepare(back);cache[lid]=(lines,shapely.STRtree(lines),back,{})
  lines,tree,back,diffs=cache[lid];bb=np.array(r['bounds_mm']);query=box(bb[0]-.002,bb[1]-.002,bb[2]+.002,bb[3]+.002);best=None
  for idx in tree.query(query):
   if idx not in diffs:
    diffs[idx]=shapely.GeometryCollection() if back.covers(lines[idx]) else lines[idx].difference(back)
   for g in getattr(diffs[idx],'geoms',[diffs[idx]]):
    if g.geom_type!='LineString' or g.length<.249:continue
    cost=float(np.max(abs(np.array(g.bounds)-bb)))+abs(g.length-r['length_mm'])
    if best is None or cost<best[0]:best=(cost,g)
  assert best is not None and best[0]<.001,(pid,label,r,best[0] if best else None)
  records.append(dict(r,xy_mm=np.asarray(best[1].coords).tolist()))
 d={'id':pid,'label':label,'project_sha256':rep['project_sha256'],'records':records,'elapsed_s':time.time()-st};dest.write_text(json.dumps(d,indent=2));print('RECOVERED',pid,label,len(records),round(time.time()-st,1),flush=True);return d
if __name__=='__main__':
 for spec in sys.argv[1:]:recover(*spec.split(':'))
