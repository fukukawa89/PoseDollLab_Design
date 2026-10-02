"""Obstacle-aware single-net repair. Native DRC is the final authority."""
from pathlib import Path
import json,heapq,math,numpy as np
D=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO22/electronics/carrier'
d=json.loads((D/'route_obstacles.json').read_text());STEP=.05;lo=np.array([101.,106.]);hi=np.array([112.,129.]);nx,ny=np.ceil((hi-lo)/STEP).astype(int)+1
occ=np.zeros((2,nx,ny),bool);via=np.zeros((nx,ny),bool)
def stamp(o,extra,target):
 if o['kind']=='rect':a=np.array(o['xy'][:2]);b=np.array(o['xy'][2:]);rad=extra
 else:a=np.array(o['a']);b=np.array(o['b']);rad=extra+o['radius']
 amin=np.minimum(a,b)-rad;amax=np.maximum(a,b)+rad
 left=np.maximum(0,np.floor((amin-lo)/STEP).astype(int));right=np.minimum([nx-1,ny-1],np.ceil((amax-lo)/STEP).astype(int))
 if np.any(right<left):return
 xx=lo[0]+np.arange(left[0],right[0]+1)[:,None]*STEP;yy=lo[1]+np.arange(left[1],right[1]+1)[None,:]*STEP
 if o['kind']=='rect':dist=np.maximum(np.maximum(a[0]-xx,xx-b[0]),0)**2+np.maximum(np.maximum(a[1]-yy,yy-b[1]),0)**2
 else:
  ab=b-a;length=ab@ab;t=np.clip(((xx-a[0])*ab[0]+(yy-a[1])*ab[1])/length,0,1) if length else 0
  dist=(xx-a[0]-t*ab[0])**2+(yy-a[1]-t*ab[1])**2
 target[left[0]:right[0]+1,left[1]:right[1]+1]|=dist<(rad+.003)**2
for o in d['obstacles']:
 if o['net']=='/B03_DO':continue
 for l in o['layers']:stamp(o,.15+.075,occ[0 if l==0 else 1])
 stamp(o,.15+.3,via)
# Vias off all component lands, including the connected pads.
for o in d['obstacles']:
 if o['kind']=='rect':stamp(o,.3+.1,via)
start=tuple(np.round((np.array(d['pads'][0]['p'])-lo)/STEP).astype(int))+(0,)
goal=tuple(np.round((np.array(d['pads'][1]['p'])-lo)/STEP).astype(int))+(0,)
assert not occ[start[2],start[0],start[1]],start
pq=[(0,0,start)];cost={start:0};prev={};steps=0
while pq:
 _,c,u=heapq.heappop(pq)
 if c!=cost[u]:continue
 if u==goal:break
 x,y,l=u;steps+=1
 candidates=[((x+dx,y+dy,l),14 if dx and dy else 10) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]]
 if not via[x,y]:candidates.append(((x,y,1-l),150))
 for v,w in candidates:
  xx,yy,ll=v
  if not(0<=xx<nx and 0<=yy<ny) or occ[ll,xx,yy]:continue
  if ll==l and xx!=x and yy!=y and (occ[l,x,yy] or occ[l,xx,y]):continue
  n=c+w
  if n<cost.get(v,1e30):
   cost[v]=n;prev[v]=u;dx,dy=abs(xx-goal[0]),abs(yy-goal[1]);heuristic=14*min(dx,dy)+10*abs(dx-dy)
   heapq.heappush(pq,(n+heuristic,n,v))
else:raise RuntimeError('No repair route in local window')
path=[goal]
while path[-1]!=start:path.append(prev[path[-1]])
path=path[::-1];points=[[(lo[0]+x*STEP),(lo[1]+y*STEP),l] for x,y,l in path]
(D/'signal_repair.json').write_text(json.dumps({'net':'/B03_DO','width_mm':.15,'endpoints':d['pads'],'path':points,'search_states':steps},indent=2));print('REPAIR',len(path),steps)
