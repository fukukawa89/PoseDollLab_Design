"""Export actual adjacent-layer deposition crops for each flagged original type."""
from pathlib import Path
import sys,json,concurrent.futures,traceback,numpy as np,shapely
from shapely.geometry import box
from html import escape
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';D=O/'review/evidence/layers';D.mkdir(parents=True,exist_ok=True)
def make(args):
 plate,tasks=args
 rep,raw,feat,names=extract_detailed(B/'O22F3_Release/projects'/f'{plate}_O22F3_PLA_fins.3mf',arc_tolerance_mm=.025,max_arc_segment_mm=1.)
 a=np.asarray(raw).reshape(-1,9);feat=np.asarray(feat);mask=a[:,7]==0;a=a[mask];feat=feat[mask];rows=[]
 for pid,q in tasks:
  zz=q['plate_z_mm'];bb=q['plate_bounds_mm'];pad=max(2,min(5,max(bb[2]-bb[0],bb[3]-bb[1])*.15));x0,y0,x1,y1=bb[0]-pad,bb[1]-pad,bb[2]+pad,bb[3]+pad;crop=box(x0,y0,x1,y1)
  covers=[];current=None;selectedfeat=None
  for z in [zz-.2,zz]:
   mask=(abs(a[:,5]-z)<.002)&(np.minimum(a[:,0],a[:,3])<=x1+.5)&(np.maximum(a[:,0],a[:,3])>=x0-.5)&(np.minimum(a[:,1],a[:,4])<=y1+.5)&(np.maximum(a[:,1],a[:,4])>=y0-.5)
   ar=a[mask];lines=shapely.linestrings(np.stack([ar[:,:2],ar[:,3:5]],axis=1));cover=shapely.union_all(shapely.buffer(lines,ar[:,8]/2,quad_segs=4));covers.append(cover.intersection(crop));current=ar;selectedfeat=feat[mask]
  prev,cur=covers;scale=min(970/(x1-x0),590/(y1-y0));ox=50+(970-(x1-x0)*scale)/2-x0*scale;oy=740+y0*scale
  def pathshape(shape,color,alpha=1):
   out=[]
   for p in getattr(shape,'geoms',[shape]):
    if p.geom_type!='Polygon':continue
    paths=[]
    for ring in [p.exterior,*p.interiors]:paths.append('M'+' L'.join(f'{ox+x*scale:.3f},{oy-y*scale:.3f}' for x,y in ring.coords)+' Z')
    out.append(f'<path d="{" ".join(paths)}" fill="{color}" fill-opacity="{alpha}" fill-rule="evenodd"/>')
   return ''.join(out)
  doc=f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="830"><rect width="100%" height="100%" fill="white"/><g font-family="Segoe UI,Microsoft YaHei,sans-serif" fill="#163d46"><text x="40" y="38" font-size="24">{escape(pid)} · {escape(q["object_name"].split(" ")[0])} · Z {zz:.2f} mm</text><text x="40" y="74" font-size="17">灰：前层出丝　蓝：当前出丝　红：缺少前层半线宽承托的路径　虚线：所选标记区</text><text x="40" y="104" font-size="15">由原生 Orca 3MF 的实际 G-code 绘制；此图仅显示几何承托，不是材料变形预测。</text></g>'
  doc+=pathshape(prev,'#b3beb7')+pathshape(cur,'#3d89ae',.72)
  for i,row in enumerate(current):
   if names[int(selectedfeat[i])] in ['Sparse infill','Internal sparse infill','Gap infill']:continue
   line=shapely.LineString([row[:2],row[3:5]]).intersection(crop).difference(prev.buffer(.025,quad_segs=4))
   for p in getattr(line,'geoms',[line]):
    if p.geom_type=='LineString' and p.length>.1:doc+='<polyline points="'+' '.join(f'{ox+x*scale:.3f},{oy-y*scale:.3f}' for x,y in p.coords)+'" fill="none" stroke="#d42737" stroke-width="1.6"/>'
  doc+=f'<rect x="{ox+bb[0]*scale:.3f}" y="{oy-bb[3]*scale:.3f}" width="{max(.1,(bb[2]-bb[0])*scale):.3f}" height="{max(.1,(bb[3]-bb[1])*scale):.3f}" fill="none" stroke="#9f2b42" stroke-dasharray="6 5"/><text x="40" y="800" font-family="Segoe UI,Microsoft YaHei,sans-serif" font-size="14">前层 Z {zz-.2:.2f} mm；层高 0.20 mm；XY 范围 {x0:.2f}…{x1:.2f} / {y0:.2f}…{y1:.2f} mm。</text></svg>'
  (D/f'{pid}.svg').write_text(doc,encoding='utf8');rows.append({'id':pid,'plate':plate,'z_mm':zz,'source_gcode_sha256':rep['gcode_sha256'],'source_project_sha256':q['project_sha256'],'region':q});print('LAYER_CROP',pid,zz,flush=True)
 return rows
if __name__=='__main__':
 manifest=json.loads((B/'O22F3_Release/manifest.json').read_text(encoding='utf8'));best={}
 for p in manifest['plates']:
  if p['optional']:continue
  native=json.loads((O/'audit/native_baseline/Orca'/f"{p['id']}_O22F3_PLA_fins.json").read_text(encoding='utf8'));assert native['audit_schema']=='local-extrusion-v2-preserve-nested-islands'
  for kind,arr in [('island',native['detached_bead_regions']),('span',native['unresolved_spans'])]:
   for q in arr:
    bb=q['bounds_mm'];cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2;it=next(i for i in p['items'] if i['bounds_mm'][0]-.5<=cx<=i['bounds_mm'][3]+.5 and i['bounds_mm'][1]-.5<=cy<=i['bounds_mm'][4]+.5)
    score=q.get('area_mm2',0)*10+q.get('unsupported_footprint_diagonal_mm',0)
    if it['id'] not in best or score>best[it['id']][0]:best[it['id']]=(score,p['id'],dict(q,plate_bounds_mm=bb,plate_z_mm=q['z_mm'],object_name=it['object_name'],project_sha256=native['project_sha256']))
 tasks={}
 for pid,(_,plate,q) in best.items():tasks.setdefault(plate,[]).append((pid,q))
 rows=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for r in pool.map(make,tasks.items()):rows+=r
 (D/'index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print('LAYER_CROPS_COMPLETE',len(rows),flush=True)

