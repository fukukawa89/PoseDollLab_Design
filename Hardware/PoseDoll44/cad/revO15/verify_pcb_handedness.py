from layout_fullbody import *
rows=[]
for char in ('quinn','manny'):
 p,m,st,f,pr=build(char,{});_,mm,_,_,_=build(char,{},geometry=False)
 for k,s in p.items():
  if m[k]['sku']!='AS5048A_MINI_PCBA':continue
  prefix=k[:-len('sensor_PCB')];group={kk for kk in p if kk.startswith(prefix) and m[kk]['sku'] in ('AS5048A_MINI_PCBA','PCBA_INCLUDED')};module=m[k]['module'];obstacles={kk:v for kk,v in p.items() if m[kk]['module']==module and kk not in group};findings=[]
  for kk in group:
   shape=p[kk];bb=np.array(shape.bounding_box())
   for other,ss in obstacles.items():
    ob=np.array(ss.bounding_box())
    if np.any(np.minimum(bb[3:],ob[3:])<=np.maximum(bb[:3],ob[:3])):continue
    vol=float((shape^ss).volume())
    if vol>1e-4:findings.append({'pair':[kk,other],'overlap_mm3':vol})
  determinants=[float(np.linalg.det(mm[kk]['transform'][:3,:3])) for kk in group];row={'character':char,'pcb':k,'proper_rotations':all(abs(d-1)<1e-7 for d in determinants),'constituent_count':len(group),'module_interference':findings};rows.append(row)
 print('PCB_HANDEDNESS',char,sum(r['proper_rotations'] and not r['module_interference'] for r in rows if r['character']==char),'of',sum(r['character']==char for r in rows),flush=True)
save('pcb_handedness.json',{'rows':rows,'source_sha256':sha(Path(__file__).with_name('layout_fullbody.py')),'scope':'Same manufactured PCBA on reflected printed mounts; nominal module interference only. Connector mating/cables/calibration separate.'})
