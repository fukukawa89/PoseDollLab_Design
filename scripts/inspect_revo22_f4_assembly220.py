from pathlib import Path
import sys,json,numpy as np,shapely
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,box,project_xz,slab
from o22_cross_section_geometry import polygon
from repair_revo22_f4_guarded_chamfer import context
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';p=O/'candidates/W006/gap212_self';n=np.load(p/'parts/W006.npz');d=json.loads((p/'design/W006.json').read_text());s=solid(n['v'],n['f']);parts,key,T=context(d,'W006');region=box([-7,5,0],[19,18,22]);near=[]
for k,part in parts.items():
 if k==key:continue
 m=part.transform(T[:3,:]);cut=m^region
 if cut.volume()>.01:near.append((k,cut));print(k,cut.volume(),cut.bounding_box(),flush=True)
im=Image.new('RGB',(1500,1000),'white');dr=ImageDraw.Draw(im);colors=['#d64053','#926aba','#51a984','#b68041','#dd789b','#4e5866']
for j,y in enumerate([10.,11.5,13.]):
 ox=j*500+135;oy=800;scale=25
 def P(q):return ox+q[0]*scale,oy-q[1]*scale
 def poly(g,c):
  if g.is_empty:return
  if g.geom_type=='Polygon':
   dr.polygon([P(q)for q in g.exterior.coords],fill=c)
   for r in g.interiors:dr.polygon([P(q)for q in r.coords],fill='white')
  elif hasattr(g,'geoms'):
   for a in g.geoms:poly(a,c)
 local=s^region;poly(polygon(project_xz(slab(local,y-.02,y+.02,np.array(local.bounding_box())))), '#69a2ca')
 for i,(k,m)in enumerate(near):
  if m.is_empty():continue
  poly(polygon(project_xz(slab(m,y-.02,y+.02,np.array(m.bounding_box())))),colors[i%len(colors)])
 dr.text((j*500+12,15),f'W006 assembly X-Z slice; Y={y}',fill='black');dr.ellipse([P([3.9-.12,9.9+.12]),P([3.9+.12,9.9-.12])],fill='yellow');dr.line([P([-5,0]),P([14,0])],fill='black',width=2)
 for i,(k,m)in enumerate(near):dr.text((j*500+8,835+i*20),k,fill=colors[i%len(colors)])
im.save(p/'verification/assembly_sections220.png');print(p/'verification/assembly_sections220.png',flush=True)
