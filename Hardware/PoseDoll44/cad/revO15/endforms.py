"""Add real head, palm and split sole forms to the connected prototype.
Forms are fused to a single rigid body, never across a movable joint.
"""
from common import *
from layout_fullbody import *
from connected import build_connected,carrier_inputs,adjacent_pairs
from carriers_swept import Router,ASSEMBLY_POSE,motion_bank

VARIANT='carriers_finished'

def transform_at(key,meta,T):
 return T[key.split('/',1)[1]] if key.startswith('frame/') else meta[key]['transform']

def swept_connected(body,pp,mm,base_meta,T,bank,related):
 obs={};seen={};inverses={k:np.linalg.inv(transform_at(k,base_meta,T)) for k in pp}
 for name,meta,t in bank:
  B=T[body]@np.linalg.inv(t[body])
  for k,s in pp.items():
   if k=='frame/'+body:continue
   mods=set(mm[k].get('modules',[mm[k]['module']]))
   if not mods&related:
    if name=='assembly':obs[k]=s
    continue
   M=B@transform_at(k,meta,t)@inverses[k];stamp=tuple(np.round(M,7).ravel())
   if stamp in seen.setdefault(k,set()):continue
   seen[k].add(stamp);obs[k+'@'+name]=pose(s,M[:3,:3],M[:3,3])
 return obs

def oval_yz(center,w,h,t):
 s=cyl(1,-t/2,t/2,96).scale([w/2,h/2,1]);return pose(s,np.c_[[0,1,0],[0,0,1],[1,0,0]],center)

def rounded_plate(lo,hi,r=3):
 lo=np.array(lo);hi=np.array(hi)
 return md.Manifold.batch_hull([cyl(r,lo[2],hi[2],48).translate([x,y,0]) for x in (lo[0]+r,hi[0]-r) for y in (lo[1]+r,hi[1]-r)])

def candidates_for(body,refT,T):
 if body=='head':
  tip=refT['head_tip'][:3,3]
  for dx,dz in sorted(itertools.product((32,38,44,50),(0,5,-5,10)),key=lambda q:q[0]+abs(q[1])):
   c=np.array([tip[0]+dx,0,tip[2]-20+dz]);s=oval_yz(c,34,40,4)-oval_yz(c+[0,0,1],25,29,7)
   # Nose marker and brow remain on this one terminal output body.
   s+=rounded_plate([c[0]-2,-3,c[2]-3],[c[0]+5,3,c[2]+3],1)
   s+=beam(c+[0,-14,6],c+[0,14,6],1.8)+beam(c,c+[0,0,6],1.8)
   yield s,c+[0,0,18],{'center_world_mm':c.tolist(),'reference_tip_mm':tip.tolist(),'form':'open head outline; forward nose marker'}
 elif body.startswith('hand_'):
  tip=refT['hand_tip_'+body[-1]][:3,3]
  for dx,dz,dy in sorted(itertools.product((0,10,-10,20,-20,30),(0,-10,-20,-30),(0,10,-10)),key=lambda q:np.linalg.norm(q)):
   c=tip+[dx,dy,dz];s=oval_yz(c,18,27,4);s-=oval_yz(c+[0,0,-2],7,12,7)
   yield s,c+[0,0,11],{'center_world_mm':c.tolist(),'reference_tip_mm':tip.tolist(),'form':'palm grip outline'}
 elif body.startswith(('foot_','ball_')):
  side=body[-1];center=refT['foot_'+side][:3,3];x0,x1=(-22,18) if body.startswith('foot_') else (44,72)
  for dz,dy,shorten in itertools.product((0,-3,-6),(0,3,-3),(0,5,10)):
   lo=[x0+shorten,center[1]-16+dy,-3+dz];hi=[x1,center[1]+16+dy,.5+dz];s=rounded_plate(lo,hi);c=(np.array(lo)+hi)/2
   yield s,c+[0,0,1],{'bounds_world_mm':[lo,hi],'form':'heel sole' if body.startswith('foot_') else 'separate moving toe sole'}

