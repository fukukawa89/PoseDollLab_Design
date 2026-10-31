from electronics_carrier import *
from electronics_route import rules
b=p.LoadBoard(str(D/'route_input.kicad_pcb'));assert not list(b.GetTracks())
pads={ (f.GetReference(),q.GetNumber()):q for f in b.GetFootprints() for q in f.Pads() };net=pads['U4','21'].GetNetCode()
def track(a,z,L):
 t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(p.FromMM(.15));t.SetLayer(L);t.SetNetCode(net);t.SetLocked(True);b.Add(t)
track((14.8625,32.625),(16.5,32.625),p.B_Cu);track((47.5,19.175),(47.5,17.9),p.B_Cu);track((16.5,32.625),(47.5,17.9),p.In1_Cu)
for xx,yy in [(16.5,32.625),(47.5,17.9)]:
 q=p.PCB_VIA(b);q.SetPosition(v(xx,yy));q.SetWidth(p.FromMM(.6));q.SetDrill(p.FromMM(.3));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetNetCode(net);q.SetLocked(True);b.Add(q)
p.SaveBoard(str(D/'priority_input.kicad_pcb'),b);p.ExportSpecctraDSN(b,str(D/'priority_input.dsn'));rules();shutil.copy2(D/'route_input.kicad_pro',D/'priority_input.kicad_pro')
subprocess.run([str(CLI),'pcb','drc','--format','json','--severity-all','-o',str(D/'priority_drc.json'),str(D/'priority_input.kicad_pcb')],check=True)
a=json.loads((D/'priority_drc.json').read_text('utf8'));print('PRIORITY',len(a['violations']),len(a['unconnected_items']),a['violations'][:2]);assert not a['violations']
