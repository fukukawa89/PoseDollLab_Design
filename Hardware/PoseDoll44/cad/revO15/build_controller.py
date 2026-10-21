"""KiCad-native central scanner carrier C1. Prototype, not hardware-qualified.
Manufacturer pin numbers are explicit; no inherited anonymous connectivity.
XIAO mounts on two 1x7 2.54mm pin strips; buck module is separately wired/retained.
"""
from pathlib import Path
import sys,json,uuid,subprocess,xml.etree.ElementTree as ET
import pcbnew as pcb
H=Path(__file__).resolve().parents[2];R=H.parents[1];OUT=H/'electronics/revO15/central_c1';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(H/'tools'))
import build_regional_revM as legacy
LIB=legacy.LIB;CLI=LIB.parents[1]/'bin/kicad-cli.exe';NAME='PoseDoll_O15_Central_C1'
DEFS={
 'XIAO_S3_HEADER':[(i,n,t) for i,n,t in [(1,'D0_GPIO1','output'),(2,'D1_GPIO2','output'),(3,'D2_GPIO3_STRAP','input'),(4,'D3_GPIO4','output'),(5,'D4_GPIO5','output'),(6,'D5_GPIO6','output'),(7,'D6_GPIO43','output'),(8,'D7_GPIO44','output'),(9,'D8_GPIO7','output'),(10,'D9_GPIO8','input'),(11,'D10_GPIO9','output'),(12,'3V3_MCU','power_out'),(13,'GND','power_in'),(14,'5V_VBUS','power_in')]],
 'TPS2553_1_DBV':[(1,'IN','power_in'),(2,'GND','power_in'),(3,'EN','input'),(4,'FAULT_N','open_collector'),(5,'ILIM','passive'),(6,'OUT','power_out')],
 'LVC1G125_DBV':[(1,'OE_N','input'),(2,'A','input'),(3,'GND','power_in'),(4,'Y','tri_state'),(5,'VCC','power_in')],
}
def custom(name):
 defs=DEFS[name];half=(len(defs)+1)//2;hh=(half+1)*1.27;body=[]
 for j,(n,label,typ) in enumerate(defs):
  side=-1 if j<half else 1;y=(half-1)*1.27-2.54*(j%half);a=0 if side<0 else 180
  body.append(f'(pin {typ} line (at {side*17.78} {y} {a}) (length 5.08) (name "{label}" {legacy.effect()}) (number "{n}" {legacy.effect()}))')
 return f'(symbol "{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 {hh+2.54} 0) {legacy.effect()}) (property "Value" "{name}" (at 0 {hh+5.08} 0) {legacy.effect()}) (symbol "{name}_0_1" (rectangle (start -12.7 {hh}) (end 12.7 {-hh}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol "{name}_1_1" {" ".join(body)}))'
legacy.custom_symbol=custom;legacy.OUT=OUT;legacy.NAME=NAME;legacy.NS=uuid.UUID('9b6fa74b-240c-4653-8c64-a55d6b9e9b15');legacy.comps=[]
C=legacy.comps

def part(ref,lib,sym,value,fp,nets,x,y,angle=0,section='control'):
 return legacy.part(ref,lib,sym,value,fp,nets,(x,y),angle=angle,section=section)

