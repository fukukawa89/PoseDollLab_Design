"""Close plane-island connections; preserve explicit fabrication rules."""
from pathlib import Path
import pcbnew as p,json,subprocess,math,collections
from build_controller import OUT,NAME,CLI
FILE=OUT/(NAME+'.kicad_pcb')
b=p.LoadBoard(str(FILE));report=json.loads((OUT/'drc_routed.json').read_text());added=[]
for f in report['unconnected_items']:
 item=f['items'][0];uid=item['uuid'];tracks=[t for t in b.GetTracks() if t.m_Uuid.AsString()==uid]
 if len(tracks)!=1:raise ValueError(uid)
 t=tracks[0];a=t.GetStart();z=t.GetEnd();x=round((a.x+z.x)/2);y=round((a.y+z.y)/2)
 via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(x,y));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('/GND'));b.Add(via);added.append([p.ToMM(x),p.ToMM(y)])
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
# SaveBoard can rewrite project settings from the API's cached defaults. Apply
# the intended 0.15mm / 0.30mm fabrication specification after that save.
pro=json.loads(FILE.with_suffix('.kicad_pro').read_text());pro['board']['design_settings']['rules'].update(min_track_width=.15,min_clearance=.15,min_copper_edge_clearance=.3,min_through_hole_diameter=.3,min_via_annular_width=.15)
FILE.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2));(OUT/'plane_stitching.json').write_text(json.dumps({'added_ground_vias_mm':added,'method':'midpoint of each reported disconnected ground track'},indent=2))
subprocess.run([str(CLI),'pcb','drc','--format','json','--schematic-parity','-o',str(OUT/'drc_final.json'),str(FILE)],check=True)
d=json.loads((OUT/'drc_final.json').read_text());print('DRC',collections.Counter(v['type'] for v in d['violations']),'UNCONNECTED',len(d['unconnected_items']))