def main(char='quinn'):
 base_variant='carriers_swept';rr,frames,hashes=carrier_inputs(char,base_variant)
 if rr['status']!='ROUTING_GENERATED' or any(x['issues'] or x['mesh']['components']!=1 for x in rr['frames']):raise RuntimeError('Complete connected carriers are required before end forms')
 pp,mm,st,f,pr,_=build_connected(char,ASSEMBLY_POSE,base_variant);_,base_meta,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);T,_=fk(pr,ASSEMBLY_POSE)
 refT,_=fk(read(G3/f'layouts/{char}/anatomy_profile.json'),{});Tzero,_=fk(build(char,{},geometry=False)[4],{});bank=motion_bank(char);adj=adjacent_pairs(char);records=read(OUT/f'{base_variant}/{char}_routing.json')['frames'];by={r['body']:r for r in records};rows=[]
 for body in ('head','hand_l','hand_r','ball_l','ball_r','foot_l','foot_r'):
  rec=by[body];ownmods=set(k.split('/')[0] for k in rec['replaces']);related=set(ownmods)
  for pair in adj:
   if pair&ownmods:related.update(pair)
  obs=swept_connected(body,pp,mm,base_meta,T,bank,related);router=Router(obs,5 if body.startswith(('foot_','ball_')) else 3.6)
  M=T[body]@np.linalg.inv(Tzero[body]);starts=[np.array(p[-1]) for p in rec['paths_world_mm'] if len(p)>1];selected=None;attempts=[]
  for index,(shape,end,description) in enumerate(candidates_for(body,refT,Tzero)):
   s=pose(shape,M[:3,:3],M[:3,3]);b=M[:3,:3]@end+M[:3,3]
   if not router.clear_shape(s):attempts.append({'candidate':index,'cause':'FORM_CONTACT'});continue
   for a in sorted(starts,key=lambda a:np.linalg.norm(a-b)):
    route=router.path(a,b)
    if route is None:continue
    neck=md.Manifold()
    for p0,p1 in zip(route,route[1:]):neck+=beam(p0,p1,router.r)+md.Manifold.sphere(router.r,24).translate(p0)+md.Manifold.sphere(router.r,24).translate(p1)
    fused=pp['frame/'+body]+s+neck
    if solid_count(fused)!=1:continue
    selected=(fused,description,route,index);break
   if selected:break
   attempts.append({'candidate':index,'cause':'NO_CONNECTED_ROUTE'})
  if selected:
   s,description,path,index=selected;pp['frame/'+body]=s;I=np.linalg.inv(T[body]);frames[body]=pose(s,I[:3,:3],I[:3,3]);rec['mesh']=mesh_record(s);rec['terminal_form']={**description,'candidate':index,'path_world_mm':[p.tolist() for p in path]};rows.append({'body':body,'selected':rec['terminal_form'],'attempts':attempts});print('END FORM',char,body,'candidate',index,flush=True)
  else:
   rec['issues'].append({'cause':'END_FORM_ROUTE_FAILED'});rows.append({'body':body,'selected':None,'attempts':attempts});print('END FORM BLOCKED',char,body,flush=True)
  save(f'{VARIANT}/{char}_endforms.json',{'rows':rows})
 dst=OUT/f'{VARIANT}/{char}_parts.npz';dst.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(dst,**{k:tri(v) for k,v in frames.items()})
 inputs={str(p):sha(p) for p in [Path(__file__),OUT/f'{base_variant}/{char}_parts.npz',OUT/f'{base_variant}/{char}_routing.json']};inputs.update(rr['input_sha256'])
 save(f'{VARIANT}/{char}_routing.json',{**rr,'status':'ROUTING_GENERATED' if not any(r['issues'] for r in records) else 'END_FORMS_BLOCKED','frames':records,'input_sha256':inputs,'mesh_sha256':sha(dst),'scope':'Connected carriers and end forms checked against sampled adjacent motion; no physical test or continuous clearance proof.'})
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn')
