from validate_stock import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from matplotlib.font_manager import FontProperties
a,ss=saved();S={p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};r=load(OUT/'interfaces.json')['rolls'][0];iw=np.linalg.inv(r['W']);font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
fig,ax=plt.subplots(figsize=(11,8),dpi=160);fig.patch.set_facecolor('#f5f7f3');ax.set_facecolor('#f5f7f3')
selected=[n for n in S if n.startswith('RP_')]+['ROOT','SHOULDER_PITCH']
for n in selected:
 s=moved(S[n],rot([1,0,0],90)@iw);polys=s.slice(.01).to_polygons();verts=[];codes=[]
 for q in polys:
  points=[[-p[1],p[0]] for p in q];verts.extend(points+[points[0]]);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(points)-1)+[MPath.CLOSEPOLY])
 col='#789c8d' if n=='ROOT' else '#b5d0bf' if n=='RP_keeper' else '#50776e' if n=='SHOULDER_PITCH' else '#2471b7' if 'A8' in n else '#d6ac4f' if n=='RP_ANCHOR' else '#a7adb3'
 if verts:ax.add_patch(PathPatch(MPath(verts,codes),facecolor=col,edgecolor='#263a3c',lw=.55))
ax.set_xlim(-13,19);ax.set_ylim(-23,23);ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_xlabel('轴向 Z / mm',fontproperties=font);ax.set_ylabel('径向 X / mm',fontproperties=font)
ax.set_title('RP 肩俯仰：生产 STL 的真实中心截面',fontproperties=font,fontsize=16,pad=15)
labels=[((-1,10),(-10,20),'压盖环唇：捕获大平垫'),((.75,8.7),(4,21),'18×6.4×1.5 金属大平垫'),((-2.0,7),(-12,-15),'打印转子耳'),((-4.4,3),(-12,-20),'4片 A8：两片并联 × 两组串联'),((4.6,0),(9,-14),'闭合六角窝内 NL3'),((11,16),(12,11),'M3×16 锁压盖')]
for xy,tx,text in labels:ax.annotate(text,xy=xy,xytext=tx,fontproperties=font,fontsize=9,arrowprops=dict(arrowstyle='-',lw=.8,color='#364c46'),bbox=dict(fc='white',ec='none',alpha=.9,pad=2))
fig.text(.5,.035,'压盖挡止、碟簧预紧、尼龙螺纹锁固各自独立；截面只显示接口局部。',ha='center',fontproperties=font,fontsize=10);fig.tight_layout(rect=[0,.055,1,1]);fig.savefig(OUT/'images/roll_section.png');plt.close(fig)
