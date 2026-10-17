from pathlib import Path
import sys,json,numpy as np,shapely
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
from refine_revo22_f4_full_bead import refine
from build_revo22_fins import solid,union
from o22_cross_section_geometry import polygon
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
pid,label=sys.argv[1:3];p=O/'candidates'/pid/label;aq=p/'verification/full_bead_contacts_v5.json';aq=aq if aq.exists()else p/'verification/full_bead_contacts_v2.json';q=json.loads(aq.read_text());proj=p/'projects'/json.loads((p/'verification/local_extrusion.json').read_text())['project'];rep,raw,features,names=extract_detailed(proj,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);mask=a[:,7]==0;features=np.asarray(features)[mask];a=a[mask];zs=np.unique(a[:,5]);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
for i,flag in enumerate(q['external_islands']+q['critical_external_runs']):
 if i>6:break
 b=flag['bounds_mm'];z=flag['z_mm'];prev=zs[zs<z-.01][-1];bb=[b[0]-2,b[1]-2,b[2]+2,b[3]+2];scale=min(760/(bb[2]-bb[0]),690/(bb[3]-bb[1]));im=Image.new('RGB',(900,800),'white');dr=ImageDraw.Draw(im)
 def xy(q):return (50+(q[0]-bb[0])*scale,750-(q[1]-bb[1])*scale)
 for zz,color,outline in [(prev,'#adb9b7','#808c89'),(z,'#74bee5','#24648a')]:
  ar=a[abs(a[:,5]-zz)<.002];idx=np.where((abs(a[:,5]-zz)<.002)&(np.minimum(a[:,0],a[:,3])<bb[2]+.5)&(np.maximum(a[:,0],a[:,3])>bb[0]-.5)&(np.minimum(a[:,1],a[:,4])<bb[3]+.5)&(np.maximum(a[:,1],a[:,4])>bb[1]-.5))[0]
  for j in idx:
   row=a[j];s=shapely.LineString([row[:2],row[3:5]]).buffer(float(row[8])/2,quad_segs=8)
   dr.polygon([xy(c) for c in s.exterior.coords],fill=color,outline=outline)
   if zz==z:dr.line([xy(row[:2]),xy(row[3:5])],fill='#16475f',width=1)
 dr.rectangle([xy([b[0],b[3]]),xy([b[2],b[1]])],outline='#e22741',width=3)
 dr.text((20,10),f'{pid} {label}   Z={z:.2f}  prev={prev:.2f}',font=font,fill='#142e35');dr.text((20,38),f'Previous bead grey; current bead blue; red: flagged bounds',font=font,fill='#142e35');im.save(p/'verification'/f'path_crop_{i}.png')
 print(i,z,flag.get('length_mm',flag.get('area_mm2')),flush=True)
