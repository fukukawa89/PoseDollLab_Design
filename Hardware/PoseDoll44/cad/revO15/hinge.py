"""Complete printed single-axis joint using O12 stock friction stack.
Positive through-bolts retain housing and removable sensor/magnet caps.
Magnetic performance and printed material properties remain deferred tests.
"""
from common import *
def make():
 src=H/'bench/revO12/parts.npz';old={k:from_tri(t) for k,t in np.load(src).items()};p={};owners={};sku={}
 def put(k,s,owner,stock=None):p[k]=from_tri(tri(s));owners[k]=owner;sku[k]=stock
 # Exact received stock friction stack, relocated so the lever bearing plane is Z=0.
 for k,s in old.items():
  if k.startswith(('printed_','case_')):continue
  put(k,s.translate([0,0,-10.5]),'parent',{'shoulder_D4_L8_M3_thread6':'SHOULDER_D4_L8_M3_L6','inner_M4_wide':'W_M4_D12_T1','outer_M4_wide':'W_M4_D12_T1','front_M4_washer':'W_M4_D9_T0P8','spring_1':'A8_SS','spring_2':'A8_SS','M3_nut':'NUT_M3','M3_reaction_washer':'W_M3_D9_T0P8'}[k])
 cavity=(hexagon(5.8,-8.65,-6.05)+cyl(4.65,-6.15,-5.3)+cyl(1.7,-10.6,-3.5)+cyl(2.125,-4.4,-2.0))
 base=box([-14,-9,-10.5],[14,9,-2.5])-cavity
 for i,x in enumerate((-9,9)):
  M=rot(0,-90);origin=[x,0,-6.5]
  # 18 mm clamped width; standard M3x20 clears both the neighbouring joint
  # and the sensor post. The nut is captured inside the negative half.
  base-=pose(cyl(1.7,-12,14),M,origin)
  put(f'case_screw_{i}',pose(screw(3,20,5.6,3,9),M,origin),'parent','SCREW_M3_L20')
  put(f'case_nut_{i}',pose(nut(3,5.5,2.4,-9),M,origin),'parent','NUT_M3')
 # One fixed support in the unused angular sector; operating range -90..145 deg.
 # The rest of the 360-degree sweep is explicitly outside this joint's use range.
 holder=box([-6.3,-5.1,15.0],[-5.5,5.1,16.495])+box([5.5,-5.1,15.0],[6.3,5.1,16.495])
 # Positive XY location: the top clip alone cannot stop a PCB sliding out.
 for side in (-1,1):
  lo,hi=sorted((side*6.05,side*7.05));holder+=box([lo,-6.1,16.195],[hi,6.1,17.495])
  lo,hi=sorted((side*5.1,side*6.1));holder+=box([-7.05,lo,16.195],[7.05,hi,17.495])
 x,y=-13.5,-13.5
 post=cyl(5,-9.5,17.495).translate([x,y,0])
 post-=box([x-3.3,y-7,11.0],[x+3.3,y,13.55]);post-=hexagon(5.8,11.1,13.55).translate([x,y,0]);post-=cyl(1.7,10.8,19.1).translate([x,y,0])
 holder+=post+beam([-12,-8,-7],[x,y,-7],3)
 for side in (-1,1):holder+=beam([x,y,15.0],[side*5.9,-4.7,15.0],1.45)
 clip=box([-6.2,-5.5,17.495],[6.2,-4.6,19])+box([-6.2,-4.6,17.495],[-5.6,5.1,19])+box([5.6,-4.6,17.495],[6.2,5.1,19])
 clip+=cyl(5,17.495,19).translate([x,y,0])+beam([x,y,18.3],[-5.9,-5,18.3],.7)
 clip-=cyl(1.7,17.3,19.1).translate([x,y,0])
 # Key across the split prevents the one-screw clip turning about its fastener.
 key=box([x-4.7,y-.6,17.2],[x-2.7,y+.6,18.0]);holder+=key;clip-=key.translate([0,0,.0])
 put('pcb_clip',clip,'parent');put('pcb_clip_screw',screw(3,8,5.6,3,19).translate([x,y,0]),'parent','SCREW_M3_L8')
 put('pcb_clip_nut',nut(3,5.5,2.4,11.1).translate([x,y,0]),'parent','NUT_M3')
 for xx,yy in ((-2.3,-3.7),(-2.3,3.7),(2.3,-3.7),(2.3,3.75)):holder-=box([xx-1.2,yy-.95,15.0],[xx+1.2,yy+.95,16.6])
 # The cradle and clip lift together after removing their shared M3 screw.
 # This opens the magnet cup for a real assembly/service path. Lower post and
 # captured nut remain integral with the fixed half; two keys resist rotation.
 split=13.55
 cradle=holder^box([-50,-50,split],[50,50,50])
 holder=holder^box([-50,-50,-50],[50,50,split])
 for side in (-1,1):
  lo,hi=sorted((x+side*3.4,x+side*4.7))
  key=box([lo,y-.7,split-.2],[hi,y+.7,split+.65])
  holder+=key
  cradle-=box([lo-.1,y-.8,split-.01],[hi+.1,y+.8,split+.75])
 cradle-=cyl(1.7,10.8,19.1).translate([x,y,0])
 put('sensor_cradle',cradle,'parent')
 base_minus=(base^box([-20,-20,-20],[20,0,0]))+holder
 base_minus-=cyl(1.7,10.8,19.1).translate([x,y,0])
 for xx in (-9,9):base_minus-=pose(cyl(1.7,-12,14)+hexagon(5.8,-9.1,-6.59),rot(0,-90),[xx,0,-6.5])
 put('base_service_half',base^box([-20,0,-20],[20,20,0]),'parent')
 put('base_sensor_half',base_minus,'parent')
 lever=cyl(6,-1.5,1.5)+box([4,-6,-1.5],[30,6,4.5]);lever-=cyl(6.15,1.5,4.6);lever-=cyl(2.125,-1.6,4.6)
 # Positive cup-to-lever union, retained magnet cup cap with two M2 fasteners.
 cup=washer(11.5,6.3,1.5,8.3)
 # Open the full 12.6 mm bore for the 12 mm washers and shoulder-screw head.
 # A separate seat drops in after preload adjustment; the existing cap bolts
 # clamp its flange. Magnet insertion remains open before the cap is installed.
 seat=cyl(6.2,8.4,10.6)+cyl(11.5,9.8,10.6)
 seat-=cyl(3.1,10.4,10.7)+cyl(1.9,8.3,10.7)
 lever+=cup
 for x in (-8,8):
  seat-=cyl(1.15,8.3,10.7).translate([x,0,0])
  lever-=cyl(1.1,5.9,10.7).translate([x,0,0]);lever-=hexagon(4.3,6.1,7.8).translate([x,0,0])
  lever-=box([7.9 if x>0 else -13,-2.2,6.05],[13 if x>0 else -7.9,2.2,7.8])
  put(f'magnet_cap_nut_{x:+}',nut(2,4,1.6,6.2).translate([x,0,0]),'child','NUT_M2')
  put(f'magnet_cap_screw_{x:+}',screw(2,5,3.8,2,11.1).translate([x,0,0]),'child','SCREW_M2_L5')
 cap=cyl(11.5,10.6,13.1)-cyl(3.075,10.5,12.95)-cyl(2.9,12.8,13.2)
 for x in (-8,8):cap-=(cyl(1.15,10.5,13.2)+cyl(2.05,11.1,13.2)).translate([x,0,0])
 put('lever_cup',lever,'child');put('magnet_cap',cap,'child');put('magnet_seat',seat,'child');put('magnet',cyl(3,10.4,12.9),'child','MAGNET_D6_T2P5_DIAMETRIC')
 put('sensor_PCB',box([-6,-5,16.495],[6,5,17.495]),'parent','AS5048A_MINI_PCBA')
 put('sensor_IC',box([-3.25,-2.5,14.5],[3.25,2.5,16.495]),'parent','PCBA_INCLUDED')
 put('sensor_FPC_connector',box([-2.575,-1.575,17.495],[2.575,1.575,18.495]),'parent','PCBA_INCLUDED')
 # Conservative original passive component packages, tracked as PCBA constituents.
 for i,(x,y) in enumerate(((-2.3,-3.7),(-2.3,3.7),(2.3,-3.7),(2.3,3.75))):put(f'passive_{i}',box([x-1,y-.75,15.2],[x+1,y+.75,16.495]),'parent','PCBA_INCLUDED')
 return p,owners,sku

