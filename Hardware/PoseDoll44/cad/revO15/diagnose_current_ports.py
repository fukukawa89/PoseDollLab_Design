from carriers_swept import *
char='quinn';pp,meta,states,fail,prof=build(char,ASSEMBLY_POSE);T,_=fk(prof,ASSEMBLY_POSE);aa=anchors(states,meta);bank=motion_bank(char);adj=adjacent_pairs(char);rr=read(OUT/'carriers_swept/quinn_routing.json');rows=[]
for rec in rr['frames']:
 if not rec['issues']:continue
 body=rec['body'];ends=aa[body];ids=[e['part'] for e in ends];ownmods={meta[k]['module'] for k in ids};related=set(ownmods)
 for pair in adj:
  if pair&ownmods:related.update(pair)
 obs=swept_obstacles(body,ids,related,pp,meta,T,bank,{})
 obb={k:np.array(v.bounding_box()) for k,v in obs.items()}
 for e in ends:
  if e['part'] not in [i.get('part') for i in rec['issues']]:continue
  alts=[]
  for point,normal in e['alternatives']:
   tests={}
   for tag,s in [('root',md.Manifold.sphere(3.85,24).translate(point)),('escape',md.Manifold.batch_hull([md.Manifold.sphere(3.85,24).translate(point),md.Manifold.sphere(5.25,24).translate(point+8*normal)]))]:
    bb=np.array(s.bounding_box());hh=[]
    for k,v in obs.items():
     vb=obb[k]
     if np.any(np.minimum(bb[3:],vb[3:])<=np.maximum(bb[:3],vb[:3])):continue
     vol=float((s^v).volume())
     if vol>1e-4:hh.append({'part':k,'volume':vol})
    tests[tag]=hh
   alts.append({'point':point.tolist(),'normal':normal.tolist(),'tests':tests})
  rows.append({'body':body,'part':e['part'],'alternatives':alts});best=sorted(alts,key=lambda a:sum(h['volume'] for h in a['tests']['root']))[:2];print('ROOT',body,e['part'],[(a['point'],a['tests']) for a in best],flush=True)
 save('current_port_diagnosis.json',{'parts':rows})
