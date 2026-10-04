from pathlib import Path
import sys,math,cadquery as cq
H=Path.cwd()/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import thread_sweep,checked,overlap_volume
f=thread_sweep([(2.72,-.23),(3.07,-(.23-.35/math.sqrt(3))),(3.07,.23-.35/math.sqrt(3)),(2.72,.23)],z0=6.5,height=4,pitch=.5)
m=thread_sweep([(2.70,-(.025+.30/math.sqrt(3))),(3.,-.025),(3.,.025),(2.70,.025+.30/math.sqrt(3))],z0=6.5,height=3.5,pitch=.5)
for angle in [0.3,7,23]:
 b0=ring(6,2.73,7,10).rotate((0,0,0),(0,0,1),angle);p0=cyl(2.71,5.675,10.4).rotate((0,0,0),(0,0,1),angle)
 b=checked(b0,f,'cut','b');p=checked(p0,m,'fuse','p')
 print('angle',angle,'female_removed',b0.Volume()-b.Volume(),'added',p.Volume()-p0.Volume(),'overlap',overlap_volume(b,p),flush=True)
