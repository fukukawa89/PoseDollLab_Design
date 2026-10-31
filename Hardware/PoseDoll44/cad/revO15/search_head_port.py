from carriers_swept import *
char='quinn';pp,meta,states,fail,prof=build(char,ASSEMBLY_POSE);T,_=fk(prof,ASSEMBLY_POSE);aa=anchors(states,meta);bank=motion_bank(char);adj=adjacent_pairs(char);body='chest';ends=aa[body];ids=[e['part'] for e in ends];ownmods={meta[k]['module'] for k in ids};related=set(ownmods)
for pair in adj:
 if pair&ownmods:related.update(pair)
obs=swept_obstacles(body,ids,related,pp,meta,T,bank,{});router=Router(obs);m=next(m for m in states if m['id']=='head');M=np.array(m['world_mount']);O=np.array(m['origin_mm']);solutions=[];tested=0
for z in (-23.3,-21.8,-25.3,-28.3,-30.9,-32.0):
 for deg in (180,195,210,225,240,255,270,285,300,315,330,345,360):
  a=np.deg2rad(deg);point=np.array([11.4*np.cos(a),11.4*np.sin(a),z-1.5]);wp=M@point+O;overlap=float((pp['head/P_case_minus']^md.Manifold.sphere(2.6,16).translate(wp)).volume())
  if overlap<8:continue
  for nz in (0,-.5,.5,-1,1):
   n=unit([np.cos(a),np.sin(a),nz]);v=M@n;tested+=1;path=router.escape(wp,v)
   if path is not None:solutions.append({'point_local':point.tolist(),'normal_local':n.tolist(),'length':float(np.linalg.norm(path[1]-path[0])),'overlap':overlap});print('FOUND',solutions[-1],flush=True)
save('head_port_search.json',{'tested':tested,'solutions':solutions,'sweep_samples':len(bank),'source_sha256':sha(Path(__file__).with_name('layout_fullbody.py'))})
print('HEAD_PORT_RESULT',len(solutions),'of',tested,flush=True)
