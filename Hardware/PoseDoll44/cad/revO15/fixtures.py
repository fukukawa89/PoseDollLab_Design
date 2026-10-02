"""External gateway case and a solder-spacing gauge; desktop only."""
from common import *

def make():
 p={};base=box([-6,-6,0],[29,28,8])-box([-1,-1,2],[24,22,9]);lid=box([-6,-6,8],[29,28,10]);p['gateway_xiao']=box([0,0,3],[22.5,17.8,7.5]);base-=box([-.1,-6.1,2.5],[15,1,8.1]);lid-=box([-.1,-6.1,8],[15,1,10.1])
 # Four corner fasteners, captured M2 nuts and supported PCB rails.
 base+=box([0,17.8,2],[22.5,19.5,5])+box([0,-.9,2],[22.5,0,3]);stock={}
 for j,(x,y) in enumerate([(-4,25.5),(27,25.5),(-4,-4),(27,-4)]):
  base+=cyl(3,0,8).translate([x,y,0]);base-=(cyl(1.15,1.2,8.1)+hexagon(4.3,2,3.8)+box([-2.5,-3.2,2],[2.5,0,3.8])).translate([x,y,0]);lid+=cyl(3,8,10).translate([x,y,0]);lid-=cyl(1.15,7.9,10.1).translate([x,y,0]);p[f'gateway_screw_{j}']=screw(2,8,3.8,2,10).translate([x,y,0]);stock[f'gateway_screw_{j}']='SCREW_M2_L8';p[f'gateway_nut_{j}']=nut(2,4,1.6,2.1).translate([x,y,0]);stock[f'gateway_nut_{j}']='NUT_M2'
 # Antenna has its own flat plate, away from USB and metal mounting screws.
 lid+=box([-8,30,8],[31,49,10])+box([8,25,8],[16,32,10]);lid-=cyl(1.2,7.9,10.1).translate([12,20,0]);p['gateway_antenna']=box([-7.2,30.7,10],[30.2,48.2,11.8]);stock['gateway_antenna']='SEEED_FPC_A02_65MM';stock['gateway_xiao']='XIAO_ESP32S3'
 p['gateway_base']=base;p['gateway_lid']=lid
 # A removable four-mm separation jig on the two outer board corners; not permanent.
 p['xiao_spacing_gauge']=box([0,0,0],[22,3,4])+box([0,3,0],[3,20,4])+box([19,3,0],[22,20,4]);stock.update(gateway_base=None,gateway_lid=None,xiao_spacing_gauge=None)
 hh=hits({k:v for k,v in p.items() if k!='xiao_spacing_gauge'});save('fixtures.json',{'parts':{k:mesh_record(v) for k,v in p.items()},'sku':stock,'findings':hh,'physical_tested':False});np.savez_compressed(OUT/'fixtures.npz',**{k:tri(v) for k,v in p.items()});print('FIXTURES',hh)
if __name__=='__main__':make()
