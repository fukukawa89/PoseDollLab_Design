"""O24D electrical revision of the O23 back carrier. Run with KiCad Python."""
from pathlib import Path
import sys,json,uuid,subprocess,hashlib,shutil
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44';OUT=H/'bench/revO24D'
sys.path.insert(0,str(R/'scripts'))
import build_revo21_electronics as e
p=e.pcb;k=e.k;CLI=e.CLI
D=OUT/'electronics/carrier';NAME='PoseDoll_O24D_SPI_Carrier'
def put(f,x):f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def check(name):
 args=['sch','erc'] if name=='erc' else ['pcb','drc','--schematic-parity','--all-track-errors'];ext='.kicad_sch' if name=='erc' else '.kicad_pcb'
 r=subprocess.run([str(CLI),*args,'--format','json','--severity-all','-o',str(D/(name+'.json')),str(D/(NAME+ext))],capture_output=True)
 (D/(name+'.log')).write_bytes(r.stdout+r.stderr);a=json.loads((D/(name+'.json')).read_text('utf8'));issues=a.get('violations',[])+[x for s in a.get('sheets',[]) for x in s.get('violations',[])];return dict(exit=r.returncode,violations=len(issues),unconnected=len(a.get('unconnected_items',[])),categories={t:sum(x['type']==t for x in issues) for t in sorted({x['type'] for x in issues})})
def main():
 D.mkdir(parents=True,exist_ok=True);k.OUT=D;k.NAME=NAME;k.NS=uuid.uuid5(uuid.NAMESPACE_URL,'posedoll/O24D/SPI');k.custom_symbol=e.symbol
 old=H/'bench/revO23/electronics/carrier';placements=json.loads((old/'placement.json').read_text('utf8'));positions={c['reference']:c for c in placements['footprints']}
 source=json.loads((H/'bench/revO22/electronics/carrier/components.json').read_text('utf8'))
 k.comps=[c for c in source if c['ref'] not in [*['J'+str(n) for n in range(18,24)],'J41','J57']]
 for c in k.comps:
  ref=c['ref'];pos=positions.get(ref)
  if ref in ['R50','R51','C10']:c['value']={'R50':'31.6k 0.1%','R51':'6.65k 0.1%','C10':'220p C0G starting value'}[ref]
  if pos:c.update(pcb=[pos['x_mm'],pos['y_mm']],angle=pos['angle_deg'],back=pos['side']=='B')
  if ref=='J1':c['nets']['3']='MOSI_MCU';c['value']='XIAO LEFT D0-D6; D2=MOSI'
  if ref=='U2':
   for pi,po,bank in zip([6,8,11],[14,12,9],'ABC'):c['nets'][str(pi)]='MOSI_MCU';c['nets'][str(po)]='MOSI_'+bank+'_DRV'
  if ref in ['U3','U4','U5']:
   count=8 if ref=='U3' else 15
   for i,pi in enumerate([9,8,7,6,5,4,3,2,23,22,21,20,19,18,17,16]):
    if i>=count:c['nets'][str(pi)]='GND'
  if ref.startswith('J') and ref not in ['J1','J2','J3']:
   bank=c['nets']['3'][-1];c['nets']['6']='MOSI_'+bank;c['sym']='Conn_01x06';c['fp']='Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical';c['value']=c['value'].split()[0]+' BM06B-SRSS-TB'
 for i,bank in enumerate('ABC'):
  k.resistor('R'+str(60+i),'33R',f'MOSI_{bank}_DRV',f'MOSI_{bank}',(43,35+4*i))
 k.resistor('R63','100k','MOSI_MCU','GND',(43,47))
 root=k.schematic();k.board(root)
 b=p.LoadBoard(str(D/'placement.kicad_pcb'))
 for q in list(b.GetDrawings()):b.Delete(q)
 for f in b.GetFootprints():
  c=next(c for c in k.comps if c['ref']==f.GetReference());f.SetOrientationDegrees(c['angle']);f.SetPosition(v(*c['pcb']))
  # Match O23's exact back footprint orientation, independent of importer convention.
  oldf=positions.get(c['ref'])
  if c['back'] and f.GetLayer()!=p.B_Cu:f.Flip(f.GetPosition(),True)
  if c['back']:f.SetOrientationDegrees(0)
 pts=[(0,0),(64,0),(64,60),(0,60)]
 for a,z in zip(pts,pts[1:]+pts[:1]):
  q=p.PCB_SHAPE();q.SetShape(p.SHAPE_T_SEGMENT);q.SetStart(v(*a));q.SetEnd(v(*z));q.SetLayer(p.Edge_Cuts);q.SetWidth(p.FromMM(.05));b.Add(q)
 b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
 pro=json.loads((D/(NAME+'.kicad_pro')).read_text('utf8'));rules=pro['board']['design_settings']['rules'];rules.update(min_track_width=.15,min_clearance=.15,min_copper_edge_clearance=.3,min_through_hole_diameter=.3,min_via_annular_width=.15)
 default=pro['net_settings']['classes'][0];default.update(track_width=.2,clearance=.15,via_diameter=.6,via_drill=.3)
 pro['net_settings']['classes']=[default,dict(default,name='Power',track_width=.5),dict(default,name='Ground',track_width=.5)]
 pro['net_settings']['netclass_patterns']=[{'netclass':'Power','pattern':'/'+n} for n in ['EXT5V','FUSED5V','VIN','LX','REG_3V45','SENSOR_3V45']]+[{'netclass':'Ground','pattern':'/GND'}]
 for n in [NAME,'placement','route_input']:put(D/(n+'.kicad_pro'),pro)
 libs=sorted({c['fp'].split(':')[0] for c in k.comps if c['fp']});(D/'fp-lib-table').write_text('(fp_lib_table '+''.join('(lib (name "'+n+'") (type KiCad) (uri "${KICAD10_FOOTPRINT_DIR}/'+n+'.pretty") (options "") (descr ""))' for n in libs)+')','utf8')
 p.SaveBoard(str(D/(NAME+'.kicad_pcb')),b);p.SaveBoard(str(D/'route_input.kicad_pcb'),b)
 assert p.ExportSpecctraDSN(b,str(D/'route_input.dsn'))
 put(D/'components.json',k.comps)
 rows=[]
 for f in b.GetFootprints():
  bb=f.GetBoundingBox(False,False);rows.append(dict(reference=f.GetReference(),value=f.GetValue(),side='B' if f.GetLayer()==p.B_Cu else 'F',x_mm=p.ToMM(f.GetPosition().x),y_mm=p.ToMM(f.GetPosition().y),bbox_mm=[p.ToMM(bb.GetLeft()),p.ToMM(bb.GetTop()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())],pads={q.GetNumber():q.GetNetname() for q in f.Pads()}))
 put(D/'placement.json',dict(board_mm=[64,60,1.6],footprints=rows,sensor_ports=38,banks={'A':8,'B':15,'C':15},source_O23_sha256=hashlib.sha256((old/'PoseDoll_O23C_SSI_Carrier.kicad_pcb').read_bytes()).hexdigest(),checks={n:check(n) for n in ['erc','drc']},routing_complete=False,manufacturing_release=False,pinout=['GND','SENSOR_3V45','SCK','SDO','CS_N','SDI'],design='O23 form factor, power, XIAO and three read mux banks; D2 MOSI fanout through three formerly spare U2 buffers. Shared broadcast CS and SDI, independent SDO per port.'))
 print('O24D carrier generated',flush=True)
if __name__=='__main__':main()
