import json,sys,numpy as np
sys.path.insert(0,'PoseDoll_HW44_Plan/design/scripts')
import o22f6_holeclear as h
m=json.loads((h.SRC/'manifest.json').read_text());p=next(x for x in m['plates']if x['id']=='D11');flag=json.loads((h.WORK/'plates/D11/deposited_hole_clearance.json').read_text())['flagged_layers'][0];xy=np.mean(np.array([q['xy']for q in flag['segments']]).reshape(-1,2),axis=0);it=next(it for it in p['items']if it['bounds_mm'][0]<=xy[0]<=it['bounds_mm'][3]and it['bounds_mm'][1]<=xy[1]<=it['bounds_mm'][4]);pid=it['id'];xyz=(np.r_[xy,flag['z_mm']]-np.array(it['translation_mm']))@np.array(it['rotation_matrix']);print('PART',pid,'local',xyz,'transform',it)
n=np.load(h.OUT/f'parts/{pid}.npz');g=np.load(h.WORK/f'guards/{pid}.npz');shapes={key:h.solid(n[v],n[f])for key,v,f in [('body','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]};shapes['guard']=h.solid(g['v'],g['f'])
from o22_cross_section_geometry import polygon
from shapely.geometry import box,Point
from PIL import Image,ImageDraw
roi=box(xyz[0]-1.5,xyz[1]-1.5,xyz[0]+1.5,xyz[1]+1.5);im=Image.new('RGB',(1200,450),'white');draw=ImageDraw.Draw(im)
colors={'guard':'#c4e8ff','body':'#a0a0a0','fin':'#ffbb77','teeth':'#ff6969'}
for j,z in enumerate([xyz[2]-.1999,xyz[2]-.1,xyz[2]-.0001]):
 def tr(p):return [(int((x-(xyz[0]-1.5))*120+j*400+20),int(405-(y-(xyz[1]-1.5))*120))for x,y in p]
 for k in ['guard','body','fin','teeth']:
  pg=polygon(shapes[k].slice(z)).intersection(roi);print(k,z,'area',pg.area,'center_inside',pg.contains(Point(xyz[:2])))
  for poly in (pg.geoms if hasattr(pg,'geoms')else[pg]):
   if poly.is_empty or poly.geom_type!='Polygon':continue
   draw.polygon(tr(poly.exterior.coords),fill=colors[k]);
   for ring in poly.interiors:draw.polygon(tr(ring.coords),fill='white')
 for q in flag['segments']:
  loc=(np.c_[q['xy'],[flag['z_mm']]*2]-np.array(it['translation_mm']))@np.array(it['rotation_matrix']);draw.line(tr(loc[:,:2]),fill='black',width=3)
 draw.text((j*400+20,10),f'{pid} z={z:.4f} mm',fill='black');draw.text((j*400+20,430),'grey=body orange=fin red=tooth blue=guard',fill='black')
path=h.WORK/'P002_hole_path_inspection.png';im.save(path);print(path)
d=json.loads((h.SRC/f'design/{pid}.json').read_text());print('KEYS',list(d));print('BODYCHANGES',{k:v for k,v in d.items()if any(x in k for x in ['body','chamfer','repair','ramp','tilt'])})