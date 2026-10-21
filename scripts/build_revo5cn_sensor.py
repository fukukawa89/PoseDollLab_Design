"""Independent O5CN KiCad sensor trial. No old board or firmware is rewritten.
Run with KiCad's Python. Source drawings and unknown EP behavior are explicit.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,os,uuid
R=Path(__file__).resolve().parents[1];HW=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(HW/'tools'))
import pcbnew as pcb
import build_regional_revM as legacy
import route_revo5cn_sensor as router
OUT=HW/'electronics/sensor_revO5CN';OUT.mkdir(parents=True,exist_ok=True)
NAME='PoseDoll_MT6701_CJT_CN1';LIB=legacy.LIB;CLI=LIB.parents[1]/'bin/kicad-cli.exe'
INPUTS=[Path(__file__),HW/'mechanical_manifest/requirements_revO5CN.json',HW/'references/revO5CN/downloaded_sources.json',HW/'tools/build_regional_revM.py',HW/'tools/build_sensor_revC_mini.py',R/'scripts/route_revo5cn_sensor.py',HW/'electronics/sensor_revB/PoseDoll_AS5048A_revB.kicad_pro']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def v(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def footprint(name,pads,body,cy):
 f=pcb.FOOTPRINT(None);f.SetFPID(pcb.LIB_ID('PoseDoll',name));f.SetAttributes(pcb.FP_SMD)
 for number,x,y,w,h in pads:
  pad=pcb.PAD(f);pad.SetNumber(str(number));pad.SetAttribute(pcb.PAD_ATTRIB_SMD);pad.SetShape(pcb.PAD_SHAPE_RECT);pad.SetPosition(v(x,y));pad.SetSize(v(w,h));layers=pcb.LSET();layers.AddLayer(pcb.F_Cu);layers.AddLayer(pcb.F_Paste);layers.AddLayer(pcb.F_Mask);pad.SetLayerSet(layers);f.Add(pad)
 for bounds,layer,width in [(body,pcb.F_Fab,.1),(cy,pcb.F_CrtYd,.05)]:
  x0,y0,x1,y1=bounds;pts=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
  for a,b in zip(pts,pts[1:]+pts[:1]):
   line=pcb.PCB_SHAPE(f);line.SetShape(pcb.SHAPE_T_SEGMENT);line.SetStart(v(*a));line.SetEnd(v(*b));line.SetLayer(layer);line.SetWidth(pcb.FromMM(width));f.Add(line)
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 pcb.PCB_IO_MGR.FindPlugin(pcb.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(OUT/'PoseDoll.pretty'),f)
 return f

def custom_symbol(name):
 assert name=='MT6701QT_TRIAL'
 defs={1:('NC','no_connect'),2:('NC','no_connect'),3:('NC','no_connect'),4:('NC','no_connect'),5:('PUSH','output'),6:('DO','output'),7:('CLK','input'),8:('CSN','input'),9:('W','output'),10:('NC','no_connect'),11:('U','output'),12:('V','output'),13:('VDD','power_in'),14:('MODE','input'),15:('OUT','output'),16:('GND','power_in'),17:('EP_UNSPECIFIED','passive')}
 body=[]
 for i,(number,(label,typ)) in enumerate(defs.items()):
  side=-1 if i<9 else 1;y=10.16-2.54*(i%9)
  body.append(f'(pin {typ} line (at {side*17.78} {y} {0 if side<0 else 180}) (length 5.08) (name "{label}" {legacy.effect()}) (number "{number}" {legacy.effect()}))')
 return f'(symbol "{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 15 0) {legacy.effect()}) (property "Value" "{name}" (at 0 18 0) {legacy.effect()}) (symbol "{name}_0_1" (rectangle (start -12.7 12.7) (end 12.7 -12.7) (stroke (width .254) (type default)) (fill (type background)))) (symbol "{name}_1_1" '+''.join(body)+'))'

def main():
 folder=OUT/'PoseDoll.pretty';folder.mkdir(exist_ok=True)
 # p35 mechanical package, custom proposed land pattern, not supplier-released.
 pads=[]
 for j in range(4):
  pads.extend([(1+j,-1.4,-.75+.5*j,.65,.25),(5+j,-.75+.5*j,1.4,.25,.65),(9+j,1.4,.75-.5*j,.65,.25),(13+j,.75-.5*j,-1.4,.25,.65)])
 pads.append((17,0,0,1.8,1.8))
 footprint('MT6701QT_QFN16_EP_UNSPECIFIED',pads,(-1.55,-1.55,1.55,1.55),(-2,-2,2,2))
 # CJT A1002WR-S-XP-LCP A3, PCB layout drawing, five positions.
 jp=[(i+1,i-2,-2.0,.6,1.55) for i in range(5)]+[('',-3.3,1.875,1.2,1.8),('',3.3,1.875,1.2,1.8)]
 footprint('CJT_A1002WR_S_5P_LCP',jp,(-3.5,-1.9,3.5,2.5),(-4.2,-3.05,4.2,3.05))
 legacy.OUT=OUT;legacy.NAME=NAME;legacy.NS=uuid.UUID('6e28aff3-24d3-4815-ab4b-93e90cba274d');legacy.custom_symbol=custom_symbol;legacy.comps=[]
 nets={i:None for i in range(1,18)};nets.update({6:'DO_IC',7:'CLK',8:'CS_N',13:'+3V3',14:'+3V3',16:'GND'})
 legacy.part('U1','PoseDoll','MT6701QT_TRIAL','MT6701QT-STD / EP unresolved','PoseDoll:MT6701QT_QFN16_EP_UNSPECIFIED',nets,(100,100))
 legacy.part('J1','Connector_Generic','Conn_01x05','A1002WR-S-5P-LCP / CN1 FIVE-WIRE ONLY','PoseDoll:CJT_A1002WR_S_5P_LCP',{1:'GND',2:'+3V3',3:'CLK',4:'DO',5:'CS_N'},(100,100),back=True)
 legacy.capacitor('C1','100n X7R','+3V3','GND',(102.8,96.6))
 legacy.capacitor('C2','10u bulk; derating pending','+3V3','GND',(102.6,103.6),fp='Capacitor_SMD:C_0805_2012Metric')
 legacy.resistor('R1','33R source damping candidate','DO_IC','DO',(97.4,96.6))
 legacy.resistor('R2','10k CS safe high','+3V3','CS_N',(97.4,103.6))
 legacy.part('#FLG01','power','PWR_FLAG','PWR_FLAG','',{1:'+3V3'},(0,0))
 legacy.part('#FLG02','power','PWR_FLAG','PWR_FLAG','',{1:'GND'},(0,0))
 for c in legacy.comps:
  if c['lib']!='PoseDoll':INPUTS.append(LIB/'symbols'/(c['lib']+'.kicad_sym'))
  if c['fp'] and not c['fp'].startswith('PoseDoll:'):
   lib,f=c['fp'].split(':');INPUTS.append(LIB/'footprints'/(lib+'.pretty')/(f+'.kicad_mod'))
 hashes={str(p.relative_to(R)) if p.is_relative_to(R) else str(p):sha(p) for p in INPUTS}
 rid=legacy.schematic();legacy.board(rid)
 b=pcb.LoadBoard(str(OUT/'placement.kicad_pcb'));b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(pcb.FromMM(1.0))
 for s in list(b.GetDrawings()):
  if s.GetLayer()==pcb.Edge_Cuts:b.Remove(s)
 pts=[(95,95),(105,95),(106,96),(106,104),(105,105),(95,105),(94,104),(94,96)]
 for a,z in zip(pts,pts[1:]+pts[:1]):
  q=pcb.PCB_SHAPE();q.SetShape(pcb.SHAPE_T_SEGMENT);q.SetStart(v(*a));q.SetEnd(v(*z));q.SetLayer(pcb.Edge_Cuts);q.SetWidth(pcb.FromMM(.05));b.Add(q)
 pcb.SaveBoard(str(OUT/'placement.kicad_pcb'),b)
 libs=sorted({c['fp'].split(':')[0] for c in legacy.comps if c['fp']})
 (OUT/'fp-lib-table').write_text('(fp_lib_table '+''.join('(lib (name "'+k+'") (type KiCad) (uri "'+('${KIPRJMOD}/PoseDoll.pretty' if k=='PoseDoll' else '${KICAD10_FOOTPRINT_DIR}/'+k+'.pretty')+'") (options "") (descr ""))' for k in libs)+')',encoding='utf-8')
 pro=json.loads((OUT/(NAME+'.kicad_pro')).read_text());pro['board']['design_settings']['rules'].update(min_copper_edge_clearance=.25,min_track_width=.15,min_clearance=.15,min_through_hole_diameter=.3);pro['net_settings']['classes'][0].update(track_width=.15,clearance=.15)
 save(OUT/(NAME+'.kicad_pro'),pro);save(OUT/'placement.kicad_pro',pro)
 # Explicit unresolved EP remains an isolated pad; no invented connection to GND.
 orders=['DO_IC,DO,CLK,CS_N,+3V3,GND','+3V3,GND,DO_IC,DO,CLK,CS_N','CS_N,CLK,DO_IC,DO,+3V3,GND']
 attempts=[];route_ok=False
 for order in orders:
  trial=pcb.LoadBoard(str(OUT/'placement.kicad_pcb'));os.environ['PD44_ROUTE_ORDER']=order
  try:
   log=router.route(trial);b=trial;route_ok=True;attempts.append({'order':order,'routed':True,'connections':log});break
  except RuntimeError as e:attempts.append({'order':order,'routed':False,'error':str(e)})
 pcb.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),b)
 # pcbnew SaveBoard may also write the project loaded by LoadBoard. Reapply declared rules after saving.
 save(OUT/(NAME+'.kicad_pro'),pro);save(OUT/'placement.kicad_pro',pro)
 checks={}
 for what,args in [('erc',['sch','erc']),('drc',['pcb','drc','--schematic-parity','--all-track-errors'])]:
  source=OUT/(NAME+('.kicad_sch' if what=='erc' else '.kicad_pcb'));dest=OUT/(what+'.json')
  cmd=[str(CLI),*args,'--format','json','--severity-all','-o',str(dest),str(source)]
  proc=subprocess.run(cmd,capture_output=True);(OUT/(what+'.txt')).write_bytes(proc.stdout+proc.stderr)
  d=json.loads(dest.read_text());issues=d.get('violations',[])+[v for sheet in d.get('sheets',[]) for v in sheet.get('violations',[])]
  checks[what]={'exit':proc.returncode,'violations':len(issues),'unconnected':len(d.get('unconnected_items',[])),'by_type':{k:sum(x.get('type')==k for x in issues) for k in sorted({x.get('type') for x in issues})},'pass':proc.returncode==0 and not issues and not d.get('unconnected_items',[])}
 pads=[{'ref':f.GetReference(),'pin':p.GetNumber(),'net':p.GetNetname(),'xy_mm':[pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y)],'size_mm':[pcb.ToMM(p.GetSize().x),pcb.ToMM(p.GetSize().y)],'back':p.IsOnLayer(pcb.B_Cu)} for f in b.GetFootprints() for p in f.Pads()]
 for k,h in hashes.items():assert sha(R/k if not Path(k).is_absolute() else Path(k))==h,k
 report={'schema':'cn1-sensor-pcb-v1','board_mm':[12,10,1],'baseline_board_area_reduction_percent':0,'signal_pins':5,'routing_complete':route_ok,'attempts':attempts,'checks':checks,'input_sha256':hashes,'pad_map':pads,'component_origins':{f.GetReference():[pcb.ToMM(f.GetPosition().x),pcb.ToMM(f.GetPosition().y)] for f in b.GetFootprints()},'pin_map_source':'MT6701 Rev1.8 pp4,24,35; CJT WR A3 drawing','EP_status':'OPEN isolates pad17 pending manufacturer instructions; blocks fabrication','physical_tested':False,'manufacturing_released':False,'regional_boards_converted':False,'notes':['Mechanical board datum kept; no smaller whole joint claimed','No MISO buffer deletion; all-low CRC-valid frame cannot establish presence','No live ESP/UE capture enabled','0.3 mm vias, 0.15 mm clearance/track; supplier DFM still open']}
 save(OUT/'result.json',report);print(json.dumps({'routing':route_ok,'checks':checks},indent=2))
if __name__=='__main__':main()