def rr(ref,value,a,b,x,y,angle=0):return part(ref,'Device','R',value,legacy.RFP,{1:a,2:b},x,y,angle)
def cc(ref,value,a,b,x,y):return part(ref,'Device','C',value,legacy.CFP,{1:a,2:b},x,y)
def buf(ref,rail,oe,a,y,xp,yp):return part(ref,'PoseDoll','LVC1G125_DBV','SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:oe,2:a,3:'GND',4:y,5:rail},xp,yp)

def components():
 part('U1','PoseDoll','XIAO_S3_HEADER','Seeed XIAO ESP32S3; 2x 1x7 P2.54 male pin strips','PoseDoll:XIAO_ESP32S3_2x7_PTH',{1:'IO_ENABLE',2:'CS1',3:None,4:'CS2',5:'CS3',6:'CS4',7:'CS5',8:'CS6',9:'SCK',10:'MISO',11:'MOSI',12:'MCU_3V3',13:'GND',14:'MCU_5V'},35,14)
 part('D1','Device','D_Schottky','SS14 / 1A 40V','Diode_SMD:D_SMA',{1:'MCU_5V',2:'VIN_5V'},27.5,28,90)
 part('J7','Connector_Generic','Conn_01x02','5V INPUT ONLY / JST PH 2','Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical',{1:'VIN_5V',2:'GND'},35,55)
 part('J8','Connector_Generic','Conn_01x03','Pololu D24V22F3 harness: GND, VIN5, VOUT3V3','Connector_JST:JST_PH_B3B-PH-SM4-TB_1x03-1MP_P2.00mm_Vertical',{1:'GND',2:'VIN_5V',3:'SENSOR_3V3'},35,43)
 rr('R1','100k','IO_ENABLE','GND',35,28);rr('R2','100k','MISO','MCU_3V3',39,28)
 cc('C1','10u X7R 10V','VIN_5V','GND',30,48);cc('C2','10u X7R 10V','SENSOR_3V3','GND',39,48)
 for i in range(1,7):
  left=i<=3;x=13 if left else 57;y=10+19*((i-1)%3);sg=1 if left else -1;tag=f'P{i}';v=tag+'_3V3';oe=tag+'_OE_N';cs=f'CS{i}';n=i*100
  part(f'J{i}','Connector_Generic','Conn_01x06',f'CHAIN{i} GND,3V3,SCK,MOSI,MISO,CS','Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal',{1:'GND',2:v,3:tag+'_SCK',4:tag+'_MOSI',5:tag+'_MISO',6:tag+'_CS'},5 if left else 65,y,90 if left else -90,tag)
  part(f'U{n}','PoseDoll','TPS2553_1_DBV','TPS2553DBVR-1 / latched-off','Package_TO_SOT_SMD:SOT-23-6',{1:'SENSOR_3V3',2:'GND',3:'SENSOR_3V3',4:tag+'_FAULT_N',5:tag+'_ILIM',6:v},x+sg*7,y-5.5)
  rr(f'R{n}','88.7k 1%',tag+'_ILIM','GND',x+sg*7,y-2)
  cc(f'C{n}','100n X7R 10V','SENSOR_3V3','GND',x+sg*3,y-7)
  cc(f'C{n+1}','1u X7R 10V',v,'GND',x-sg*2,y-7)
  rr(f'R{n+1}','47k',v,oe,x+sg*9,y+2)
  part(f'Q{i}','Transistor_FET','2N7002','2N7002','Package_TO_SOT_SMD:SOT-23',{1:'IO_ENABLE',2:'GND',3:oe},x+sg*8,y+6)
  rr(f'R{n+2}','10k','MCU_3V3',cs,x+sg*4,y+8)
  for j,(a,sig) in enumerate([('SCK','SCK'),('MOSI','MOSI'),(cs,'CS')]):
   yy=y-4+j*4;buf(f'U{n+1+j}',v,oe,a,tag+'_'+sig+'_DRV',x,yy)
   rr(f'R{n+3+j}','100R',tag+'_'+sig+'_DRV',tag+'_'+sig,x-sg*4,yy)
  buf(f'U{n+4}','MCU_3V3',cs,tag+'_MISO','MISO',x+sg*5,y+1.5)
  rr(f'R{n+6}','100k',tag+'_MISO','GND',x+sg*5,y-2)
  rr(f'R{n+7}','10k',v,tag+'_CS',x-sg*4,y+7)
  rr(f'R{n+8}','47k',tag+'_SCK','GND',x-sg*4,y-6)
  rr(f'R{n+9}','47k',tag+'_MOSI','GND',x-sg*4,y+5)
  cc(f'C{n+2}','100n X7R 10V',v,'GND',x+sg*4,y-5)
  cc(f'C{n+3}','100n X7R 10V','MCU_3V3','GND',x+sg*5,y+5)
  cc(f'C{n+4}','100n X7R 10V',v,'GND',x+sg*2,y)
  cc(f'C{n+5}','100n X7R 10V',v,'GND',x+sg*2,y+4)
  rr(f'R{n+10}','47k','SENSOR_3V3',tag+'_FAULT_N',x+sg*8,y+9)
  part(f'TP{i}','Connector','TestPoint',tag+'_FAULT_N','TestPoint:TestPoint_Pad_D1.0mm',{1:tag+'_FAULT_N'},x+sg*10,y-1)
 for i,net in enumerate(['GND','VIN_5V','MCU_5V','SENSOR_3V3']):part(f'#FLG{i+1}','power','PWR_FLAG','PWR_FLAG','',{1:net},0,0)
 return C

def footprint():
 folder=OUT/'PoseDoll.pretty';folder.mkdir(exist_ok=True);f=pcb.FOOTPRINT(None);f.SetFPID(pcb.LIB_ID('PoseDoll','XIAO_ESP32S3_2x7_PTH'));f.SetAttributes(pcb.FP_THROUGH_HOLE)
 for i in range(14):
  n=i+1;x=-7.62 if n<=7 else 7.62;y=-7.62+(n-1 if n<=7 else 14-n)*2.54
  p=pcb.PAD(f);p.SetNumber(str(n));p.SetAttribute(pcb.PAD_ATTRIB_PTH);p.SetShape(pcb.PAD_SHAPE_RECT if n==1 else pcb.PAD_SHAPE_CIRCLE);p.SetSize(pcb.VECTOR2I(pcb.FromMM(1.8),pcb.FromMM(1.8)));p.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(1),pcb.FromMM(1)));layers=pcb.LSET.AllCuMask();layers.AddLayer(pcb.F_Mask);layers.AddLayer(pcb.B_Mask);p.SetLayerSet(layers);p.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));f.Add(p)
 for layer,rect in [(pcb.F_Fab,(-8.89,-10.5,8.89,10.5)),(pcb.F_CrtYd,(-9.4,-12.1,9.4,11.1))]:
  x0,y0,x1,y1=rect
  for a,b in zip([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],[(x1,y0),(x1,y1),(x0,y1),(x0,y0)]):
   g=pcb.PCB_SHAPE(f);g.SetShape(pcb.SHAPE_T_SEGMENT);g.SetLayer(layer);g.SetWidth(pcb.FromMM(.05));g.SetStart(pcb.VECTOR2I(*[pcb.FromMM(t) for t in a]));g.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(t) for t in b]));f.Add(g)
 pcb.PCB_IO_KICAD_SEXPR().FootprintSave(str(folder),f)
 libs={'PoseDoll',*[c['fp'].split(':')[0] for c in C if c['fp']]}
 (OUT/'fp-lib-table').write_text('(fp_lib_table '+''.join(f'(lib (name "{lib}") (type "KiCad") (uri "'+('${KIPRJMOD}/PoseDoll.pretty' if lib=='PoseDoll' else str(LIB/'footprints'/(lib+'.pretty')).replace('\\','/'))+'") (options "") (descr ""))' for lib in sorted(libs))+')')

