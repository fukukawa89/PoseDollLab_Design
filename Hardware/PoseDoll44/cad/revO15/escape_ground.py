"""Escape final ground pad on routed board, preserving 0.2 mm clearance.
Native DRC, not the conservative grid helper, decides whether it is usable.
"""
from pathlib import Path
import pcbnew as p,json,math,heapq
from route_controller import OUT,FILE
mm=p.ToMM;pt=lambda q:(mm(q.x),mm(q.y))
b=p.LoadBoard(str(FILE));pad=next(x for f in b.GetFootprints() if f.GetReference()=='U100' for x in f.Pads() if x.GetNumber()=='2');net=pad.GetNetname();start=pt(pad.GetPosition())
pads=[];traces=[];holes=[]
for f in b.GetFootprints():
 for x in f.Pads():
  bb=x.GetBoundingBox();pads.append((x.GetNetname(),[mm(bb.GetLeft()),mm(bb.GetTop()),mm(bb.GetRight()),mm(bb.GetBottom())],set(x.GetLayerSet().Seq())))
  if x.GetAttribute() in (p.PAD_ATTRIB_NPTH,p.PAD_ATTRIB_PTH):holes.append((pt(x.GetPosition()),mm(max(x.GetDrillSize().x,x.GetDrillSize().y))/2))
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  traces.append((t.GetNetname(),pt(t.GetPosition()),pt(t.GetPosition()),mm(t.GetWidth(p.F_Cu))/2,None));holes.append((pt(t.GetPosition()),mm(t.GetDrillValue())/2))
 else:traces.append((t.GetNetname(),pt(t.GetStart()),pt(t.GetEnd()),mm(t.GetWidth())/2,t.GetLayer()))
def pd(q,r):return math.hypot(max(r[0]-q[0],0,q[0]-r[2]),max(r[1]-q[1],0,q[1]-r[3]))
def sd(q,a,z):
 d=(z[0]-a[0],z[1]-a[1]);den=d[0]*d[0]+d[1]*d[1];v=max(0,min(1,((q[0]-a[0])*d[0]+(q[1]-a[1])*d[1])/den)) if den else 0
 return math.hypot(q[0]-a[0]-v*d[0],q[1]-a[1]-v*d[1])
def clear(q,via=False):
 radius=.3 if via else .1
 if not 1<q[0]<69 or not 1<q[1]<59:return False
 for n,r,ls in pads:
  if n!=net and (via or p.F_Cu in ls) and pd(q,r)<radius+.205:return False
  if via and pd(q,r)<radius+.07:return False
 for n,a,z,r,layer in traces:
  if n!=net and (via or layer in (None,p.F_Cu)) and sd(q,a,z)<radius+r+.205:return False
 if via and any(math.dist(q,c)<.15+r+.251 for c,r in holes):return False
 return True
step=.1;origin=start;point=lambda k:(origin[0]+k[0]*step,origin[1]+k[1]*step)
Q=[(0,(0,0))];prev={};cost={(0,0):0};end=None
while Q:
 _,k=heapq.heappop(Q);q=point(k)
 if clear(q,True):end=k;break
 for a,z in [(1,0),(-1,0),(0,1),(0,-1)]:
  v=(k[0]+a,k[1]+z)
  if v in cost or max(abs(v[0]),abs(v[1]))>120:continue
  if not clear(point(v)):continue
  cost[v]=cost[k]+1;prev[v]=k;heapq.heappush(Q,(cost[v],v))
if end is None:raise RuntimeError('No escape; reposition parts')
route=[end]
while route[-1]!=(0,0):route.append(prev[route[-1]])
route=route[::-1];simple=[route[0]]
for i in range(1,len(route)-1):
 if (route[i][0]-route[i-1][0],route[i][1]-route[i-1][1])!=(route[i+1][0]-route[i][0],route[i+1][1]-route[i][1]):simple.append(route[i])
simple.append(route[-1]);points=[point(k) for k in simple]
for a,z in zip(points,points[1:]):
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[p.FromMM(v) for v in a]));t.SetEnd(p.VECTOR2I(*[p.FromMM(v) for v in z]));t.SetWidth(p.FromMM(.2));t.SetLayer(p.F_Cu);t.SetNet(pad.GetNet());b.Add(t)
v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(*[p.FromMM(c) for c in point(end)]));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(pad.GetNet());b.Add(v)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(OUT/'manual_trial.kicad_pcb'),b);(OUT/'manual_trial.kicad_pro').write_bytes(FILE.with_suffix('.kicad_pro').read_bytes());(OUT/'last_ground_route.json').write_text(json.dumps(points,indent=2));print('GROUND ROUTE',points)
