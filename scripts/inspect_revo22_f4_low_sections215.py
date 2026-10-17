from pathlib import Path
import sys,json,numpy as np,shapely
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,md
from o22_cross_section_geometry import polygon
from o22_f3_gcode import extract_paths
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';p=O/'candidates/W006/stout213_self';n=np.load(p/'parts/W006.npz');d=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(d['rotation_matrix']);off=np.array(d['translation_mm']);shapes=[solid(n[v],n[f])for v,f in[('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]]
audit=json.loads((p/'verification/local_extrusion.json').read_text());_,raw=extract_paths(p/'projects'/audit['project'],arc_tolerance_mm=.025,max_arc_segment_mm=1);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];im=Image.new('RGB',(1500,1050),'white');dr=ImageDraw.Draw(im);colors=['#538abe','#f19133','#dfc532'];scale=55
for j,z in enumerate([3.5,5.9,7.9,9.5,9.7,9.9]):
 col=j%3;row=j//3;ox=col*500+100;oy=row*525+485
 def P(pt):return (ox+pt[0]*scale,oy-(pt[1]-7)*scale)
 def poly(g,c):
  if g.is_empty:return
  if g.geom_type=='Polygon':
   dr.polygon([P(q)for q in g.exterior.coords],fill=c)
   for ring in g.interiors:dr.polygon([P(q)for q in ring.coords],fill='white')
  elif hasattr(g,'geoms'):
   for gg in g.geoms:poly(gg,c)
 for sh,c in zip(shapes,colors):poly(polygon(sh.slice(z)).intersection(shapely.box(-1,7,6.8,15)),c)
 ar=a[abs(a[:,5]-(z+.1))<.002]
 for r in ar:
  ps=(np.array([[*r[:2],z],[*r[3:5],z]])-off)@M
  if np.all((ps[:,0]>-1)&(ps[:,0]<6.8)&(ps[:,1]>7)&(ps[:,1]<15)):dr.line([P(q)for q in ps],fill='#252525',width=1)
 dr.text((col*500+15,row*525+12),f'geometry Z={z:.1f}; toolpaths Z={z+.1:.1f}',fill='black')
 dr.rectangle((col*500,row*525,(col+1)*500-1,(row+1)*525-1),outline='#888888')
im.save(p/'verification/low_sections215.png');print(p/'verification/low_sections215.png')
for z in[9.5,9.7,9.9]:
 for name,sh in zip(['body','fin','teeth'],shapes):
  reg=polygon(sh.slice(z)).intersection(shapely.box(3.1,10.5,4.7,12.5));print(z,name,reg.area,reg.bounds)

