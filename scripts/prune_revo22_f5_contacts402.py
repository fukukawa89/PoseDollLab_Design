import sys,json,shutil,traceback,concurrent.futures,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,md,union,box
from o22_material_components import material_components
from verify_revo22_x062_removal245 import exact_clear
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def rods(d,teeth):
 out=[];xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]])
 for i,r in enumerate(d.get('local_route_repairs',[])):
  if r.get('kind')!='extractable_void_contact_341':continue
  a=np.array(r['root']);b=np.array(r['tip']);h=r.get('taper_height_mm',.45);mid=b-[0,0,h]if r.get('contact_pad')else a+(b-a)*max(0.,1-h/(b[2]-a[2]));tt=union([md.Manifold.hull_points(np.r_[xy*.4+a,xy*.4+mid]),md.Manifold.hull_points(np.r_[xy*.4+mid,xy*(r.get('tip_width_mm',.6)/2)+b])]);tt=tt^teeth;out.append((i,r,tt))
 return out

def create(p,src):
 a=O/'candidates'/p/src;d=json.loads((a/'design'/f'{p}.json').read_text());n=dict(np.load(a/'parts'/f'{p}.npz'));body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);rr=rods(d,teeth);free=[s-body-fin for _,_,s in rr];choices=[]
 if p=='X046':
  keep=[]
  for j,(i,r,s)in enumerate(rr):
   ok=exact_clear(s-body,body,np.array(r['stem_removal_vector'])*220)[0]
   if ok:keep.append(j)
   else:print('PRUNE402_BAD',p,i,flush=True)
  choices=[keep]
 else:
  conflicts={i:set()for i in range(len(rr))}
  for i in range(len(rr)):
   for j in range(i+1,len(rr)):
    if(free[i]^free[j]).volume()>1e-6:conflicts[i].add(j);conflicts[j].add(i)
  print('PRUNE402_GRAPH',p,len(rr),sum(map(len,conflicts.values()))//2,flush=True)
  orders=[list(reversed(range(len(rr)))),sorted(range(len(rr)),key=lambda i:len(conflicts[i])),list(range(len(rr)))]
  rng=np.random.default_rng(402)
  for k in range(3):orders.append(rng.permutation(len(rr)).tolist())
  for order in orders:
   keep=[]
   for i in order:
    if not any(j in conflicts[i]for j in keep):keep.append(i)
   if set(keep)not in[set(x)for x in choices]:choices.append(keep)
 base=teeth-union([s for _,_,s in rr]);jobs=[]
 for k,keep in enumerate(choices):
  l=f'prune402_{k}';b=O/'candidates'/p/l
  if not(b/'parts'/f'{p}.npz').exists():
   ts=base+union([rr[j][2]for j in keep]);ts=union([c for c in material_components(ts)if(c^body).volume()>.005 and(c^fin).volume()>.005]);nf=union([f for f in material_components(fin)if(f^ts).volume()>.005])
   for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
   nn=dict(n);nn['fin_v'],nn['fin_f']=vf(nf);nn['teeth_v'],nn['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{p}.npz',**nn);dd=json.loads(json.dumps(d));ids={rr[j][0]for j in keep};dd['local_route_repairs']=[r for i,r in enumerate(d['local_route_repairs'])if r.get('kind')!='extractable_void_contact_341'or i in ids];dd.update(trial=l,new_tooth_count=d['new_tooth_count']-len(rr)+len(keep),support_count=len(material_components(nf)),support_volume_mm3=float((nf+ts).volume()),pruned_new_contact_indices=[rr[j][0]for j in range(len(rr))if j not in keep]);put(b/'design'/f'{p}.json',dd)
   for fn in ['guards.npz','strict_magnet_guards.npz']:shutil.copy2(a/'verification'/fn,b/'verification'/fn)
  jobs.append((p,l));print('PRUNE402_BUILT',p,l,len(rr)-len(keep),'removed',flush=True)
 return jobs

def run(j):
 p,l=j;q=audit(p,l)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p)
 return p,l,q['native_review_resolved']
if __name__=='__main__':
 jobs=[]
 for p,src in [('P130','orient398_r2_route2'),('X046','cap396_0')]:jobs+=create(p,src)
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('PRUNE402_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('PRUNE402_ERROR',fs[f],flush=True)
