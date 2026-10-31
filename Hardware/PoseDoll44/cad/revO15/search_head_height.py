from carriers_swept import *
rows=[]
for dz in (4,8,12,16,20,24):
 char='quinn';ov={'head':{'offset_parent_mm':[0,0,dz]}};pp,meta,states,fail,prof=build(char,ASSEMBLY_POSE,overrides=ov);T,_=fk(prof,ASSEMBLY_POSE);aa=anchors(states,meta);bank=motion_bank(char,ov);adj=adjacent_pairs(char);ends=aa['chest'];ids=[e['part'] for e in ends];ownmods={meta[k]['module'] for k in ids};related=set(ownmods)
 for pair in adj:
  if pair&ownmods:related.update(pair)
 obs=swept_obstacles('chest',ids,related,pp,meta,T,bank,{});router=Router(obs);e=next(e for e in ends if e['part']=='head/P_case_minus');found=None
 for point,normal in e['alternatives']:
  path=router.escape(point,normal)
  if path is not None:found={'point':point.tolist(),'normal':normal.tolist()};break
 rows.append({'offset_z_mm':dz,'samples':len(bank),'clear_port':found});print('HEAD_HEIGHT',rows[-1],flush=True);save('head_height_search.json',{'trials':rows,'scope':'Input mount taper versus sampled modules; long carrier still unchecked'})
 if found:break