def main():
 p,owners,sku=make();rec={k:mesh_record(s) for k,s in p.items()};nom=hits(p)
 np.savez_compressed(OUT/'hinge_parts.npz',**{k:tri(s) for k,s in p.items()})
 samples=[]
 for angle in sorted(set(range(-180,181,10))|set(range(-90,146,5))):
  pp={k:pose(s,rot(2,angle)) if owners[k]=='child' else s for k,s in p.items()};cross=[]
  for h in hits(pp):
   if owners[h['pair'][0]]!=owners[h['pair'][1]]:cross.append(h)
  samples.append({'angle_deg':angle,'inside_operating_range':-90<=angle<=145,'findings':cross})
 save('hinge_build.json',{'inputs_sha256':{str(Path(__file__).relative_to(H)):sha(__file__),'bench/revO12/parts.npz':sha(H/'bench/revO12/parts.npz')},'parts':rec,'owners':owners,'stock_skus':sku,'nominal_findings':nom,'motion':samples,'operating_range_deg':[-90,145],'magnet_airgap_to_package_mm':1.6,'physical_tested':False,'assumption':'O12 friction stack usable as user-directed design input; new mounts and whole joint still untested'})
 print('hinge parts',len(p),'components',[(k,r['components']) for k,r in rec.items() if r['components']!=1], 'nominal',nom,'motion hits',[(r['angle_deg'],len(r['findings'])) for r in samples if r['findings'] and r['inside_operating_range']],flush=True)
if __name__=='__main__':main()
