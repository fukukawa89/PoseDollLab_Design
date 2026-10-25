"""Import local autorouting, preserve explicit project rules, repair only selected nets."""
from electronics_carrier import *
def rules():
 pro=json.loads((D/(NAME+'.kicad_pro')).read_text('utf8'))
 pro['board']['design_settings']['rules'].update(min_track_width=.12,min_clearance=.15,min_copper_edge_clearance=.3,min_through_hole_diameter=.3,min_via_annular_width=.15)
 for c in pro['net_settings']['classes']:c['clearance']=.15
 for n in [NAME,'route_input','repair_input']:put(D/(n+'.kicad_pro'),pro)
def main():
 mode=sys.argv[1]
 if mode=='repair':
  b=p.LoadBoard(str(D/(NAME+'.kicad_pcb')))
  names={'/'+f'B{i:02}_DO' for i in [9,10,11,12,13]}
  for q in list(b.GetTracks()):
   if q.GetNetname() in names:b.Delete(q)
  p.SaveBoard(str(D/'repair_input.kicad_pcb'),b);assert p.ExportSpecctraDSN(b,str(D/'repair_input.dsn'));rules();return
 stem='priority' if mode=='import-priority' else ('repair' if mode=='import-repair' else 'route')
 b=p.LoadBoard(str(D/(stem+'_input.kicad_pcb')))
 assert p.ImportSpecctraSES(b,str(D/(stem+'.ses')))
 for q in b.GetTracks():
  if isinstance(q,p.PCB_VIA):q.SetWidth(p.FromMM(.6));q.SetDrill(p.FromMM(.3))
 b.BuildConnectivity();p.SaveBoard(str(D/(NAME+'.kicad_pcb')),b);rules()
 result={x:check(x) for x in ['erc','drc']};d=json.loads((D/'drc.json').read_text('utf8'));result['drc']['parity']=len(d['schematic_parity'])
 lay=json.loads((D/'placement.json').read_text('utf8'));lay.update(checks=result,tracks=len(list(b.GetTracks())),routing_complete=not d['violations'] and not d['unconnected_items'] and not d['schematic_parity'],pcb_sha256=hashlib.sha256((D/(NAME+'.kicad_pcb')).read_bytes()).hexdigest(),trace_process='Four layers, min 0.12 mm traces, 0.15 mm clearance, 0.60 / 0.30 mm through vias; DC/thermal review separate');put(D/'placement.json',lay);print(result,flush=True)
if __name__=='__main__':main()
