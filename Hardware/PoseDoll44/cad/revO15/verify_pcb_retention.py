from layout_fullbody import *
rows=[]
for kind,(p,owners,skus) in libraries().items():
 for key,plate in p.items():
  if not key.endswith('sensor_PCB'):continue
  prefix=key[:-len('sensor_PCB')];members=[k for k in p if k.startswith(prefix) and skus[k] in ('AS5048A_MINI_PCBA','PCBA_INCLUDED')];board=md.Manifold.batch_boolean([p[k] for k in members],md.OpType.Add);ic=p[prefix+'sensor_IC'];center=np.array(mesh_record(plate)['COM_mm']);normal=unit(center-np.array(mesh_record(ic)['COM_mm']));owner=owners[key]
  obstacles={k:s for k,s in p.items() if owners[k]==owner and k not in members};tests=[]
  for axis,sg in itertools.product(range(3),(-1,1)):
   ds=[]
   for d in (.05,.1,.2,.5,1):
    delta=np.eye(3)[axis]*sg*d;hh=hits({'PCB_GROUP':pose(board,p=delta),**obstacles});hits_board=[h for h in hh if 'PCB_GROUP' in h['pair']];ds.append({'distance_mm':d,'blocked_by':hits_board})
   tests.append({'axis':axis,'direction':sg,'blocked_within_1mm':any(r['blocked_by'] for r in ds),'samples':ds})
  removed=[k for k in obstacles if k.startswith(prefix) and ('pcb_clip' in k or 'pcb_screw' in k) and 'nut' not in k];service=[]
  for d in (.1,.5,1,2,5,10,15):
   moving=pose(board,p=normal*d);hh=hits({'PCB_GROUP':moving,**{k:s for k,s in obstacles.items() if k not in removed}});service.append({'lift_mm':d,'findings':[h for h in hh if 'PCB_GROUP' in h['pair']]})
  rr={'kind':kind,'pcb':key,'translation_checks':tests,'all_translation_directions_blocked':all(t['blocked_within_1mm'] for t in tests),'service_removed':removed,'extraction_direction':normal.tolist(),'extraction':service,'clear_extraction_samples':all(not r['findings'] for r in service)};rows.append(rr);print('PCB',kind,key,'retained',rr['all_translation_directions_blocked'],'service',rr['clear_extraction_samples'],flush=True)
  save('pcb_retention.json',{'status':'CHECK_RUNNING','boards':rows})
save('pcb_retention.json',{'status':'SAMPLED_GEOMETRY_CHECK','boards':rows,'input_sha256':{p.name:sha(p) for p in OUT.glob('*_parts.npz')},'scope':'Rigid local translations and straight extraction after named clips/screws removed. Not retention-force, vibration, or all coupled escape-path proof.'})
