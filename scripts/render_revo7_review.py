from pathlib import Path
import json,math,argparse,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
source=H/'generated/revO7/runs/o7_20260924_r1/review_mesh.json';data=json.loads(source.read_text())
S=2;W,HH=1500,1060
im=Image.new('RGB',(W*S,HH*S),'#f5f5f1');d=ImageDraw.Draw(im)
font='C:/Windows/Fonts/msyh.ttc'
def text(x,y,s,size=22,fill='#243749'):
 d.text((x*S,y*S),s,font=ImageFont.truetype(font,size*S),fill=fill)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
cam=[.69,-.61,.39];l=math.sqrt(dot(cam,cam));cam=[v/l for v in cam];u=[-cam[1],cam[0],0];l=math.sqrt(dot(u,u));u=[v/l for v in u];v=[cam[1]*u[2]-cam[2]*u[1],cam[2]*u[0]-cam[0]*u[2],cam[0]*u[1]-cam[1]*u[0]]
colors={'al6061':(157,184,202),'al7075':(128,161,184),'steel':(130,140,146),'bronze':(193,150,70),'lining':(188,112,77),'PEEK':(188,112,77),'FR4':(35,141,107),'package':(67,75,81),'connector':(228,219,189),'POM':(226,222,199),'magnet':(206,96,108),'nylon':(185,184,157),'ceramic':(181,148,98)}
text(45,24,'PoseDoll O7 · 变薄方案的收益与代价',36)
text(47,80,'实际 STEP 同尺度投影；L6 隐去杯体及左半盒，LP6 隐去后承力板及左前半板。',21)
for index,m in enumerate(data['models']):
 cx=385+index*735;cy=400;scale=7.5;faces=[]
 for p in m['parts']:
  vs=p['vertices'];rgb=colors.get(p['material'],(150,150,150))
  for f in p['faces']:
   pts=[vs[i] for i in f];e1=[pts[1][i]-pts[0][i] for i in range(3)];e2=[pts[2][i]-pts[0][i] for i in range(3)];normal=[e1[1]*e2[2]-e1[2]*e2[1],e1[2]*e2[0]-e1[0]*e2[2],e1[0]*e2[1]-e1[1]*e2[0]];nl=math.sqrt(dot(normal,normal));shade=.58+.42*abs(dot(normal,cam))/nl if nl else .8
   poly=[((cx+scale*dot(pt,u))*S,(cy-scale*dot(pt,v))*S) for pt in pts];depth=sum(dot(pt,cam) for pt in pts)/3;faces.append((depth,poly,tuple(int(c*shade) for c in rgb)))
 for _,poly,c in sorted(faces,key=lambda x:x[0]):d.polygon(poly,fill=c)
 dims=[m['bounds_mm'][i+3]-m['bounds_mm'][i] for i in range(3)]
 text(cx-300,640,m['family']+'  '+('现有模块对照' if index==0 else '三组周向碟簧试验件'),29)
 text(cx-300,688,f"模型质量 {m['mass_g']:.2f} g · {dims[0]:.1f} × {dims[1]:.1f} × {dims[2]:.1f} mm",19)
 text(cx-300,728,('58 个零件；轴向碟簧' if index==0 else '75 个零件；轴向缩短约 33.5%，径向增大'),19)
d.line((45*S,790*S,1455*S,790*S),fill='#c6cdd0',width=2*S)
text(47,820,'关节变薄 ≠ 整机运动通过',25)
text(47,865,'LP6：保留原尺寸 AS5048 测角头，支承跨度 10.8 mm；目录弹簧力不是保证预紧力。',20)
text(47,904,'双臂仍有实体碰撞；先测材料摩擦、弹簧曲线与受载滑动，再决定多轴结构尺寸。',20)
text(47,978,'数字研究结果 · 无实物测试 · 尚未制造放行',21,fill='#9a5438')
a.out.parent.mkdir(parents=True,exist_ok=True);im.resize((W,HH),Image.Resampling.LANCZOS).save(a.out)
print(str(a.out))

