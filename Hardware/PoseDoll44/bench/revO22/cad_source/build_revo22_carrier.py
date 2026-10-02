"""O22 carrier layout, exact power choices, two-layer routing candidate."""
from pathlib import Path
import sys,json,uuid,shutil,subprocess,re
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';B=H/'bench/revO22'
sys.path.insert(0,str(R/'scripts'))
import build_revo21_electronics as e
p=e.pcb;k=e.k
e.B=B
original_setup=e.setup
def setup(folder,name):
 original_setup(folder,name.replace('O21','O22'));k.NS=uuid.uuid5(uuid.NAMESPACE_URL,'posedoll/o22/'+k.NAME)
e.setup=setup
D=B/'electronics/carrier';NAME='PoseDoll_O22_SSI_Carrier'
def main():
 e.carrier()
 for c in k.comps:
  c['nets']={pin:(net.replace('SENSOR_3V3','SENSOR_3V45').replace('REG_3V3','REG_3V45') if net else None) for pin,net in c['nets'].items()}
  ref=c['ref']
  changes={'F4':('1206L110THR / input 1.1A','Fuse:Fuse_1206_3216Metric'),
           'F5':('0467001.NR / 1A fast','Fuse:Fuse_0603_1608Metric'),
           'L1':('74438357022 / 2.2uH','Inductor_SMD:L_Wuerth_MAPI-4030'),
           'R50':('316k 0.1%','Resistor_SMD:R_0603_1608Metric'),
           'R51':('66.5k 0.1%','Resistor_SMD:R_0603_1608Metric')}
  if ref in changes:c['value'],c['fp']=changes[ref]
  if c['fp'] and c['pcb']==(0,0):c['pcb']=(0,0)
 # Coordinates denote courtyard centers; strip header pin1 direction is explicit.
 positions={'J1':(92.38,88),'J2':(107.62,88),'U1':(82,99),'U2':(146,103),'U6':(128,98),
  'J3':(143,80),'F4':(145,88),'D1':(134.5,78),'U7':(130,86),'L1':(122,86),
  'C7':(134,89),'C8':(120,92),'C9':(124,92),'R50':(126,81),'R51':(130,81),
  'C10':(122,81),'F5':(116,93),'Q1':(84,85),'R1':(80,90),'R2':(84,90),
  'C1':(80,93.5),'C2':(150,97),'C6':(134,99)}
 for c in k.comps:
  ref=c['ref']
  if ref in positions:c['pcb']=positions[ref]
  if ref=='J2':c['angle']=180
  if ref.startswith('R') and 10<=int(ref[1:])<20:
   n=int(ref[1:])-10;c['pcb']=(96+4*(n%3),82+3*(n//3))
 for bank,a in enumerate('ABC'):
  cx=86+24*bank
  positions={f'U{3+bank}':(cx,109),f'C{3+bank}':(cx+7,105),f'R{40+bank}':(cx+8,110),
   f'R{30+2*bank}':(cx+2,102),f'R{31+2*bank}':(cx+6,102)}
  for c in k.comps:
   ref=c['ref']
   if ref in positions:c['pcb']=positions[ref]
   if ref.startswith('J') and 10+16*bank<=int(ref[1:])<10+16*bank+(14 if bank==0 else 16):
    i=int(ref[1:])-10-16*bank;c['pcb']=(cx-5+10*(i%2),117+6.5*(i//2))
    c['value']=f'{a}{i+1:02} BM05B-SRSS-TB'
 next(c for c in k.comps if c['ref']=='C5')['pcb']=(148,109)
 for n,(net,xy) in enumerate([('GND',(152,93)),('REG_3V45',(152,90)),('SENSOR_3V45',(152,112)),('VIN',(152,87))],1):
  k.part('TP'+str(n),'Connector','TestPoint',net,'TestPoint:TestPoint_Pad_D1.0mm',{1:net},xy)
 for n,xy in enumerate([(78,78),(152,78),(78,166),(152,166)],1):
  k.part('H'+str(n),'Mechanical','MountingHole','M2 clearance','MountingHole:MountingHole_2.2mm_M2',{},xy)
 assert all(c['pcb']!=(0,0) for c in k.comps if c['fp']),[c['ref'] for c in k.comps if c['fp'] and c['pcb']==(0,0)]
 root=k.schematic();k.board(root)
 b=p.LoadBoard(str(D/'placement.kicad_pcb'));b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
 for s in list(b.GetDrawings()):
  if s.GetLayer()==p.Edge_Cuts:b.Remove(s)
 for a,z in zip([(75,75),(155,75),(155,169),(75,169)],[(155,75),(155,169),(75,169),(75,75)]):
  s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(e.v(*a));s.SetEnd(e.v(*z));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
 for f in b.GetFootprints():
  if f.GetReference().startswith('J') and f.GetReference() not in ('J1','J2','J3'):
   label=p.PCB_TEXT(b);label.SetText(f.GetValue().split()[0]);xy=f.GetPosition()
   label.SetPosition(p.VECTOR2I(xy.x,xy.y+p.FromMM(2.9)));label.SetTextSize(e.v(.8,.8));label.SetTextThickness(p.FromMM(.12));label.SetLayer(p.F_SilkS);b.Add(label)
 pro=json.loads((D/(NAME+'.kicad_pro')).read_text())
 pro['board']['design_settings']['rules'].update(min_track_width=.15,min_clearance=.15,min_copper_edge_clearance=.3,min_through_hole_diameter=.3,min_via_annular_width=.15)
 default=pro['net_settings']['classes'][0];default.update(track_width=.2,clearance=.15,via_diameter=.6,via_drill=.3)
 pro['net_settings']['classes']=[default,dict(default,name='Power',track_width=.8),dict(default,name='Ground',track_width=.5)]
 pro['net_settings']['netclass_patterns']=[{'netclass':'Power','pattern':'/'+n} for n in ['EXT5V','FUSED5V','VIN','LX','REG_3V45','SENSOR_3V45']]+[{'netclass':'Ground','pattern':'/GND'}]
 for name in (NAME,'placement','route_input'):e.put(D/(name+'.kicad_pro'),pro)
 p.SaveBoard(str(D/'placement.kicad_pcb'),b);p.SaveBoard(str(D/(NAME+'.kicad_pcb')),b)
 libs=sorted({c['fp'].split(':')[0] for c in k.comps if c['fp']})
 (D/'fp-lib-table').write_text('(fp_lib_table '+''.join('(lib (name "'+n+'") (type KiCad) (uri "'+'$'+'{KICAD10_FOOTPRINT_DIR}/'+n+'.pretty") (options "") (descr ""))' for n in libs)+')')
 e.put(D/'components.json',k.comps)
 checks={'erc':e.check('erc'),'placement_drc':e.check('drc')}
 e.put(D/'placement_review.json',checks);print(checks,flush=True)
if __name__=='__main__':main()
