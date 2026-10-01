"""Keep 80x94 outline; add two continuous internal power/reference layers."""
from pathlib import Path
import json,pcbnew as p,subprocess
D=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO22/electronics/carrier';N='PoseDoll_O22_SSI_Carrier'
b=p.LoadBoard(str(D/(N+'.kicad_pcb')));b.SetCopperLayerCount(4)
for existing in list(b.Zones()):
 if existing.GetLayer() in (p.In1_Cu,p.In2_Cu):b.Remove(existing)
# Rule areas apply through the internal layers too. No copper under inductor body.
for layer,net in [(p.In1_Cu,'/GND'),(p.In2_Cu,'/SENSOR_3V45')]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNetCode(b.FindNet(net).GetNetCode());z.SetLocalClearance(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.2));poly=z.Outline();poly.NewOutline()
 for x,y in [(75.5,75.5),(154.5,75.5),(154.5,168.5),(75.5,168.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
 keep=p.ZONE(b);keep.SetIsRuleArea(True);keep.SetLayer(layer);keep.SetDoNotAllowTracks(True);keep.SetDoNotAllowVias(True);keep.SetDoNotAllowZoneFills(True);keep.SetDoNotAllowPads(False);keep.SetDoNotAllowFootprints(False)
 poly=keep.Outline();poly.NewOutline()
 for x,y in [(119.75,83.75),(124.25,83.75),(124.25,88.25),(119.75,88.25)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(keep)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(D/(N+'.kicad_pcb')),b)
pro=json.loads((D/(N+'.kicad_pro')).read_text())
for c in pro['net_settings']['classes']:c['clearance']=.15
pro['board']['design_settings']['rules'].update(min_track_width=.15,min_clearance=.15,min_through_hole_diameter=.3,min_via_annular_width=.15)
(D/(N+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
subprocess.run(['D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--schematic-parity','--severity-all','-o',str(D/'drc_routed.json'),str(D/(N+'.kicad_pcb'))],check=True)
d=json.loads((D/'drc_routed.json').read_text());print('FOUR LAYER DRC',[(v['type'],v['description']) for v in d['violations']],len(d['unconnected_items']))
print('Inner areas',[(z.GetNetname(),z.CalculateFilledArea()) for z in b.Zones() if not z.GetIsRuleArea()])
