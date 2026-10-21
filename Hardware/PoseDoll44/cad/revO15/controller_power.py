"""Copper-resistance bound along actual branch output-to-connector routing.
No field-solver, transient or temperature measurement is claimed.
"""
import pcbnew as p,json,math,heapq,hashlib
from pathlib import Path
from route_controller import FILE,OUT
b=p.LoadBoard(str(FILE));rows=[];to=p.ToMM
for branch in range(1,7):
 net='/P'+str(branch)+'_3V3';ts=[t for t in b.GetTracks() if t.GetNetname()==net];points=[];index={};edges={}
 def node(x,y,l):
  key=(round(x,5),round(y,5),l)
  if key not in index:index[key]=len(points);points.append(key);edges[index[key]]=[]
  return index[key]
 def link(a,z,r):edges[a].append((z,r));edges[z].append((a,r))
 def point(v):return (to(v.x),to(v.y))
 tracks=[]
 for t in ts:
  if isinstance(t,p.PCB_VIA):
   x,y=point(t.GetPosition());link(node(x,y,p.F_Cu),node(x,y,p.B_Cu),.003)
  else:
   a,z=point(t.GetStart()),point(t.GetEnd());l=t.GetLayer();node(*a,l);node(*z,l);tracks.append((a,z,l,to(t.GetWidth())))
 for a,z,l,w in tracks:
  dx,dy=z[0]-a[0],z[1]-a[1];length=math.hypot(dx,dy);members=[]
  if length==0:continue
  for i,(x,y,ly) in enumerate(points):
   if ly!=l:continue
   u=((x-a[0])*dx+(y-a[1])*dy)/length**2
   if -.00001<=u<=1.00001 and abs((x-a[0])*dy-(y-a[1])*dx)/length<.00002:members.append((max(0,min(1,u)),i))
  members.sort()
  for (u,i),(v,j) in zip(members,members[1:]):link(i,j,(v-u)*length/1000*.017241*(1+.00393*40)/(w*.035))
 pads={}
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetname()!=net:continue
   idx=len(points);points.append(('pad',f.GetReference(),pad.GetNumber()));edges[idx]=[];pads[f.GetReference()+':'+pad.GetNumber()]=idx;bb=pad.GetBoundingBox()
   for (x,y,l),j in list(index.items()):
    if pad.IsOnLayer(l) and to(bb.GetLeft())-1e-5<=x<=to(bb.GetRight())+1e-5 and to(bb.GetTop())-1e-5<=y<=to(bb.GetBottom())+1e-5:link(idx,j,.001)
 source=pads[f'U{branch*100}:6'];target=pads[f'J{branch}:2'];q=[(0,source)];dist={source:0}
 while q:
  d,i=heapq.heappop(q)
  if d>dist[i]:continue
  for j,r in edges[i]:
   v=d+r
   if v<dist.get(j,1e9):dist[j]=v;heapq.heappush(q,(v,j))
 if target not in dist:raise RuntimeError(('Cannot reconstruct power route',branch))
 row={'branch':branch,'copper_path_ohm_at_60C_bound':dist[target],'assumed_outer_copper_um':35,'via_allowance_ohm_each':.003,'trace_segment_count':len(tracks)};rows.append(row);print(row)
(OUT/'power_trace_resistance.json').write_text(json.dumps({'branches':rows,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),'method':'Minimum single graph path, ignoring parallel copper. Pad and via allowances added; 60C copper resistivity. Does not model connector, protection IC, wire, heating, transient or full plane impedance.'},indent=2))
