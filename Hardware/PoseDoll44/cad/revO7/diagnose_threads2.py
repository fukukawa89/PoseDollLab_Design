from pathlib import Path
import sys,math,cadquery as cq
H=Path.cwd()/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import checked,overlap_volume
fp=[(2.72,-.23),(3.07,-(.23-.35/math.sqrt(3))),(3.07,.23-.35/math.sqrt(3)),(2.72,.23)];mp=[(2.70,-(.025+.30/math.sqrt(3))),(3.,-.025),(3.,.025),(2.70,.025+.30/math.sqrt(3))]
for height in [3.5,4]:
 def sweep(points,h):
  path=cq.Wire.makeHelix(.5,h,2.85,center=(0,0,6.5))
  return cq.Workplane('XZ').polyline([(x,6.5+z) for x,z in points]).close().sweep(path,isFrenet=True).val()
 f=sweep(fp,4);m=sweep(mp,height)
 b=checked(ring(6,2.73,7,10),f,'cut','b');p=checked(cyl(2.71,6.175,10.4),m,'fuse','p')
 print('HEIGHT',height,'vols',b.Volume(),p.Volume(),'overlap',overlap_volume(b,p),flush=True)
 for tol in [None,1e-6,1e-5,.0001,.001]:
  inter=b.intersect(p) if tol is None else b.intersect(p,tol=tol)
  print('tol',tol,'volume',inter.Volume(),'valid',inter.isValid(),'solids',len(inter.Solids()),flush=True)
 count=0
 for k in range(24):
  th=math.radians(k*15)
  for rad in [2.75,2.8,2.85,2.9,2.95]:
   for iz in range(120):
    q=cq.Vector(rad*math.cos(th),rad*math.sin(th),7+iz*.025+.013)
    if b.isInside(q) and p.isInside(q):count+=1
 print('sampletruehits',count,flush=True)
