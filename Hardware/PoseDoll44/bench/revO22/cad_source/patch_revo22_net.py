from pathlib import Path
import json,pcbnew as p
D=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO22/electronics/carrier';N='PoseDoll_O22_SSI_Carrier'
b=p.LoadBoard(str(D/(N+'.kicad_pcb')));obs=[];pads=[]
for f in b.GetFootprints():
 for pad in f.Pads():
  if pad.GetNetname()=='/B03_DO':pads.append({'p':[p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)],'ref':f.GetReference()})
  bb=pad.GetBoundingBox();obs.append({'kind':'rect','net':pad.GetNetname(),'layers':[l for l in [0,2] if pad.IsOnLayer(l)],'xy':[p.ToMM(bb.GetLeft()),p.ToMM(bb.GetTop()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())]})
for t in b.GetTracks():
 a=t.GetStart();v=t.GetEnd();isvia=isinstance(t,p.PCB_VIA)
 obs.append({'kind':'segment','net':t.GetNetname(),'layers':[0,2] if isvia else [t.GetLayer()],'a':[p.ToMM(a.x),p.ToMM(a.y)],'b':[p.ToMM(v.x),p.ToMM(v.y)],'radius':(.3 if isvia else p.ToMM(t.GetWidth())/2)})
(D/'route_obstacles.json').write_text(json.dumps({'obstacles':obs,'pads':pads}));print(pads)