def board(root):
 subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(OUT/'netlist.xml'),str(OUT/(NAME+'.kicad_sch'))],check=True)
 b=pcb.BOARD();b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(pcb.FromMM(1.2));nets={};netmap={}
 for el in ET.parse(OUT/'netlist.xml').findall('./nets/net'):
  net=pcb.NETINFO_ITEM(b,el.attrib['name'],int(el.attrib['code']));b.Add(net);nets[el.attrib['name']]=net
  for n in el.findall('node'):netmap[(n.attrib['ref'],n.attrib['pin'])]=net
 for c in C:
  if not c['fp']:continue
  lib,fp=c['fp'].split(':');folder=OUT/'PoseDoll.pretty' if lib=='PoseDoll' else LIB/'footprints'/(lib+'.pretty');f=pcb.FootprintLoad(str(folder),fp);assert f,c['fp']
  f.SetFPID(pcb.LIB_ID(lib,fp));f.SetReference(c['ref']);f.SetValue(c['value']);f.SetPosition(pcb.VECTOR2I(*[pcb.FromMM(v) for v in c['pcb']]));f.SetOrientationDegrees(c['angle']);b.Add(f)
  if c['ref']!='U1':
   boxes=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==pcb.F_CrtYd]
   if boxes:
    dx=(min(bb.GetLeft() for bb in boxes)+max(bb.GetRight() for bb in boxes))//2;dy=(min(bb.GetTop() for bb in boxes)+max(bb.GetBottom() for bb in boxes))//2;f.SetPosition(f.GetPosition()-(pcb.VECTOR2I(dx,dy)-f.GetPosition()))
  pp=pcb.KIID_PATH();pp.push_back(pcb.KIID(root));pp.push_back(pcb.KIID(legacy.uid(c['ref'])));f.SetPath(pp)
  for pad in f.Pads():
   net=netmap.get((c['ref'],pad.GetNumber()))
   if net:pad.SetNet(net)
  f.Value().SetVisible(False);f.Reference().SetVisible(False)
 for j,(x,y) in enumerate([(11,3),(59,3),(3,57),(67,57)],1):
  f=pcb.FootprintLoad(str(LIB/'footprints/MountingHole.pretty'),'MountingHole_2.2mm_M2');f.SetReference('H'+str(j));f.SetAttributes(f.GetAttributes()|pcb.FP_BOARD_ONLY);f.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));f.Value().SetVisible(False);f.Reference().SetVisible(False);b.Add(f)
 pack(b)
 for a,z in zip([(0,0),(70,0),(70,60),(0,60)],[(70,0),(70,60),(0,60),(0,0)]):
  g=pcb.PCB_SHAPE();g.SetShape(pcb.SHAPE_T_SEGMENT);g.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]));g.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in z]));g.SetLayer(pcb.Edge_Cuts);g.SetWidth(pcb.FromMM(.05));b.Add(g)
 pro=json.loads((H/'electronics/sensor_revB/PoseDoll_AS5048A_revB.kicad_pro').read_text());pro['meta']['filename']=NAME+'.kicad_pro';rules=pro['board']['design_settings']['rules'];rules.update(min_track_width=.15,min_clearance=.15,min_copper_edge_clearance=.3,min_through_hole_diameter=.3)
 pro['net_settings']['classes'][0].update(track_width=.2,clearance=.2,via_diameter=.65,via_drill=.3)
 (OUT/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2));pcb.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),b)
 (OUT/'connectivity.json').write_text(json.dumps(C,indent=2));print('PLACEMENT',len(C),'components',len(nets),'nets')
 return b

