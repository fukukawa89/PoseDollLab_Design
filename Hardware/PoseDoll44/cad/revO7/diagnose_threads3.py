from pathlib import Path
import sys,math,cadquery as cq
H=Path.cwd()/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import thread_sweep,checked,overlap_volume
for pitch,ri,fi,mh,fh in [(.5,2.70,2.72,.025,.23),(.75,2.6,2.61,.04,.32),(1.,2.45,2.47,.025,.37)]:
 mp=[(ri,-(mh+(3-ri)/math.sqrt(3))),(3.,-mh),(3.,mh),(ri,mh+(3-ri)/math.sqrt(3))]
 fp=[(fi,-fh),(3.07,-(fh-(3.07-fi)/math.sqrt(3))),(3.07,fh-(3.07-fi)/math.sqrt(3)),(fi,fh)]
 f=thread_sweep(fp,z0=6.5,height=4,pitch=pitch);m=thread_sweep(mp,z0=6.5,height=4,pitch=pitch)
 blank=ring(6,fi+.01,7,10);b=checked(blank,f,'cut','b');p=checked(cyl(ri+.01,5.675,10.4),m,'fuse','p')
 print('case',pitch,'female removal',blank.Volume()-b.Volume(),'overlap',overlap_volume(b,p),'baseRingV',blank.Volume(),'fV',f.Volume(),flush=True)
 for x in [2.8,2.9]: print('sample',x,'f',f.isInside(cq.Vector(x,0,8.0)),'b',b.isInside(cq.Vector(x,0,8.0)),'p',p.isInside(cq.Vector(x,0,8.0)),flush=True)
