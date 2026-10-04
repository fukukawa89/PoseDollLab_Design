"""Local-only Specctra route adapter. KiCad final DRC remains authoritative."""
from pathlib import Path
import sys,json,subprocess,shutil,collections,re
import pcbnew as p
from build_controller import OUT,NAME,CLI,H
FILE=OUT/(NAME+'.kicad_pcb')
def prepare():
 b=p.LoadBoard(str(FILE));pro=json.loads(FILE.with_suffix('.kicad_pro').read_text());default=pro['net_settings']['classes'][0]
 power=dict(default,name='Power',track_width=.6,via_diameter=.8,via_drill=.4);branch=dict(default,name='BranchPower',track_width=.4,via_diameter=.8,via_drill=.4)
 pro['net_settings']['classes']=[default,power,branch];pro['net_settings']['netclass_patterns']=[{'netclass':'Power','pattern':'/VIN_5V'},{'netclass':'Power','pattern':'/MCU_5V'},{'netclass':'Power','pattern':'/SENSOR_3V3'},{'netclass':'Power','pattern':'/MCU_3V3'},{'netclass':'BranchPower','pattern':'/P*_3V3'}]
 for name in (NAME,'route_input'):(OUT/(name+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
 # Reload net classes through KiCad before DSN export.
 p.SaveBoard(str(OUT/'route_input.kicad_pcb'),b);b=p.LoadBoard(str(OUT/'route_input.kicad_pcb'))
 from seed_controller_planes import seed
 seeded=seed(b);(OUT/'plane_fanout.json').write_text(json.dumps(seeded,indent=2));print('FANOUT',collections.Counter(v['status'] for v in seeded))
 for layer,net in [(p.In1_Cu,'/GND'),(p.In2_Cu,'/SENSOR_3V3')]:
  z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet(net));z.SetLocalClearance(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.2));poly=z.Outline();poly.NewOutline()
  for x,y in [(0.4,0.4),(69.6,.4),(69.6,59.6),(.4,59.6)]:poly.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(OUT/'route_input.kicad_pcb'),b)
 assert p.ExportSpecctraDSN(b,str(OUT/'route_input.dsn'))
 # Native pcbnew exporter in this version writes default rules only. Explicit
 # net-class rules preserve the captured power widths in the autorouter input.
 d=(OUT/'route_input.dsn').read_text();anchor='  (placement'
 groups={'Power':['/VIN_5V','/MCU_5V','/SENSOR_3V3','/MCU_3V3'],'BranchPower':[f'/P{i}_3V3' for i in range(1,7)]}
 start=d.index('(class kicad_default');level=0;quoted=False
 for end in range(start,len(d)):
  ch=d[end]
  if ch=='"':quoted=not quoted
  if quoted:continue
  if ch=='(':level+=1
  elif ch==')':
   level-=1
   if not level:break
 block=d[start:end+1];extra=[]
 for name,names in groups.items():
  for net in names:block=re.sub(r'(?<![^\s])'+re.escape(net)+r'(?=\s)', '',block)
  extra.append('(class '+name+' '+' '.join(names)+' (circuit (use_via "Via[0-3]_600:300_um")) (rule (width '+('600' if name=='Power' else '400')+') (clearance 200)))')
 d=d[:start]+block+'\n'+'\n'.join(extra)+d[end+1:]
 for layer in ('In1.Cu','In2.Cu'):
  d=re.sub(r'(\(layer '+re.escape(layer)+r'\s+\(type )signal',r'\1power',d)
 (OUT/'route_input.dsn').write_text(d)
 print('DSN_READY',len(b.GetTracks()))
def finish():
 b=p.LoadBoard(str(OUT/'route_input.kicad_pcb'));assert p.ImportSpecctraSES(b,str(OUT/'route.ses'))
 # KiCad's SES importer can use the net-class drill instead of the named
 # SES padstack. Restore BOTH dimensions from each routed via's actual stack.
 ses=(OUT/'route.ses').read_text();assert '(resolution um 10)' in ses
 via_defs={}
 for diameter,drill,x,y in re.findall(r'\(via "Via\[0-3\]_(\d+):(\d+)_um"\s+([+-]?[\d.]+)\s+([+-]?[\d.]+)',ses):
  via_defs[(round(float(x)/10000,4),round(-float(y)/10000,4))]=(float(diameter)/1000,float(drill)/1000)
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   pos=t.GetPosition();key=(round(p.ToMM(pos.x),4),round(p.ToMM(pos.y),4))
   if key not in via_defs:raise ValueError(('missing SES via definition',key))
   dia,drill=via_defs[key];t.SetWidth(p.FromMM(dia));t.SetDrill(p.FromMM(drill))
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
 pro=json.loads(FILE.with_suffix('.kicad_pro').read_text());pro['board']['design_settings']['rules'].update(min_track_width=.15,min_clearance=.15,min_copper_edge_clearance=.3,min_through_hole_diameter=.3,min_via_annular_width=.15);FILE.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2))
 subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','-o',str(OUT/'drc_routed.json'),str(FILE)],check=True)
 d=json.loads((OUT/'drc_routed.json').read_text());print('ROUTED_DRC',collections.Counter(v['type'] for v in d['violations']),'UNCONNECTED',len(d['unconnected_items']))
if __name__=='__main__':prepare() if sys.argv[1]=='prepare' else finish()
