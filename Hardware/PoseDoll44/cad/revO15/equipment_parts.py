"""Physical enclosure candidates using manufacturer dimensions and actual PCBA layout.
All positions in board u,v, outward h millimetres. Dimensions are prototypes;
no fabricated supplier qualification or heat/strength claims.
"""
from common import *
D=H/'electronics/revO15/central_c1'

def controller():
 p={};sku={};note={}
 def put(k,s,stock=None):p[k]=s;sku[k]=stock
 shell=box([-5,-5,0],[75,65,23])-box([-2,-2,2],[72,62,24]);lid=box([-5,-5,23],[75,65,25]);pcb=box([0,0,6],[70,60,7.2])
 # Positive captive-nut standoffs, with side-loaded nuts before the board.
 for j,(u,v) in enumerate([(11,3),(59,3),(3,57),(67,57)]):
  post=cyl(3.2,1.8,6).translate([u,v,0]);void=(cyl(1.15,.8,7.3)+hexagon(4.3,2.7,4.45)+box([-2.5,-3.3,2.7],[2.5,0,4.45])).translate([u,v,0]);shell+=post;shell-=void;pcb-=cyl(1.1,5.9,7.3).translate([u,v,0]);put('pcb_nut_'+str(j),nut(2,4,1.6,2.8).translate([u,v,0]),'NUT_M2');put('pcb_screw_'+str(j),screw(2,6,3.8,2,7.2).translate([u,v,0]),'SCREW_M2_L6')
 for j,(u,v) in enumerate([(-2.4,-2.4),(72.4,-2.4),(-2.4,62.4),(72.4,62.4)]):
  lid+=cyl(3.2,23,25).translate([u,v,0]);shell+=cyl(3.2,0,23).translate([u,v,0]);shell-=(cyl(1.15,16.5,23.1)+hexagon(4.3,17.7,19.5)+box([-2.5,-4.5,17.7],[2.5,0,19.5])).translate([u,v,0]);lid-=cyl(1.15,22.9,25.1).translate([u,v,0]);put('lid_nut_'+str(j),nut(2,4,1.6,17.8).translate([u,v,0]),'NUT_M2');put('lid_screw_'+str(j),screw(2,8,3.8,2,25).translate([u,v,0]),'SCREW_M2_L8')
 for r in read(D/'mechanical_envelopes.json'):
  ref=r['ref'];x0,y0,x1,y1=r['bounds_mm']
  if ref.startswith('H') or ref=='U1':continue
  if r['side']=='back':z0,z1=4.5,6
  else:z0,z1=7.2,7.2+(6 if ref in ('J7','J8') else 3 if ref.startswith('J') else 2.5 if ref=='D1' else 1.5)
  put('pcba_'+ref,box([x0,y0,z0],[x1,y1,z1]),'C1_PCBA_INCLUDED')
  if r['side']=='back':shell-=box([x0-.25,y0-.25,z0-.2],[x1+.25,y1+.25,z1+.2])
 for n,(u,v) in enumerate([(27.38,14-7.62+i*2.54) for i in range(7)]+[(42.62,14-7.62+i*2.54) for i in range(7)]):pcb-=cyl(.5,5.9,7.3).translate([u,v,0])
 for u in (27.38,42.62):put('xiao_pinstrip_'+str(u),box([u-1.27,14-8.89,7.2],[u+1.27,14+8.89,9.74]),'HEADER_1X7_P2P54')
 put('xiao',box([26.11,3.5,11.2],[43.89,24.5,15.66]),'XIAO_ESP32S3')
 # Buck faces down from removable lid, on the two diagonal factory holes.
 # Top-view holes are (2.3,2.3),(15.5,15.5); 17.8 square, PCB1.02,
 # components6.0 front /1.1 back. No fabricated pin or component clearance.
 ub,vb=10.,32.;buckpcb=box([ub,vb,16],[ub+17.8,vb+17.8,17.02]);buckfront=box([ub+.2,vb+.2,10],[ub+17.6,vb+17.6,16]);buckback=box([ub+.2,vb+.2,17.02],[ub+17.6,vb+17.6,18.12]);F=rot(0,180)
 for j,(a,b) in enumerate([(2.3,2.3),(15.5,15.5)]):
  u,v=ub+a,vb+b;hole=cyl(1.09,9.9,18.2).translate([u,v,0]);buckpcb-=hole
  # Manufacturer drawings show clear mounting circles at the two corners.
  keep=cyl(2.2,9.8,18.3).translate([u,v,0]);buckfront-=keep;buckback-=keep
  post=cyl(2.1,17.02,23.1).translate([u,v,0]);lid+=post;lid-=(cyl(1.15,15.9,23.1)+hexagon(4.3,20.2,21.95)+box([-2.5,-3,20.2],[2.5,0,21.95])).translate([u,v,0]);put('buck_nut_'+str(j),nut(2,4,1.6,20.3).translate([u,v,0]),'NUT_M2');put('buck_screw_'+str(j),pose(screw(2,6,3.8,2,0),F,[u,v,16]),'SCREW_M2_L6')
 put('buck',buckpcb+buckfront+buckback,'POLOLU_D24V22F3')
 # Ventilation and a 37.4 x17.5 mm Seeed A-02 antenna outside the lid.
 for u in (44,50,56,62):lid-=box([u,32,22.9],[u+2,54,25.1])
 lid-=cyl(1.2,22.9,25.1).translate([15,14,0]);put('antenna',box([16.3,5.25,25],[53.7,22.75,26.8]),'SEEED_FPC_A02_65MM')
 for side in (0,1):
  for j,v in enumerate((10,29,48)):
   u0,u1=(-6,1) if side==0 else (69,76);shell-=box([u0,v-5,6.5],[u1,v+5,14]);p0,p1=(-10,1) if side==0 else (69,80);put(f'gh_mate_{side}_{j}',box([p0,v-3,7.5],[p1,v+3,11.5]),'JST_GH_6P_MATE')
 # Power cable exits the bottom. Rounded edge/tie slots are retained.
 shell-=box([30,61,10],[40,66,18])
 for u in (23,45):shell-=box([u,61,3],[u+3,66,4.6])
 put('main_PCB',pcb,'C1_CENTRAL_PCBA');put('base',shell);put('lid',lid)
 note={'board_to_xiao_PCB_bottom_mm':4.0,'xiao_header_instruction':'Solder module at 4.0 mm separation using temporary printed gauge; header body is2.54mm. No shorting underside parts.','buck_mount':'two existing diagonal M2 holes, underside of removable lid','antenna':'Seeed A-02 37.4x17.5mm, coax65mm; RF unmeasured','sources':['https://www.pololu.com/file/0J1031/d24v22fx-step-down-voltage-regulator-dimension-diagram.pdf','https://files.seeedstudio.com/wiki/XIAO_WiFi/antenna/FPC_Antenna_2.4GHz_1.16dbi_for_XIAO_ESP32S3/res/Datasheet_2.4GHz_FPC_Antenna_1.16dbi_for_XIAO_ESP32S3.pdf']}
 return p,sku,note

