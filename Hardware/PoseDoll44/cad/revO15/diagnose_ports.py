from carriers_swept import *
char='quinn';pp,meta,states,fail,prof=build(char,ASSEMBLY_POSE);T,_=fk(prof,ASSEMBLY_POSE);aa=anchors(states,meta);bank=motion_bank(char);adj=adjacent_pairs(char);body='chest';ends=aa[body];ids=[e['part'] for e in ends];ownmods={meta[k]['module'] for k in ids};related=set(ownmods)
for pair in adj:
 if pair&ownmods:related.update(pair)
obs=swept_obstacles(body,ids,related,pp,meta,T,bank,{})
e=next(e for e in ends if e['part']=='head/P_case_minus');rows=[]
for point,normal in e['alternatives']:
 b=point+normal*8;s=md.Manifold.batch_hull([md.Manifold.sphere(2.85,24).translate(point),md.Manifold.sphere(5.25,24).translate(b)]);bb=np.array(s.bounding_box());hh=[]
 for k,v in obs.items():
  vb=np.array(v.bounding_box())
  if np.any(np.minimum(bb[3:],vb[3:])<=np.maximum(bb[:3],vb[:3])):continue
  vol=float((s^v).volume())
  if vol>1e-4:hh.append({'part':k,'volume':vol})
 rows.append({'point':point.tolist(),'hits':hh});print(point, sorted(hh,key=lambda h:-h['volume'])[:5],flush=True)
save('head_port_diagnosis.json',{'trials':rows})
