"""O21 native circuits: SOP8 sensor trial; central schematic, not a fabrication release."""
from pathlib import Path
import sys,json,uuid,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';B=H/'bench/revO21'
sys.path.insert(0,str(H/'tools'))
import pcbnew as pcb
import build_regional_revM as k
import route_revo5cn_sensor as router
CLI=k.LIB.parents[1]/'bin/kicad-cli.exe'
def put(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def v(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
defs={
 'MT6701CT':{1:('VDD','power_in'),2:('MODE','input'),3:('OUT','output'),4:('GND','power_in'),5:('PUSH','output'),6:('DO','bidirectional'),7:('CLK','input'),8:('CSN','input')},
 'MUX4067':{**{p:(f'I{i}','passive') for i,p in enumerate([9,8,7,6,5,4,3,2,23,22,21,20,19,18,17,16])},1:('COM','passive'),10:('S0','input'),11:('S1','input'),12:('GND','power_in'),13:('S3','input'),14:('S2','input'),15:('E','input'),24:('VCC','power_in')},
 'LVC244':{**{p:(f'A{i}','input') for i,p in enumerate([2,4,6,8,11,13,15,17])},**{p:(f'Y{i}','tri_state') for i,p in enumerate([18,16,14,12,9,7,5,3])},1:('OE1_N','input'),19:('OE2_N','input'),10:('GND','power_in'),20:('VCC','power_in')},
 'LVC125':{1:('OE1_N','input'),2:('A1','input'),3:('Y1','tri_state'),4:('OE2_N','input'),5:('A2','input'),6:('Y2','tri_state'),7:('GND','power_in'),8:('Y3','tri_state'),9:('A3','input'),10:('OE3_N','input'),11:('Y4','tri_state'),12:('A4','input'),13:('OE4_N','input'),14:('VCC','power_in')},
 'AP3429A':{1:('EN','input'),2:('GND','power_in'),3:('LX','output'),4:('VIN','power_in'),5:('FB','input')}}
def symbol(name):
 d=defs[name];half=(len(d)+1)//2;hh=(half+1)*1.27;pins=[]
 for j,(num,(label,typ)) in enumerate(sorted(d.items())):
  side=-1 if j<half else 1;y=(half-1)*1.27-2.54*(j%half)
  pins.append(f'(pin {typ} line (at {side*17.78} {y} {0 if side<0 else 180}) (length 5.08) (name "{label}" {k.effect()}) (number "{num}" {k.effect()}))')
 return f'(symbol "{name}" (pin_names (offset .5)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 {hh+2.54} 0) {k.effect()}) (property "Value" "{name}" (at 0 {hh+5.08} 0) {k.effect()}) (symbol "{name}_0_1" (rectangle (start -12.7 {hh}) (end 12.7 {-hh}) (stroke (width .254) (type default)) (fill (type background)))) (symbol "{name}_1_1" '+''.join(pins)+'))'
def setup(folder,name):
 k.OUT=B/'electronics'/folder;k.OUT.mkdir(parents=True,exist_ok=True);k.NAME=name;k.NS=uuid.uuid5(uuid.NAMESPACE_URL,'posedoll/o21/'+name);k.comps=[];k.custom_symbol=symbol
def flag(n,net):k.part('#FLG'+str(n),'power','PWR_FLAG','PWR_FLAG','',{1:net},(0,0))
def check(kind):
 args=['sch','erc'] if kind=='erc' else ['pcb','drc','--schematic-parity','--all-track-errors'];suffix='.kicad_sch' if kind=='erc' else '.kicad_pcb'
 proc=subprocess.run([str(CLI),*args,'--format','json','--severity-all','-o',str(k.OUT/(kind+'.json')),str(k.OUT/(k.NAME+suffix))],capture_output=True)
 (k.OUT/(kind+'.txt')).write_bytes(proc.stdout+proc.stderr);d=json.loads((k.OUT/(kind+'.json')).read_text())
 issues=d.get('violations',[])+[v for sh in d.get('sheets',[]) for v in sh.get('violations',[])]
 return {'exit':proc.returncode,'violations':len(issues),'unconnected':len(d.get('unconnected_items',[])),'pass':not issues and not d.get('unconnected_items',[]) and proc.returncode==0}
def sensor():
 setup('sensor','PoseDoll_O21_MT6701CT');folder=k.OUT/'PoseDoll.pretty';folder.mkdir(exist_ok=True)
 f=pcb.FOOTPRINT(None);f.SetFPID(pcb.LIB_ID('PoseDoll','WirePads_5P'));f.SetAttributes(pcb.FP_SMD)
 for i in range(5):
  p=pcb.PAD(f);p.SetNumber(str(i+1));p.SetAttribute(pcb.PAD_ATTRIB_SMD);p.SetShape(pcb.PAD_SHAPE_RECT);p.SetPosition(v((i-2)*1.27,0));p.SetSize(v(.85,1.1))
  layers=pcb.LSET();layers.AddLayer(pcb.F_Cu);layers.AddLayer(pcb.F_Mask);p.SetLayerSet(layers);f.Add(p)
 for a,b in zip([(-3.2,-.8),(3.2,-.8),(3.2,.8),(-3.2,.8)],[(3.2,-.8),(3.2,.8),(-3.2,.8),(-3.2,-.8)]):
  q=pcb.PCB_SHAPE(f);q.SetShape(pcb.SHAPE_T_SEGMENT);q.SetStart(v(*a));q.SetEnd(v(*b));q.SetLayer(pcb.F_CrtYd);q.SetWidth(pcb.FromMM(.05));f.Add(q)
 pcb.PCB_IO_MGR.FindPlugin(pcb.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(folder),f)
 k.part('U1','PoseDoll','MT6701CT','MT6701CT-STD-R','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',{1:'+3V3',2:'+3V3',3:None,4:'GND',5:None,6:'DO_IC',7:'CLK',8:'CS_N'},(100,100))
 k.part('J1','Connector_Generic','Conn_01x05','FACTORY_SOLDERED_5_CORE','PoseDoll:WirePads_5P',{1:'GND',2:'+3V3',3:'CLK',4:'DO',5:'CS_N'},(100,104.05))
 k.capacitor('C1','100n X7R 16V','+3V3','GND',(100,96.1));k.capacitor('C2','1u X7R 16V','+3V3','GND',(95.3,100),angle=90)
 k.resistor('R1','33R','DO_IC','DO',(104.65,102.1),angle=90);k.resistor('R2','10k','+3V3','CS_N',(104.65,97.5),angle=90)
 flag(1,'+3V3');flag(2,'GND');rid=k.schematic();k.board(rid)
 b=pcb.LoadBoard(str(k.OUT/'placement.kicad_pcb'));b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(pcb.FromMM(1))
 for s in list(b.GetDrawings()):
  if s.GetLayer()==pcb.Edge_Cuts:b.Remove(s)
 points=[(95,95),(105,95),(106,96),(106,104),(105,105),(95,105),(94,104),(94,96)]
 for a,z in zip(points,points[1:]+points[:1]):
  s=pcb.PCB_SHAPE();s.SetShape(pcb.SHAPE_T_SEGMENT);s.SetStart(v(*a));s.SetEnd(v(*z));s.SetWidth(pcb.FromMM(.05));s.SetLayer(pcb.Edge_Cuts);b.Add(s)
 pcb.SaveBoard(str(k.OUT/'placement.kicad_pcb'),b)
 pro=json.loads((k.OUT/(k.NAME+'.kicad_pro')).read_text());pro['board']['design_settings']['rules'].update(min_through_hole_diameter=.3,min_copper_edge_clearance=.25)
 for n in [k.NAME,'placement']:put(k.OUT/(n+'.kicad_pro'),pro)
 libs=sorted({c['fp'].split(':')[0] for c in k.comps if c['fp']})
 (k.OUT/'fp-lib-table').write_text('(fp_lib_table '+''.join('(lib (name "'+n+'") (type KiCad) (uri "'+('$'+'{KIPRJMOD}/PoseDoll.pretty' if n=='PoseDoll' else '$'+'{KICAD10_FOOTPRINT_DIR}/'+n+'.pretty')+'") (options "") (descr ""))' for n in libs)+')',encoding='utf-8')
 attempts=[];ok=False
 for order in ['DO_IC,DO,CLK,CS_N,+3V3,GND','CLK,CS_N,DO_IC,DO,+3V3,GND','+3V3,GND,CLK,CS_N,DO_IC,DO']:
  trial=pcb.LoadBoard(str(k.OUT/'placement.kicad_pcb'));os.environ['PD44_ROUTE_ORDER']=order
  try:router.route(trial);b=trial;ok=True;attempts.append({'order':order,'success':True});break
  except RuntimeError as e:attempts.append({'order':order,'error':str(e)})
 pcb.SaveBoard(str(k.OUT/(k.NAME+'.kicad_pcb')),b);put(k.OUT/(k.NAME+'.kicad_pro'),pro)
 checks={'erc':check('erc'),'drc':check('drc')}
 put(k.OUT/'result.json',{'routing_completed':ok,'checks':checks,'attempts':attempts,'single_side_components':True,'outline_mm':[12,10,1],'manufacturing_released':False,'new_magnet_gap_validated':False})
 print('SENSOR',checks,attempts,flush=True)
def carrier():
 setup('carrier','PoseDoll_O21_SSI_Carrier')
 k.part('J1','Connector_Generic','Conn_01x07','XIAO_LEFT D0-D6','Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical',{1:'EN_MCU',2:'A0_MCU',3:None,4:'A1_MCU',5:'A2_MCU',6:'A3_MCU',7:'CS_MCU'},(0,0))
 k.part('J2','Connector_Generic','Conn_01x07','XIAO_RIGHT D7-D10,3V3,GND,5V NC','Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical',{1:'DO_C_MCU',2:'CLK_MCU',3:'DO_A_MCU',4:'DO_B_MCU',5:'MCU_3V3',6:'GND',7:None},(0,0))
 inputs=['CLK_MCU']*3+['CS_MCU']*3+[f'A{i}_MCU' for i in range(4)]
 outputs=[f'CLK_{a}_DRV' for a in 'ABC']+[f'CS_{a}_DRV' for a in 'ABC']+[f'A{i}' for i in range(4)]
 pi=[2,4,6,8,11,13,15,17];po=[18,16,14,12,9,7,5,3]
 for j in range(2):
  nets={1:'ENABLE_N',19:'ENABLE_N',10:'GND',20:'SENSOR_3V3'}
  for z in range(8):
   t=j*8+z;nets[pi[z]]=inputs[t] if t<len(inputs) else 'GND';nets[po[z]]=outputs[t] if t<len(outputs) else None
  k.part(f'U{j+1}','PoseDoll','LVC244','SN74LVC244APWR','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',nets,(0,0));k.capacitor(f'C{j+1}','100n','SENSOR_3V3','GND',(0,0))
 k.part('Q1','Transistor_FET','2N7002','2N7002','Package_TO_SOT_SMD:SOT-23',{1:'EN_MCU',2:'GND',3:'ENABLE_N'},(0,0))
 k.resistor('R1','100k','EN_MCU','GND',(0,0));k.resistor('R2','10k','ENABLE_N','SENSOR_3V3',(0,0))
 for i,net in enumerate(sorted(set(inputs))):k.resistor(f'R{10+i}','100k',net,'GND',(0,0))
 for j,a in enumerate('ABC'):
  for i,s in enumerate(['CLK','CS']):k.resistor(f'R{30+2*j+i}','33R candidate',f'{s}_{a}_DRV',f'{s}_{a}',(0,0))
  k.resistor(f'R{40+j}','10k',f'DO_{a}','SENSOR_3V3',(0,0))
  nets={1:f'DO_{a}',10:'A0',11:'A1',13:'A3',14:'A2',15:'ENABLE_N',12:'GND',24:'SENSOR_3V3'}
  for i,pin in enumerate([9,8,7,6,5,4,3,2,23,22,21,20,19,18,17,16]):nets[pin]=f'{a}{i+1:02}_DO' if j!=0 or i<14 else 'GND'
  k.part(f'U{3+j}','PoseDoll','MUX4067','CD74HC4067PW','Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm',nets,(0,0));k.capacitor(f'C{3+j}','100n','SENSOR_3V3','GND',(0,0))
  for i in range(14 if j==0 else 16):
   k.part(f'J{10+j*16+i}','Connector_Generic','Conn_01x05',f'{a}{i+1:02} matched SH 5P keyed','Connector_JST:JST_SH_BM05B-SRSS-TB_1x05-1MP_P1.00mm_Vertical',{1:'GND',2:'SENSOR_3V3',3:f'CLK_{a}',4:f'{a}{i+1:02}_DO',5:f'CS_{a}'},(0,0))
 k.part('U6','PoseDoll','LVC125','SN74LVC125APWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm',{1:'GND',2:'DO_A',3:'DO_A_MCU',4:'GND',5:'DO_B',6:'DO_B_MCU',7:'GND',8:'DO_C_MCU',9:'DO_C',10:'GND',11:None,12:'GND',13:'MCU_3V3',14:'MCU_3V3'},(0,0))
 k.capacitor('C6','100n','MCU_3V3','GND',(0,0))
 k.part('J3','Connector_Generic','Conn_01x02','EXTERNAL REGULATED 5V ONLY; NO USB VBUS TIE','Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical',{1:'EXT5V',2:'GND'},(0,0))
 k.part('F4','Device','Polyfuse','1.1A input; MPN qualification pending','Fuse:Fuse_1812_4532Metric',{1:'EXT5V',2:'FUSED5V'},(0,0))
 k.part('D1','Device','D_Schottky','SS14 input reverse protection','Diode_SMD:D_SMA',{1:'VIN',2:'FUSED5V'},(0,0))
 k.part('U7','PoseDoll','AP3429A','AP3429AW5-7','Package_TO_SOT_SMD:TSOT-23-5',{1:'VIN',2:'GND',3:'LX',4:'VIN',5:'FB'},(0,0))
 k.part('L1','Device','L','2.2uH Isat >=3.5A DCR <=100mOhm','Inductor_SMD:L_Taiyo-Yuden_NR-40xx',{1:'LX',2:'REG_3V3'},(0,0))
 k.capacitor('C7','22u 10V X7R effective >=10u','VIN','GND',(0,0),fp='Capacitor_SMD:C_0805_2012Metric')
 for i in [8,9]:k.capacitor(f'C{i}','22u 10V X7R effective >=10u','REG_3V3','GND',(0,0),fp='Capacitor_SMD:C_0805_2012Metric')
 k.resistor('R50','300k 1%','REG_3V3','FB',(0,0));k.resistor('R51','66.5k 1%','FB','GND',(0,0));k.capacitor('C10','22p C0G starting value','REG_3V3','FB',(0,0))
 k.part('F5','Device','Fuse','1A fast Rmax<=0.15 ohm; exact MPN pending','Fuse:Fuse_1206_3216Metric',{1:'REG_3V3',2:'SENSOR_3V3'},(0,0))
 for i,net in enumerate(['GND','MCU_3V3','EXT5V','VIN','SENSOR_3V3'],1):flag(i,net)
 k.schematic()
 subprocess.run([str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(k.OUT/'netlist.xml'),str(k.OUT/(k.NAME+'.kicad_sch'))],check=True,capture_output=True)
 put(k.OUT/'components.json',k.comps)
 checks={'erc':check('erc')}
 put(k.OUT/'result.json',{'checks':checks,'schematic_only':True,'pcb_routed':False,'manufacturing_released':False,'scope':'IC pin maps fixed; connector family, XIAO spacing, fuse MPN, rail layout/thermal, enclosure remain to qualify. Header order is logical, not PCB placement.'})
 print('CARRIER',checks,flush=True)
if __name__=='__main__':sensor();carrier()
