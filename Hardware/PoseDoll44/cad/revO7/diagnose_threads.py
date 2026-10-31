from pathlib import Path
import sys,math,cadquery as cq
H=Path.cwd()/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring,bounds
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import thread_sweep,checked,overlap_volume
f=thread_sweep([(2.72,-.23),(3.07,-(.23-.35/math.sqrt(3))),(3.07,.23-.35/math.sqrt(3)),(2.72,.23)],z0=6.5,height=4,pitch=.5)
m=thread_sweep([(2.70,-(.025+.30/math.sqrt(3))),(3.,-.025),(3.,.025),(2.70,.025+.30/math.sqrt(3))],z0=6.5,height=3.5,pitch=.5)
p=checked(cyl(2.71,6.175,10.4),m,'fuse','p')
b=checked(ring(6,2.73,7,10),f,'cut','b')
print('BASIC',overlap_volume(b,p),flush=True)
for shift in [0,.025,-.025,.05,-.05,.125,-.125,.25]: print('shift',shift,overlap_volume(b,p.translate((0,0,shift))),flush=True)
for name,s in [('female',f),('male',m)]:
 print(name,'x3y0',[(round(z,3),s.isInside(cq.Vector(2.9,0,z))) for z in [7.25+i*.025 for i in range(21)]],flush=True)
