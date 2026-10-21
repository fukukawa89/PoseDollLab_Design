"""Measured F5/F6 support-hole cross-sections; no artistic reconstruction."""
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageChops
import o22f6_holeclear as h
D=h.B/'diagnostics/D01_PETG_20261013';old=json.loads((D/'P095_hole_diagnosis.json').read_text());n=np.load(h.OUT/'parts/P095.npz');new={k:[v.tolist()for v in h.solid(n[a],n[b]).slice(11.72).to_polygons()]for k,a,b in [('body','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]};W=1400;H=870;im=Image.new('RGB',(W,H),'#f5f7fa');dr=ImageDraw.Draw(im);font='C:/Windows/Fonts/msyh.ttc';cols={'body':'#4b90c7','fin':'#ed9567','teeth':'#f9c53a'}
def text(x,y,s,size=22,color='#20364a'):dr.text((x,y),s,font=ImageFont.truetype(font,size),fill=color)
def panel(rect,lim,sec):
 x,y,w,hh=rect;lo=np.array(lim[:2]);hi=np.array(lim[2:]);scale=min(w/(hi[0]-lo[0]),hh/(hi[1]-lo[1]));off=(np.array([w,hh])-(hi-lo)*scale)/2
 def tr(p):p=(np.asarray(p)-lo)*scale+off;return [(int(a),int(hh-b))for a,b in p]
 tile=Image.new('RGB',(w,hh),'white')
 for name in ['fin','body','teeth']:
  mask=Image.new('1',(w,hh),0)
  for ring in sec[name]:
   mm=Image.new('1',(w,hh),0);ImageDraw.Draw(mm).polygon(tr(ring),fill=1);mask=ImageChops.logical_xor(mask,mm)
  tile.paste(cols[name],(0,0,w,hh),mask)
 im.paste(tile,(x,y));dr.rectangle((x,y,x+w,y+hh),outline='#c9d2da',width=1)
 def pos(xy):a,b=tr([xy])[0];return x+a,y+b
 return pos
text(35,20,'P095 螺丝孔支撑避让：F5 → F6',30)
text(35,66,'真实交付网格剖面 Z = 11.72 mm；本图比较支撑几何，不代表实物试打结果。',19,'#536678')
for i,(key,label)in enumerate([('body','保留的零件本体'),('fin','需拆除的支撑鳍'),('teeth','需拆除的连接齿')]):
 x=40+i*280;dr.rectangle((x,104,x+23,125),fill=cols[key]);text(x+34,100,label,18)
for j,(title,sec)in enumerate([('O22F5 原版',old['sections']),('O22F6 当前候选',new)]):
 x=35+j*700;text(x,143,title,25);p=panel((x,187,630,400),(-2,-2,54,43),sec)
 for hole in old['holes']:
  a,b=p(hole['xy']);color='#c33b32'if j==0 and hole['number']in(2,4)else'#23805b';dr.ellipse((a-18,b-18,a+18,b+18),outline=color,width=2);text(a+21,b-15,'H'+str(hole['number']),19,color)
 for k,num in enumerate([2,4]):
  xx=x+k*325;hole=old['holes'][num-1];cx,cy=hole['xy'];text(xx,605,'H'+str(num)+' 孔口放大',20);panel((xx,642,305,155),(cx-3,cy-1.5,cx+3,cy+1.5),sec)
text(35,818,'F5：H2 / H4 内有连接齿。F6：四孔保护区内的支撑几何占用均为零（容差 0.000001 mm³）。',19)
path=h.OUT/'verification/figures/P095_孔位修复对照.png';path.parent.mkdir(parents=True,exist_ok=True);im.save(path);print(path)