def pack(b):
 # Place real library courtyards; do not reduce dimensions to make a part fit.
 def rectangle(f):
  layer=pcb.B_CrtYd if f.IsFlipped() else pcb.F_CrtYd
  bb=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
  if not bb:bb=[f.GetBoundingBox(False,False)]
  return [min(v.GetLeft() for v in bb),min(v.GetTop() for v in bb),max(v.GetRight() for v in bb),max(v.GetBottom() for v in bb)]
 fixed=[];mov=[];placed=[]
 for f in b.GetFootprints():
  ref=f.GetReference()
  if ref=='U1' or ref.startswith(('J','H')):fixed.append(f)
  else:mov.append(f)
  if ref.startswith(('R','C','TP')):f.Flip(f.GetPosition(),False)
 for f in fixed:
  r=rectangle(f);layers={0,1} if any(p.GetAttribute() in (pcb.PAD_ATTRIB_PTH,pcb.PAD_ATTRIB_NPTH) for p in f.Pads()) else {int(f.IsFlipped())}
  placed.append((r,layers,f.GetReference()))
 margin=pcb.FromMM(.2);lo=pcb.FromMM(.4);hi=pcb.FromMM(69.6);bottom=pcb.FromMM(59.6)
 mov.sort(key=lambda f:-(rectangle(f)[2]-rectangle(f)[0])*(rectangle(f)[3]-rectangle(f)[1]))
 for f in mov:
  ref=f.GetReference();r=rectangle(f);center=f.GetPosition();half=[(r[2]-r[0])/2,(r[3]-r[1])/2];cx=(r[0]+r[2])/2;cy=(r[1]+r[3])/2;side=int(f.IsFlipped());found=None
  steps=sorted(((x,y) for x in range(-30,31) for y in range(-30,31)),key=lambda v:v[0]*v[0]+v[1]*v[1])
  for dx,dy in steps:
   xx=cx+pcb.FromMM(dx*.5);yy=cy+pcb.FromMM(dy*.5);rr=[xx-half[0],yy-half[1],xx+half[0],yy+half[1]]
   if rr[0]<lo or rr[1]<lo or rr[2]>hi or rr[3]>bottom:continue
   if any(side in layers and min(rr[2],q[2])+margin>max(rr[0],q[0]) and min(rr[3],q[3])+margin>max(rr[1],q[1]) for q,layers,_ in placed):continue
   found=(xx-cx,yy-cy,rr);break
  if found is None:raise ValueError(('no courtyard placement',ref))
  dx,dy,rr=found;f.SetPosition(center+pcb.VECTOR2I(round(dx),round(dy)));placed.append((rr,{side},ref))
 (OUT/'placement_courtyards.json').write_text(json.dumps([dict(ref=ref,bounds_mm=[pcb.ToMM(int(t)) for t in bb],layers=list(layers)) for bb,layers,ref in placed],indent=2))

if __name__=='__main__':
 components();footprint();root=legacy.schematic();b=board(root)
 subprocess.run([str(CLI),'sch','erc','--format','json','-o',str(OUT/'erc.json'),str(OUT/(NAME+'.kicad_sch'))],check=True)
 subprocess.run([str(CLI),'pcb','drc','--format','json','-o',str(OUT/'drc_placement.json'),str(OUT/(NAME+'.kicad_pcb'))],check=True)