def battery():
 p={};sku={}
 def put(k,s,stock=None):p[k]=s;sku[k]=stock
 F=np.c_[[0,1,0],[0,0,1],[1,0,0]]
 def along(s):return pose(s,F,[0,0,15])
 hole=along(cyl(11.9,-45.7,45.7));base=box([-53,-15,0],[53,15,17])-hole;cap=box([-53,-15,17],[53,15,29])-hole
 # End plugs never contact the cylindrical body; four screws avoid USB centre.
 for j,(u,v) in enumerate(itertools.product((-49,49),(-10,10))):
  void=(cyl(1.15,10.8,29.1)+hexagon(4.3,12.3,14.1)+box([-3.9,-2.5,12.3],[0,2.5,14.1])).translate([u,v,0]);base-=void;cap-=cyl(1.15,16.9,29.1).translate([u,v,0]);cap-=cyl(2.1,27,29.1).translate([u,v,0]);put('nut_'+str(j),nut(2,4,1.6,12.4).translate([u,v,0]),'NUT_M2');put('screw_'+str(j),screw(2,16,3.8,2,27).translate([u,v,0]),'SCREW_M2_L16')
 # Both ends remain available; choose the supplier's output end after receipt.
 for sign in (-1,1):
  a,b=sorted((sign*44.8,sign*53.1));opening=box([a,-5,10],[b,5,20]);base-=opening;cap-=opening
 put('powerbank',along(cyl(11.4,-45.2,45.2)),'NITECORE_CARBON_6K');put('usb_rightangle',box([45.2,-4,11],[61.2,4,19]),'USB_C_5V_RIGHTANGLE_CABLE');put('base',base);put('cap',cap)
 return p,sku,{'powerbank_cavity_mm':'diameter23.8 x91.4','max_assembled_usb_extension_mm':16,'power':'5V only, no PD trigger. Power switch/cable disconnect external.','material':'PETG prototype; no charging inside holder until temperature verified.'}

if __name__=='__main__':
 for kind,fn in [('controller',controller),('battery',battery)]:
  p,s,n=fn();hh=hits(p);save('equipment/'+kind+'_local.json',{'stock_skus':s,'parts':{k:mesh_record(v) for k,v in p.items()},'findings':hh,'notes':n,'physical_tested':False});np.savez_compressed(OUT/f'equipment/{kind}_local.npz',**{k:tri(v) for k,v in p.items()});print(kind,'hits',hh,flush=True)
