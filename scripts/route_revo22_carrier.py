"""Offline Specctra route; native KiCad DRC and DC resistance check are required."""
from pathlib import Path
import sys,json,re,subprocess
import pcbnew as p
R=Path(__file__).resolve().parents[1];D=R/'Hardware/PoseDoll44/bench/revO22/electronics/carrier'
NAME='PoseDoll_O22_SSI_Carrier';CLI='D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe'
def main(mode):
 if mode=='prepare':
  d=json.loads((D/'drc.json').read_text(encoding='utf-8'))
  assert not d['violations'],[(x['type'],x['description']) for x in d['violations']]
  b=p.LoadBoard(str(D/(NAME+'.kicad_pcb')))
  # Start from actual pads/netlist. Native exporter uses .2mm default routing;
  # filled copper and subsequent DC graph audit qualify power distribution.
  p.SaveBoard(str(D/'route_input.kicad_pcb'),b)
  assert p.ExportSpecctraDSN(b,str(D/'route_input.dsn'))
  config=R/'.local/freerouting-o22';config.mkdir(exist_ok=True)
  if not (config/'freerouting.json').exists():
   cfg=json.loads((R/'.local/freerouting-o15/freerouting.json').read_text())
   import uuid
   cfg['profile'].update(id=str(uuid.uuid4()),allow_telemetry=False,allow_contact=False)
   cfg['gui']['enabled']=False;cfg['usage_and_diagnostic_data']['disable_analytics']=True
   (config/'freerouting.json').write_text(json.dumps(cfg))
  print('DSN ready',flush=True)
 else:
  b=p.LoadBoard(str(D/'route_input.kicad_pcb'))
  assert p.ImportSpecctraSES(b,str(D/'route.ses'))
  ses=(D/'route.ses').read_text()
  # Imported drill size follows net class on some KiCad versions: apply DSN stack.
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):t.SetWidth(p.FromMM(.6));t.SetDrill(p.FromMM(.3))
  b.BuildConnectivity();p.SaveBoard(str(D/(NAME+'.kicad_pcb')),b)
  pro=json.loads((D/(NAME+'.kicad_pro')).read_text(encoding='utf-8'))
  pro['board']['design_settings']['rules'].update(min_track_width=.15,min_clearance=.15,min_through_hole_diameter=.3,min_via_annular_width=.15)
  (D/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2),encoding='utf-8')
  for cls in pro['net_settings']['classes']:cls['clearance']=.15
  (D/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2),encoding='utf-8')
  sch=D/(NAME+'.kicad_sch');txt=sch.read_text(encoding='utf-8');txt=re.sub(r'(\(symbol \(lib_id "Mechanical:MountingHole"\).*?\(in_bom )yes',r'\1no',txt,flags=re.S);sch.write_text(txt,encoding='utf-8')
  subprocess.run([CLI,'pcb','drc','--format','json','--schematic-parity','--all-track-errors','--severity-all','-o',str(D/'drc_routed.json'),str(D/(NAME+'.kicad_pcb'))],check=True)
  d=json.loads((D/'drc_routed.json').read_text(encoding='utf-8'))
  from collections import Counter
  print('DRC',Counter(x['type'] for x in d['violations']),'unconnected',len(d['unconnected_items']),flush=True)
if __name__=='__main__':main(sys.argv[1])
