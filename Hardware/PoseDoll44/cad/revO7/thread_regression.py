"""Independent regression for an OCC false-empty thread cut on a small bore."""
from pathlib import Path
import sys,math,json,hashlib
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import thread_sweep
p=[(2.72,-.23),(3.07,-(.23-.35/math.sqrt(3))),(3.07,.23-.35/math.sqrt(3)),(2.72,.23)];q=[];minor=2.73
for a,b in zip(p,p[1:]+p[:1]):
 ina,inb=a[0]>=minor,b[0]>=minor
 if ina:q.append(a)
 if ina!=inb:
  t=(minor-a[0])/(b[0]-a[0]);q.append((minor,a[1]+t*(b[1]-a[1])))
cross=[a[0]*b[1]-b[0]*a[1] for a,b in zip(q,q[1:]+q[:1])];area=abs(sum(cross))/2;cr=sum((a[0]+b[0])*c for a,b,c in zip(q,q[1:]+q[:1],cross))/(3*sum(cross));expected=2*math.pi*cr*area*3/.5
f=thread_sweep(p,z0=6.5,height=4,pitch=.5);base=ring(6,minor,7,10);bad=base.cut(f,tol=1e-5);good=cyl(6,7,10).cut(f,tol=1e-5).cut(cyl(minor,6.9,10.1),tol=1e-5)
w=cq.Vector(2.9,0,8.0);removed=base.Volume()-good.Volume();assert abs(removed/expected-1)<.02 and not good.isInside(w) and base.isInside(w) and f.isInside(w)
paths=[Path(__file__),H/'cad/revO3/compact_joint.py',H/'cad/revO6/thread_geometry.py'];d={'status':'PASS_THREAD_MATERIAL_REMOVAL_REGRESSION','independent_whole_turn_removed_volume_mm3':expected,'good_order_removed_mm3':removed,'bore_first_removed_mm3':base.Volume()-bad.Volume(),'bore_first_still_contains_cut_witness':bool(bad.isInside(w)),'good_order_contains_cut_witness':bool(good.isInside(w)),'lesson':'Boolean validity and conservation against the same faulty common are insufficient. Require independently expected positive removal and a material witness.','input_sha256':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'physical_tested':False};out=H/'verification/revO7/runs/o7_20260924_r1/thread_regression.json';out.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');print(d)
