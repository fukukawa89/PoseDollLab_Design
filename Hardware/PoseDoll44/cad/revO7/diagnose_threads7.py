from pathlib import Path
import sys,math,cadquery as cq
H=Path.cwd()/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import thread_sweep,checked,overlap_volume
fp=[(2.72,-.23),(3.07,-(.23-.35/math.sqrt(3))),(3.07,.23-.35/math.sqrt(3)),(2.72,.23)];mp=[(2.70,-(.025+.30/math.sqrt(3))),(3.,-.025),(3.,.025),(2.70,.025+.30/math.sqrt(3))]
f=thread_sweep(fp,z0=6.5,height=4,pitch=.5);m=thread_sweep(mp,z0=6.5,height=3.5,pitch=.5)
p=checked(cyl(2.71,5.675,10.4),m,'fuse','p');blank=cyl(6,7,10);bore=cyl(2.73,6.9,10.1);base=ring(6,2.73,7,10)
for mode in ['cut_first','union_tool','union_high_overlap']:
 if mode=='cut_first':b=blank.cut(f,tol=1e-5).cut(bore,tol=1e-5)
 elif mode=='union_tool':b=blank.cut(bore.fuse(f,tol=1e-5),tol=1e-5)
 else:
  bore=cyl(2.82,6.9,10.1);b=blank.cut(bore.fuse(f,tol=1e-5),tol=1e-5);base=ring(6,2.82,7,10)
 print(mode,'removed',base.Volume()-b.Volume(),'valid',b.isValid(),'solids',len(b.Solids()),'overlap',overlap_volume(b,p),flush=True)
