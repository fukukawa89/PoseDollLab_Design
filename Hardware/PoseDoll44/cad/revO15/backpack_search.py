"""Search removable backpack envelopes against adjacent swept solids.
No free-space or full-range assertion is inferred from a bounding box alone.
"""
from common import *
from connected import build_connected,carrier_inputs,adjacent_pairs
from layout_fullbody import build,fk
from carriers_swept import ASSEMBLY_POSE,motion_bank,Router
from endforms import swept_connected


def search(char='quinn'):
 pp,mm,st,f,pr,_=build_connected(char,ASSEMBLY_POSE,'carriers_finished');assert not f
 _,meta,_,_,_=build(char,ASSEMBLY_POSE,geometry=False);T,_=fk(pr,ASSEMBLY_POSE);bank=motion_bank(char);adj=adjacent_pairs(char);rr,_,_=carrier_inputs(char,'carriers_finished');rec={r['body']:r for r in rr['frames']};out=[]
 for body,kind,extent in [('chest','controller',[29,100,74]),('pelvis','battery',[31,124,31])]:
  own=set(v.split('/')[0] for v in rec[body]['replaces']);related=set(own)
  for pair in adj:
   if pair&own:related.update(pair)
  obs=swept_connected(body,pp,mm,meta,T,bank,related)
  # Previously placed equipment must sweep with its own body. Independent
  # empty-body fits cannot establish that two moving enclosures fit together.
  for placed in out:
   if 'failed' in placed:continue
   prior=placed['body'];lo,hi=np.array(placed['envelope_mm']);shape=box(lo-.3,hi+.3)
   for path in placed['mount_paths_world_mm']:
    for a,b in zip(path,path[1:]):shape+=beam(a,b,4.25)+md.Manifold.sphere(4.25,16).translate(a)+md.Manifold.sphere(4.25,16).translate(b)
   for name,meta_pose,t in bank:
    M=T[body]@np.linalg.inv(t[body])@t[prior]@np.linalg.inv(T[prior]);obs['previous/'+prior+'@'+name]=pose(shape,M[:3,:3],M[:3,3])
  router=Router(obs,4);entry=None;attempts=[]
  for rear in range(60,151,5):
   for dz in ([28,38,18,48,8] if body=='chest' else [0,-10,10,-20,20]):
    c=np.array([-rear,0,T[body][2,3]+dz]);lo=c+[-extent[0],-extent[1]/2,-extent[2]/2];hi=c+[0,extent[1]/2,extent[2]/2];s=box(lo-.3,hi+.3)
    if not router.clear_shape(s):continue
    # Two independent backplate attachment roots, retained as separate witnesses.
    starts=[np.array(p[-1]) for p in rec[body]['paths_world_mm'] if len(p)>1];ends=[c+[0,y,0] for y in (-22,22)];paths=[]
    for end in ends:
     for start in sorted(starts,key=lambda p:np.linalg.norm(p-end)):
      path=router.path(start,end)
      if path is not None:paths.append([p.tolist() for p in path]);break
    if len(paths)!=2:attempts.append({'rear_mm':rear,'dz_mm':dz,'cause':'NO_TWO_MOUNT_ROUTES'});continue
    entry={'body':body,'kind':kind,'front_center_world_mm':c.tolist(),'envelope_mm':[lo.tolist(),hi.tolist()],'mount_paths_world_mm':paths,'related_modules':sorted(related),'scope':'273 construction samples; requires final finer sweep and actual housing checks'};break
   if entry:break
  out.append(entry or {'body':body,'kind':kind,'failed':True,'attempts':attempts});save('equipment/'+char+'_search.json',{'entries':out,'status':'SEARCHING','physical_tested':False});print('EQUIPMENT',char,body,entry['front_center_world_mm'] if entry else 'FAILED',flush=True)
 save('equipment/'+char+'_search.json',{'entries':out,'status':'ENVELOPES_ROUTED' if all('failed' not in v for v in out) else 'FAILED','input_sha256':{str(p):sha(p) for p in [Path(__file__),OUT/f'carriers_finished/{char}_parts.npz',OUT/f'carriers_finished/{char}_routing.json']},'physical_tested':False})
if __name__=='__main__':search(sys.argv[1] if len(sys.argv)>1 else 'quinn')
