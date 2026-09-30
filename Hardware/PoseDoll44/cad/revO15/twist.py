"""Printed finite twist with captured collar, replaceable radial brake pad,
stock M3 adjuster, and a positively retained coaxial magnet/PCBA assembly.
Friction force, wear, print creep and magnetic calibration await batch tests.
"""
from common import *
def sector(r0,r1,a,b,z0,z1):
 ang=np.deg2rad(np.linspace(a,b,max(2,int(abs(b-a)*2)+1)));v=np.r_[np.c_[r1*np.cos(ang),r1*np.sin(ang)],np.c_[r0*np.cos(ang[::-1]),r0*np.sin(ang[::-1])]];return md.CrossSection([v]).extrude(z1-z0).translate([0,0,z0])
def make(lo=-170,hi=170):
 p={};owners={};sku={}
 def put(k,s,o,stock=None):p[k]=from_tri(tri(s));owners[k]=o;sku[k]=stock
 body=cyl(12.5,-32.5,-18.8)
 for x in (-9.5,9.5):
  for z in (-30,-21.5):body+=box([x-1.9,-9,z-2],[x+1.9,9,z+2])
 body-=cyl(6.12,-34,-18);body-=cyl(9.82,-27.9,-24.7);body-=sector(9,11.48,lo-6,hi+6,-27.9,-24.7)
 # Radial pad and steel-nut-adjuster boss, distinct from shaft retention.
 zc=-30.75;body+=box([-4.5,8,zc-4.5],[4.5,15,zc+4.5])
 body-=cyl(6.12,-34,-18);body-=cyl(9.82,-27.9,-24.7);body-=sector(9,11.48,lo-6,hi+6,-27.9,-24.7)
 body-=cyl(9.2,-36,-32.5)
 body-=box([-2.65,0,zc-1.65],[2.65,9.05,zc+1.65])
 body-=pose(cyl(1.7,8.9,15.1),rot(0,-90),[0,0,zc])
 body-=pose(hexagon(5.8,9.8,12.3),rot(0,-90),[0,0,zc])
 # Nut drops from the open end before rotor/fork assembly; screw prevents escape.
 body-=box([-3.3,9.75,zc],[3.3,12.35,-18.7])
 # M3x8 has 2 mm head clearance at first pad contact; preload is adjustable.
 pad=box([-2.5,4.5,zc-1.5],[2.5,9,zc+1.5])-cyl(6.01,-33,-28)
 put('radial_pad',pad,'parent');put('adjust_screw',pose(screw(3,8,5.6,3,17),rot(0,-90),[0,0,zc]),'parent','SCREW_M3_L8')
 put('adjust_nut',pose(nut(3,5.5,2.4,9.8),rot(0,-90),[0,0,zc]),'parent','NUT_M3')
 for i,(x,z) in enumerate(itertools.product((-9.5,9.5),(-30,-21.5))):
  F=rot(0,-90);body-=pose(cyl(1.1,-12.1,12.1),F,[x,0,z]);body-=pose(hexagon(4.3,-11.1,-9),F,[x,0,z]);body-=pose(cyl(2.,9,11.1),F,[x,0,z])
  put(f'case_screw_{i}',pose(screw(2,20,3.8,2,9),F,[x,0,z]),'parent','SCREW_M2_L20')
  put(f'case_nut_{i}',pose(nut(2,4,1.6,-10.6),F,[x,0,z]),'parent','NUT_M2')
 rotor=(cyl(6,-32.3,-18.3)-cyl(4.4,-34,-18))+(cyl(9.6,-27.8,-24.8)-cyl(4.4,-28,-24))+sector(9.4,11.3,-6,6,-27.8,-24.8)
 # Sensor head local W points away from joint (negative module Z).
 Z=-34.1;F=rot(0,180)
 def local(s):return pose(s,F,[0,0,Z])
 cup=cyl(6,-1.9,.7)+cyl(9,-1.2,1.1)
 # Cup presents a solid floor at W=1.1 beneath the magnet.
 for x in (-5.8,5.8):
  cup-=cyl(1.1,-1.6,1.2).translate([x,0,0]);cup-=hexagon(4.3,-1.15,.55).translate([x,0,0])
  cup-=box([5.7 if x>0 else -10,-2.2,-1.15],[10 if x>0 else -5.7,2.2,.55])
  put(f'magnet_nut_{x:+}',local(nut(2,4,1.6,-1.1).translate([x,0,0])),'child','NUT_M2')
  put(f'magnet_screw_{x:+}',local(screw(2,4,3.8,2,2.6).translate([x,0,0])),'child','SCREW_M2_L4')
 cap=cyl(9,1.1,4.7)-cyl(3.075,1.,3.65)-cyl(2.9,3.6,4.8)
 for x in (-5.8,5.8):
  cap-=cyl(1.15,1.,4.8).translate([x,0,0]);cap-=cyl(2,2.6,4.8).translate([x,0,0])
 put('rotor',rotor+local(cup),'child');put('magnet_cap',local(cap),'child');put('magnet',local(cyl(3,1.1,3.6)),'child','MAGNET_D6_T2P5_DIAMETRIC')
 holder=box([-6.3,-5.1,5.8],[-5.5,5.1,7.195])+box([5.5,-5.1,5.8],[6.3,5.1,7.195])
 for side in (-1,1):
  lo,hi=sorted((side*6.05,side*7.05));holder+=box([lo,-6.1,6.895],[hi,6.1,8.195])
  lo,hi=sorted((side*5.1,side*6.1));holder+=box([-7.05,lo,6.895],[7.05,hi,8.195])
 for x in (-14,14):
  post=cyl(3.5,-6,8.195).translate([x,0,0]);post-=cyl(1.15,1.5,9.8).translate([x,0,0]);post-=hexagon(4.3,2,3.65).translate([x,0,0]);post-=box([x-2.5,-4,2],[x+2.5,0,3.65])
  holder+=post
  for y in (-4.7,4.7):holder+=beam([x,0,6.1],[math.copysign(5.9,x),y,6.1],1.05)
  clip=box([min(x,math.copysign(5.6,x))-.8,-1.8,8.195],[max(x,math.copysign(5.6,x))+.8,1.8,9.7]);clip-=cyl(1.15,8.1,9.8).translate([x,0,0])
  put(f'pcb_clip_{x:+}',local(clip),'parent');put(f'pcb_screw_{x:+}',local(screw(2,8,3.8,2,9.7).translate([x,0,0])),'parent','SCREW_M2_L8');put(f'pcb_nut_{x:+}',local(nut(2,4,1.6,2).translate([x,0,0])),'parent','NUT_M2')
 # Separate halves keep collar and fastener assembly radial and serviceable.
 body+=local(holder)
 for x in (-14,14):body-=local(cyl(1.15,1.5,9.8).translate([x,0,0]))
 for i,(x,z) in enumerate(itertools.product((-9.5,9.5),(-30,-21.5))):body-=pose(cyl(1.1,-12.1,12.1),rot(0,-90),[x,0,z])
 put('case_minus',body^box([-30,-30,-60],[30,0,0]),'parent');put('case_plus',body^box([-30,0,-60],[30,30,0]),'parent')
 put('sensor_PCB',local(box([-6,-5,7.195],[6,5,8.195])),'parent','AS5048A_MINI_PCBA')
 put('sensor_IC',local(box([-3.25,-2.5,5.2],[3.25,2.5,7.195])),'parent','PCBA_INCLUDED')
 put('sensor_FPC_connector',local(box([-2.575,-1.575,8.195],[2.575,1.575,9.195])),'parent','PCBA_INCLUDED')
 for i,(x,y) in enumerate(((-2.3,-3.7),(-2.3,3.7),(2.3,-3.7),(2.3,3.75))):put(f'passive_{i}',local(box([x-1,y-.75,5.9],[x+1,y+.75,7.195])),'parent','PCBA_INCLUDED')
 return p,owners,sku

def main():
 p,o,sku=make();records={k:mesh_record(s) for k,s in p.items()};nom=hits(p);motion=[]
 for q in range(-170,171,10):
  pp={k:pose(s,rot(2,q)) if o[k]=='child' else s for k,s in p.items()};cross=[h for h in hits(pp) if o[h['pair'][0]]!=o[h['pair'][1]]];motion.append({'angle_deg':q,'findings':cross})
 np.savez_compressed(OUT/'twist_parts.npz',**{k:tri(s) for k,s in p.items()})
 save('twist_build.json',{'parts':records,'owners':o,'stock_skus':sku,'nominal_findings':nom,'motion':motion,'range_deg':[-170,170],'retention':'Printed rotor collar captured by split bearing case; separate adjustable radial friction pad','pad_preload_force_N':None,'holding_torque_Nm':None,'magnet_airgap_to_package_mm':1.6,'physical_tested':False})
 print('twist',len(p),'components',[(k,r['components']) for k,r in records.items() if r['components']!=1],'nominal',nom,'motion',[(m['angle_deg'],len(m['findings'])) for m in motion if m['findings']],flush=True)
if __name__=='__main__':main()
