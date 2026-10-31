"""Targeted re-audit: actual F01 ceiling and Z=110 extrusion, not a force claim."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np,trimesh,shapely
from shapely.geometry import LineString,Point
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
from verify_revo22_f3_spans import spans
O=R/'Hardware/PoseDoll44/bench/revO22/O22F3_Release'
A=R/'Hardware/PoseDoll44/bench/revO22/F01_F3_audit';A.mkdir(exist_ok=True)
n=np.load(O/'reference/parts/X046.npz');m=trimesh.Trimesh(n['v'],n['f'],process=False)
# Select physical ceiling by its original-source plane, not an arbitrary facet ordinal.
sv=n['source_v'];f=n['f'];st=sv[f];normal=m.face_normals
ix=np.flatnonzero((np.abs(st[:,:,2]-2).max(1)<1e-6)&(st[:,:,0].min(1)>=8-1e-6)&(st[:,:,0].max(1)<=31+1e-6)&(normal[:,2]<-.9))
assert len(ix)>0
tri=m.triangles[ix];normal=normal[ix[0]];area=float(m.area_faces[ix].sum());assert abs(area-2208)<.01
lo=tri.min((0,1));hi=tri.max((0,1));angle=math.degrees(math.acos(-float(normal[2])))
place=next(p for p in json.loads((O/'manifest.json').read_text(encoding='utf8'))['plates'] if p['id']=='F01')['items'][0]
t=np.array(place['translation_mm']);root={'project':'F01_O22F3_PLA_fins.3mf','finding':'Confirmed unsupported internal ceiling; do not print F01 as delivered.','ceiling_original_source_bounds_mm':[st[ix].min((0,1)).tolist(),st[ix].max((0,1)).tolist()],'ceiling_area_mm2':area,'ceiling_height_range_mm':[float(lo[2]),float(hi[2])],'ceiling_inclination_from_horizontal_deg':angle,'maximum_tooth_height_mm':float(n['teeth_v'][:,2].max()),'nominal_layer_advance_mm_at_0p2mm_height':.2/math.tan(math.radians(angle)),'previous_check_failure':'Whole printed components with even small predecessor overlap were not counted as floating; unsupported portions connected to sidewalls were missed. Bed-only support routing silently removed targets obstructed by lower body geometry.','all_fin_contacts_are_insufficient_to_prove_all_part_overhangs_supported':True,'F01_print_recommendation':'withdrawn','physical_collapse_simulated':False}
path=O/'projects/F01_O22F3_PLA_fins.3mf';root['project_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
report,raw,features,names=extract_detailed(path,arc_tolerance_mm=.015,max_arc_segment_mm=.6)
a=np.asarray(raw).reshape(-1,9);features=np.asarray(features);a_mask=a[:,7]==0;a=a[a_mask];features=features[a_mask]
print('Parsed',len(a),'native extrusion segments',flush=True)
z=110.;layers={}
for zz in [z-.2,z]:
 rows=a[np.abs(a[:,5]-zz)<.001];lines=shapely.linestrings(np.stack([rows[:,:2],rows[:,3:5]],axis=1));cover=shapely.union_all(shapely.buffer(lines,rows[:,8]/2,quad_segs=4));layers[round(zz,1)]=(rows,cover)
prev=layers[109.8][1];rows,cur=layers[110.][0:2];feat=features[np.abs(a[:,5]-z)<.001];records=[];start=0;paths=[]
for end in range(1,len(rows)+1):
 boundary=end==len(rows) or feat[end]!=feat[start] or abs(rows[end,8]-rows[start,8])>.025 or np.linalg.norm(rows[end,:2]-rows[end-1,3:5])>.005
 if not boundary:continue
 line=LineString(np.vstack([rows[start,:2],rows[start:end,3:5]]));width=float(rows[start,8]);cover=prev.buffer(width/2+.025,quad_segs=4)
 for s in spans(line,cover,minimum=2):s.update(feature=names[int(feat[start])],line_width_mm=width);records.append(s)
 if names[int(feat[start])] not in ['Sparse infill','Internal sparse infill','Gap infill']:
  diff=line.difference(cover)
  paths.extend([x for x in getattr(diff,'geoms',[diff]) if x.geom_type=='LineString' and x.length>2])
 start=end
root['example_layer_z_mm']=z;root['example_previous_z_mm']=z-.2;root['example_unbacked_spans']=sorted(records,key=lambda x:-x['length_mm']);root['printed_widths_mm']=sorted(set(round(float(x),4) for x in rows[:,8]))
root['example_footprint_note']='True native paths and LINE_WIDTH; anchors are preceding-layer contacts, not melt/force simulation. Same-layer attachment requires separate review.'
# Draw exact layer polygons; crop to upper-box extents only.
from html import escape
x0,y0,x1,y1=cur.bounds;pad=3;x0-=pad;y0-=pad;x1+=pad;y1+=pad;scale=min(1000/(x1-x0),640/(y1-y0));W=1080;H=820
ox=40-x0*scale;oy=735+y0*scale
def xy(p):return (ox+p[0]*scale,oy-p[1]*scale)
def polygon_svg(geom,color,opacity=1):
 out=[]
 for p in getattr(geom,'geoms',[geom]):
  if p.geom_type!='Polygon':continue
  parts=[]
  for ring in [p.exterior,*p.interiors]:
   q=[xy(t) for t in ring.coords];parts.append('M'+' L'.join(f'{a:.3f},{b:.3f}' for a,b in q)+' Z')
  out.append(f'<path d="{" ".join(parts)}" fill="{color}" fill-opacity="{opacity}" fill-rule="evenodd"/>')
 return ''.join(out)
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#fff"/><g font-family="Segoe UI,Microsoft YaHei,sans-serif" fill="#263a40"><text x="35" y="38" font-size="26">F01 胸架：Z = 110.0 mm 的实际出丝</text><text x="35" y="70" font-size="17">灰：前一层 109.8 mm　蓝：当前层　红：缺少前层承托的连续路径（大于 2 mm）</text><text x="35" y="98" font-size="17">这是内腔顶壁；此高度已没有支撑鳍或连接齿。</text></g>'
svg+=polygon_svg(prev,'#c3cbc7')+polygon_svg(cur,'#296f99',.75)
for p in paths:
 q=[xy(t) for t in p.coords];svg+=f'<polyline points="{" ".join(f"{a:.3f},{b:.3f}" for a,b in q)}" fill="none" stroke="#dd2c39" stroke-width="2.5"/>'
svg+='<text x="35" y="790" font-family="Segoe UI,Microsoft YaHei,sans-serif" font-size="15" fill="#455">由交付 3MF 内的 G-code 生成；仅展示几何承托关系，不是材料或受力仿真。</text></svg>'
(A/'F01_ceiling_Z110.svg').write_text(svg,encoding='utf8');(A/'F01_ceiling_audit.json').write_text(json.dumps(root,ensure_ascii=False,indent=2),encoding='utf8')
np.savez_compressed(A/'ceiling_face.npz',v=n['v'],f=n['f'],fin_v=n['fin_v'],fin_f=n['fin_f'],teeth_v=n['teeth_v'],teeth_f=n['teeth_f'],ceiling_faces=ix,source_v=n['source_v'])
print(json.dumps(root,ensure_ascii=False,indent=2),flush=True)
