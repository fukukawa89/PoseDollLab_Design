from pathlib import Path
import json,math,pcbnew as p
D=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO22/electronics/carrier';b=p.LoadBoard(str(D/'PoseDoll_O22_SSI_Carrier.kicad_pcb'));out={}
pt=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for z in b.Zones():
 if z.GetIsRuleArea():continue
 net=z.GetNetname();layer=z.GetLayer();poly=z.GetFilledPolysList(layer).CloneDropTriangulation();thin=poly.CloneDropTriangulation();thin.Deflate(p.FromMM(.15),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,p.FromMM(.005));wide=poly.CloneDropTriangulation();wide.Deflate(p.FromMM(.35),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,p.FromMM(.005))
 nodes={};edges=[];join=[]
 # Embedded .7mm copper strips on a 1mm grid, excluding all cutouts.
 for x in range(76,155):
  for y in range(76,169):
   if wide.Contains(pt(x,y)):nodes[(x,y)]=len(nodes)
 for (x,y),i in nodes.items():
  for dx,dy in [(1,0),(0,1)]:
   other=(x+dx,y+dy)
   if other in nodes and all(wide.Contains(pt(x+t*dx/10,y+t*dy/10)) for t in range(1,10)):edges.append([i,nodes[other],1.,.7])
 vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()==net]
 for v in vias:
  xy=v.GetPosition();x,y=p.ToMM(xy.x),p.ToMM(xy.y);candidates=sorted(nodes,key=lambda n:(n[0]-x)**2+(n[1]-y)**2)
  for gx,gy in candidates[:40]:
   length=math.hypot(gx-x,gy-y);count=max(2,math.ceil(length/.05))
   if all(length*i/count<.32 or thin.Contains(pt(x+(gx-x)*i/count,y+(gy-y)*i/count)) for i in range(1,count+1)):
    join.append({'xy':[x,y],'node':nodes[(gx,gy)],'length_mm':length,'width_mm':.3});break
 out[net]={'layer':layer,'nodes':list(nodes),'edges':edges,'joins':join,'vias':len(vias),'connected_vias':len(join),'inner_copper_mm':.0175,'model':'Embedded sparse strip network; no credit for unused copper.'}
 print(net,'grid',len(nodes),'edges',len(edges),'vias',len(join),'of',len(vias),flush=True)
(D/'plane_resistor_network.json').write_text(json.dumps(out))
