"""Independent deposited-path audit inside eroded, body-subtracted fastener cavities."""
import json,sys,concurrent.futures
import numpy as np,shapely
from o22f6_holeclear import *
from o22_f3_gcode import extract_detailed
from o22_cross_section_geometry import polygon

def check(p):
 pid=p['id'];path=OUT/f'projects/{pid}_O22F6_{PROJECT_SUFFIX}.3mf';guards=[]
 for it in p['items']:
  if globals().get('GUARD_PART_IDS') is not None and it['id'] not in GUARD_PART_IDS:continue
  n=np.load(WORK/f"guards/{it['id']}.npz");s=solid(n['v'],n['f']);guards.append(s.transform(np.c_[np.array(it['rotation_matrix']),np.array(it['translation_mm'])]))
 guard=union(guards);rep,raw,features,names=extract_detailed(path,arc_tolerance_mm=.02,max_arc_segment_mm=.6);a=np.asarray(raw).reshape(-1,9);features=np.asarray(features);flags=[];layers=0;maxarea=0.;totalarea=0.
 assert not np.any(a[:,7]==1),'Generated support paths present'
 a=a[a[:,7]==0];features=features[np.asarray(raw).reshape(-1,9)[:,7]==0]
 for lid in np.unique(a[:,6]):
  ix=np.flatnonzero(a[:,6]==lid);cur=a[ix];z=float(np.median(cur[:,5]));height=p['profile']['initial'] if lid==a[:,6].min() else p['profile']['layer'];pg=polygon(guard.slice(z-height+.0001)).intersection(polygon(guard.slice(z-height/2))).intersection(polygon(guard.slice(z-.0001))).buffer(-.12)
  if pg.is_empty:continue
  layers+=1;lines=shapely.linestrings(np.stack([cur[:,:2],cur[:,3:5]],axis=1));ids=shapely.STRtree(lines).query(pg.buffer(float(cur[:,8].max()/2)),predicate='intersects')
  if not len(ids):continue
  beads=shapely.buffer(lines[ids],cur[ids,8]/2,quad_segs=8);areas=shapely.area(shapely.intersection(beads,pg));bad=ids[areas>.001];area=float(shapely.union_all(shapely.intersection(beads,pg)).area);maxarea=max(maxarea,area);totalarea+=area
  if len(bad):flags.append(dict(z_mm=z,area_mm2=area,segments=[dict(xy=[cur[i,:2].tolist(),cur[i,3:5].tolist()],width_mm=float(cur[i,8]),feature=names[int(features[ix[i]])])for i in bad[:30]],segment_count=len(bad)))
 r=dict(plate=pid,project_sha256=sha(path),cavity_inset_mm=.12,scope='All positive model extrusion swept to its saved bead width against cavity cross-sections common to the layer bottom, middle and top, checked against body-subtracted fastener clearance; 0.12 mm cavity-wall inset excludes boundary discretization and the three-section intersection excludes partial-height cavity shoulders from the core test. This is a digital core-obstruction screen, not a physical sag test.',generated_support_paths=0,layers_checked=layers,max_layer_overlap_mm2=maxarea,sum_layer_overlap_mm2=totalarea,flagged_layers=flags,passed=not flags)
 r['guard_part_ids']=sorted(globals()['GUARD_PART_IDS'])if globals().get('GUARD_PART_IDS')is not None else None
 put(WORK/f'plates/{pid}'/globals().get('REPORT_NAME','deposited_hole_clearance.json'),r);print('HOLE_GCODE',pid,'flagged',len(flags),'max',round(maxarea,5),flush=True);return r
if __name__=='__main__':
 m=json.loads((SRC/'manifest.json').read_text());ps=[p for p in m['plates']if not sys.argv[1:]or p['id']in sys.argv[1:]]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for r in pool.map(check,ps):pass