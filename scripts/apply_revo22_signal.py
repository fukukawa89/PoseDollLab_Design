from pathlib import Path
import json,pcbnew as p,subprocess
D=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO22/electronics/carrier';N='PoseDoll_O22_SSI_Carrier'
b=p.LoadBoard(str(D/(N+'.kicad_pcb')));d=json.loads((D/'signal_repair.json').read_text());net=next(n for n in b.GetNetsByNetcode().values() if n.GetNetname()==d['net'])
for t in list(b.GetTracks()):
 if t.GetNetCode()==net.GetNetCode():b.Remove(t)
v=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def track(a,z,l):
 if a==z:return
 t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(p.FromMM(.15));t.SetLayer(p.F_Cu if l==0 else p.B_Cu);t.SetNetCode(net.GetNetCode());b.Add(t)
path=d['path'];track(d['endpoints'][0]['p'],path[0][:2],0);track(path[-1][:2],d['endpoints'][1]['p'],0)
# Compact collinear raster runs, preserving each bend and layer transition.
start=path[0];lastdir=None;prev=start
for current in path[1:]:
 direction=tuple(round(current[i]-prev[i],6) for i in range(3))
 if direction!=lastdir and prev!=start:track(start[:2],prev[:2],start[2]);start=prev
 if current[2]!=prev[2]:
  via=p.PCB_VIA(b);via.SetPosition(v(*prev[:2]));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(net.GetNetCode());b.Add(via);start=current
 lastdir=direction;prev=current
track(start[:2],prev[:2],start[2]);b.BuildConnectivity();p.SaveBoard(str(D/(N+'.kicad_pcb')),b)
pro=json.loads((D/(N+'.kicad_pro')).read_text())
for c in pro['net_settings']['classes']:c['clearance']=.15
pro['board']['design_settings']['rules'].update(min_track_width=.15,min_clearance=.15,min_through_hole_diameter=.3,min_via_annular_width=.15)
(D/(N+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
subprocess.run(['D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--schematic-parity','--severity-all','-o',str(D/'drc_routed.json'),str(D/(N+'.kicad_pcb'))],check=True)
a=json.loads((D/'drc_routed.json').read_text());print([(v['type'],v['description']) for v in a['violations']],len(a['unconnected_items']))
