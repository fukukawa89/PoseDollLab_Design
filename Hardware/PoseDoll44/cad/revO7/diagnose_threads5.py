from pathlib import Path
import sys,math,cadquery as cq
H=Path.cwd()/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring,bounds
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import thread_sweep,checked,overlap_volume
for fh,ri,ro,core in [(.215,2.72,3.04,2.73),(.22,2.72,3.04,2.73),(.23,2.72,3.07,2.78),(.215,2.67,3.02,2.73)]:
 f=thread_sweep([(ri,-fh),(ro,-(fh-(ro-ri)/math.sqrt(3))),(ro,fh-(ro-ri)/math.sqrt(3)),(ri,fh)],z0=6.5,height=4,pitch=.5)
 b0=ring(6,core,7,10);b=b0.cut(f,tol=1e-5)
 print('case',fh,ri,ro,core,'vols',f.Volume(),b0.Volume()-b.Volume(),'bounds',bounds(f),'solids',len(b.Solids()),flush=True)
 print('point',f.isInside(cq.Vector(2.9,0,8.0)),b0.isInside(cq.Vector(2.9,0,8.0)),b.isInside(cq.Vector(2.9,0,8.0)),flush=True)
