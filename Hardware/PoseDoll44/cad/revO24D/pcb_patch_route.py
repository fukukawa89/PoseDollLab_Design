"""Conservative four-layer grid patch for one explicitly identified unrouted net."""
from pathlib import Path
import json,math,heapq
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parents[2]/'bench/revO24D/electronics/carrier'
NET='/B11_DO';STEP=.05;W=1281;H=1201
obs=json.loads((D/'routing_obstacles.json').read_text('utf8'))
def grid(x):return int(round(x/STEP))
def raster(extra,via=False):
 ims=[Image.new('1',(W,H)) for _ in range(4)];ds=[ImageDraw.Draw(im) for im in ims]
 for o in obs:
  own=o['net']==NET
  if own and not (via and o['kind']=='pad'):continue
  ls=o['layers'] if not(via and o['kind']=='pad' and o['smd']) else range(4)
  for l in ls:
   d=ds[l]
   if o['kind']=='pad':
    x0,y0,x1,y1=o['box'];d.rectangle((math.floor((x0-extra)/STEP),math.floor((y0-extra)/STEP),math.ceil((x1+extra)/STEP),math.ceil((y1+extra)/STEP)),fill=1)
   elif o['kind']=='via':
    x,y=o['center'];r=o['radius']+extra;d.ellipse((math.floor((x-r)/STEP),math.floor((y-r)/STEP),math.ceil((x+r)/STEP),math.ceil((y+r)/STEP)),fill=1)
   else:
    a,z=o['start'],o['end'];rr=o['radius']+extra
    d.line(tuple(grid(v) for v in a+z),fill=1,width=math.ceil(2*rr/STEP)+1)
    for x,y in [a,z]:d.ellipse((math.floor((x-rr)/STEP),math.floor((y-rr)/STEP),math.ceil((x+rr)/STEP),math.ceil((y+rr)/STEP)),fill=1)
 return np.array([np.asarray(im) for im in ims])
mask=raster(.15+.06);vmask=np.any(raster(.15+.225,True),axis=0)
startpad=next(o for o in obs if o['kind']=='pad' and o['ref']=='U4' and o['num']=='21')
s=(grid(startpad['center'][0]),grid(startpad['center'][1]),3);g=(grid(48),grid(23.9625));goal=lambda u:u[:2]==g
assert not mask[s[2],s[1],s[0]],'Start obstructed'
print('start',s,'goal',g,flush=True)
pq=[(0,0,s)];cost={s:0};prev={};end=None;n=0
while pq:
 _,c,u=heapq.heappop(pq)
 if cost.get(u)!=c:continue
 if goal(u):end=u;break
 n+=1
 if n>1500000:raise RuntimeError('Search budget')
 x,y,l=u
 neigh=[((x+dx,y+dy,l),math.sqrt(dx*dx+dy*dy)) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]]
 if not vmask[y,x]:neigh.extend([((x,y,ll),35) for ll in range(4) if ll!=l])
 for v,w in neigh:
  xx,yy,ll=v
  if xx<9 or yy<9 or xx>=W-9 or yy>=H-9 or mask[ll,yy,xx]:continue
  nc=c+w
  if nc<cost.get(v,1e100):cost[v]=nc;prev[v]=u;h=math.hypot(xx-g[0],yy-g[1]);heapq.heappush(pq,(nc+h,nc,v))
if end is None:raise RuntimeError('No route')
path=[end]
while path[-1]!=s:path.append(prev[path[-1]])
path.reverse();simple=[path[0]]
for i in range(1,len(path)-1):
 a,b,c=path[i-1:i+2]
 if tuple(b[j]-a[j] for j in range(3))!=tuple(c[j]-b[j] for j in range(3)):simple.append(b)
simple.append(path[-1]);out=dict(net=NET,start_exact_mm=startpad['center'],goal_exact_mm=[48,23.9625],track_width_mm=.12,via_mm=[.45,.2],grid_mm=STEP,states_examined=n,path=[[x*STEP,y*STEP,l] for x,y,l in simple]);(D/'patch_route.json').write_text(json.dumps(out,indent=2),'utf8');print('PATCH',len(simple),'vertices',n,'states',flush=True)
