"""Five routed sensor PCB variants fitted to existing O24D board reservations."""
from electronics_carrier import *
def main():
 e.defs['TMAG5170']={1:('SCK','input'),2:('SDI','input'),3:('SDO','output'),4:('CS_N','input'),5:('VCC','power_in'),6:('GND','power_in'),7:('TEST_GND','input'),8:('ALERT','open_collector')}
 mount=json.loads((OUT/'electronics/sensor_mounts.json').read_text('utf8'))['rows'];variants={}
 for row in mount:
  key=(round(row['board_uv_mm'][0]),round(row['board_uv_mm'][1]),*map(lambda v:round(float(v),6),row['ic_offset_uv_mm']));variants.setdefault(key,[]).append(row['sensor'])
 manifest=[]
 for index,(key,instances) in enumerate(variants.items()):
  width,height,du,dv=key;tag='S'+str(index+1);dest=OUT/'electronics/sensors'/tag;dest.mkdir(parents=True,exist_ok=True);k.OUT=dest;k.NAME='PoseDoll_O24D_TMAG_'+tag;k.NS=uuid.uuid5(uuid.NAMESPACE_URL,k.NAME);k.custom_symbol=e.symbol;k.comps=[]
  f=p.FOOTPRINT(None);f.SetFPID(p.LIB_ID('PoseDoll','WirePads_6P'));f.SetAttributes(p.FP_SMD)
  for i in range(6):
   pad=p.PAD(f);pad.SetNumber(str(i+1));pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetShape(p.PAD_SHAPE_RECT);pad.SetPosition(v((i-2.5)*1.0,0));pad.SetSize(v(.6,.85));ls=p.LSET();ls.AddLayer(p.F_Cu);ls.AddLayer(p.F_Mask);pad.SetLayerSet(ls);f.Add(pad)
  for a,z in zip([(-3.05,-.68),(3.05,-.68),(3.05,.68),(-3.05,.68)],[(3.05,-.68),(3.05,.68),(-3.05,.68),(-3.05,-.68)]):
   g=p.PCB_SHAPE(f);g.SetShape(p.SHAPE_T_SEGMENT);g.SetStart(v(*a));g.SetEnd(v(*z));g.SetLayer(p.F_CrtYd);g.SetWidth(p.FromMM(.05));f.Add(g)
  folder=dest/'PoseDoll.pretty';folder.mkdir(exist_ok=True);p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(folder),f)
  k.part('U1','PoseDoll','TMAG5170','TMAG5170A1DGKR','Package_SO:VSSOP-8_3x3mm_P0.65mm',{1:'SCK',2:'SDI',3:'SDO_IC',4:'CS_N',5:'VCC',6:'GND',7:'GND',8:None},(100+du,100+dv))
  k.part('J1','Connector_Generic','Conn_01x06','FACTORY_SOLDERED_6_CORE','PoseDoll:WirePads_6P',{1:'GND',2:'VCC',3:'SCK',4:'SDO',5:'CS_N',6:'SDI'},(100,100+(-1 if dv>1 else 1)*(height/2-1.2)))
  # Place decoupling and SDO damping in the opposite edge strip.
  cx=95.8 if width==10 else 95.2
  k.capacitor('C1','100n X7R 16V','VCC','GND',(cx,98.8),angle=90,fp='Capacitor_SMD:C_0402_1005Metric')
  k.capacitor('C2','1u X7R 10V','VCC','GND',(cx,101.2),angle=90,fp='Capacitor_SMD:C_0402_1005Metric')
  ry=99.0 if dv>1 else (101.1 if dv<-1 else 96.8)
  k.resistor('R1','33R','SDO_IC','SDO',(98.7,ry))
  k.resistor('R2','10k','VCC','CS_N',(101.3,ry))
  for c in k.comps:
   if c['ref'] in ['R1','R2']:c['fp']='Resistor_SMD:R_0402_1005Metric'
  e.flag(1,'VCC');e.flag(2,'GND');root=k.schematic();k.board(root)
  b=p.LoadBoard(str(dest/'placement.kicad_pcb'));b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(p.FromMM(.8))
  for q in list(b.GetDrawings()):b.Delete(q)
  for f in b.GetFootprints():
   c=next(c for c in k.comps if c['ref']==f.GetReference());f.SetPosition(v(*c['pcb']));f.SetOrientationDegrees(c['angle'])
  pts=[(100-width/2,100-height/2),(100+width/2,100-height/2),(100+width/2,100+height/2),(100-width/2,100+height/2)]
  for a,z in zip(pts,pts[1:]+pts[:1]):
   q=p.PCB_SHAPE();q.SetShape(p.SHAPE_T_SEGMENT);q.SetStart(v(*a));q.SetEnd(v(*z));q.SetLayer(p.Edge_Cuts);q.SetWidth(p.FromMM(.05));b.Add(q)
  p.SaveBoard(str(dest/(k.NAME+'.kicad_pcb')),b);p.SaveBoard(str(dest/'route_input.kicad_pcb'),b);p.ExportSpecctraDSN(b,str(dest/'route_input.dsn'))
  pro=json.loads((dest/(k.NAME+'.kicad_pro')).read_text('utf8'));pro['board']['design_settings']['rules'].update(min_track_width=.12,min_clearance=.15,min_copper_edge_clearance=.25,min_through_hole_diameter=.2,min_via_annular_width=.1,min_via_diameter=.4);pro['net_settings']['classes'][0].update(track_width=.15,clearance=.15,via_diameter=.4,via_drill=.2)
  for n in [k.NAME,'route_input']:put(dest/(n+'.kicad_pro'),pro)
  libs=sorted({c['fp'].split(':')[0] for c in k.comps if c['fp']});(dest/'fp-lib-table').write_text('(fp_lib_table '+''.join('(lib (name "'+n+'") (type KiCad) (uri "'+('${KIPRJMOD}/PoseDoll.pretty' if n=='PoseDoll' else '${KICAD10_FOOTPRINT_DIR}/'+n+'.pretty')+'") (options "") (descr ""))' for n in libs)+')','utf8')
  result={}
  for typ,args,ext in [('erc',['sch','erc'],'.kicad_sch'),('drc',['pcb','drc'],' .kicad_pcb'.strip())]:
   subprocess.run([str(CLI),*args,'--format','json','--severity-all','-o',str(dest/(typ+'.json')),str(dest/(k.NAME+ext))],capture_output=True,check=True);a=json.loads((dest/(typ+'.json')).read_text('utf8'));vv=a.get('violations',[])+[v for sh in a.get('sheets',[]) for v in sh.get('violations',[])];result[typ]=dict(violations=len(vv),unconnected=len(a.get('unconnected_items',[])),detail=vv)
  manifest.append(dict(tail_side_v=(-1 if dv>1 else 1),variant=tag,name=k.NAME,board_mm=[width,height,.8],ic_offset_uv_mm=[du,dv],instances=instances,checks=result,manufacturing_release=False));put(dest/'components.json',k.comps);print(tag,{t:{k:v for k,v in r.items() if k!='detail'} for t,r in result.items()},flush=True)
 put(OUT/'electronics/sensors/manifest.json',dict(variants=manifest,manufacturing_release=False,solder_tail='Factory-soldered and locally potted six-core pigtail; fanout is confined to the board perimeter, exits at the existing strain-relief datum. Free bending starts outside the potted fanout.'))
if __name__=='__main__':main()
