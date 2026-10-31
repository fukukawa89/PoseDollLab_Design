"""Deterministic short fan-outs to inner planes before offline autorouting.
Conservative pad rectangles and segment clearances; native KiCad DRC verifies.
"""
import math,json
import pcbnew as p

def seed(b):
 mm=lambda x:p.ToMM(x)
 point=lambda v:(mm(v.x),mm(v.y))
 def distance(q,a,z):
  d=(z[0]-a[0],z[1]-a[1]);den=d[0]*d[0]+d[1]*d[1];t=max(0,min(1,((q[0]-a[0])*d[0]+(q[1]-a[1])*d[1])/den)) if den else 0
  return math.hypot(q[0]-a[0]-t*d[0],q[1]-a[1]-t*d[1])
 pads=[]
 for f in b.GetFootprints():
  for pad in f.Pads():
   bb=pad.GetBoundingBox();pads.append((pad.GetNetname(),[mm(bb.GetLeft()),mm(bb.GetTop()),mm(bb.GetRight()),mm(bb.GetBottom())],pad,f.GetReference()))
 tracks=[];vias=[];rows=[]
 def pad_distance(q,r):return math.hypot(max(r[0]-q[0],0,q[0]-r[2]),max(r[1]-q[1],0,q[1]-r[3]))
 def clear_point(q,net,r,layer=None,via=False):
  if not .8<=q[0]<=69.2 or not .8<=q[1]<=59.2:return False
  for n,bb,pad,ref in pads:
   if layer is not None and not pad.IsOnLayer(layer):continue
   if n!=net and pad_distance(q,bb)<r+.22:return False
   # Avoid open via-in-pad on SMD even on the same net.
   if via and pad.GetAttribute()==p.PAD_ATTRIB_SMD and pad_distance(q,bb)<r+.08:return False
   if pad.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH):
    if math.dist(q,point(pad.GetPosition()))<(mm(max(pad.GetDrillSize().x,pad.GetDrillSize().y))+.3)/2+.27:return False
  for n,a,z,w,l in tracks:
   if (layer is None or layer==l) and n!=net and distance(q,a,z)<r+w/2+.22:return False
  for n,v in vias:
   if math.dist(q,v)<(.72 if n!=net else .58):return False
  return True
 targets=[(pad,ref) for n,r,pad,ref in pads if n in ('/GND','/SENSOR_3V3') and pad.GetAttribute()==p.PAD_ATTRIB_SMD]
 for pad,ref in targets:
  net=pad.GetNetname();start=point(pad.GetPosition());layer=p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu;width=.2 if net=='/GND' else .4;choice=None
  for radius in (.9,1.1,1.3,1.5,1.8,2.1,2.5,3.,3.5,4.):
   for degrees in (0,90,180,270,45,135,225,315):
    a=math.radians(degrees);end=(start[0]+radius*math.cos(a),start[1]+radius*math.sin(a))
    if not clear_point(end,net,.3,via=True):continue
    if not all(clear_point((start[0]+u*(end[0]-start[0]),start[1]+u*(end[1]-start[1])),net,width/2,layer) for u in [i/20 for i in range(1,21)]):continue
    choice=end;break
   if choice:break
  if choice is None:rows.append({'pad':ref+':'+pad.GetNumber(),'status':'NO_SEED'});continue
  via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(*[p.FromMM(v) for v in choice]));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pad.GetNet());b.Add(via)
  t=p.PCB_TRACK(b);t.SetStart(pad.GetPosition());t.SetEnd(via.GetPosition());t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(pad.GetNet());b.Add(t)
  tracks.append((net,start,choice,width,layer));vias.append((net,choice));rows.append({'pad':ref+':'+pad.GetNumber(),'status':'SEEDED','net':net,'via_mm':choice})
 return rows
