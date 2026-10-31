import sys,json,itertools,shutil,concurrent.futures,traceback,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,md,union
from o22_material_components import material_components
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def rods(d):
 out=[];xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]])
 for i,r in enumerate(d.get('local_route_repairs',[])):
  if r.get('kind')!='extractable_void_contact_341':continue
  a=np.array(r['root']);b=np.array(r['tip']);m=a+(b-a)*max(0.,1-.45/(b[2]-a[2]));s=union([md.Manifold.hull_points(np.r_[xy*.4+a,xy*.4+m]),md.Manifold.hull_points(np.r_[xy*.4+m,xy*.3+b])]);out.append((i,r,s))
 return out

def create(pid):
 a=O/'candidates'/pid/'extract341_0';base=O/'candidates'/pid/'extract341_base';d=json.loads((a/'design'/f'{pid}.json').read_text());n=dict(np.load(a/'parts'/f'{pid}.npz'));bn=np.load(base/'parts'/f'{pid}.npz');body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);rr=rods(d);free=[s-body-fin for _,_,s in rr];conflicts=[(i,j)for i in range(len(rr))for j in range(i+1,len(rr))if(free[i]^free[j]).volume()>1e-6];choices=[]
 for bits in itertools.product([0,1],repeat=len(rr)):
  if sum(bits)<2 or any(bits[i]and bits[j]for i,j in conflicts):continue
  choices.append([i for i,v in enumerate(bits)if v])
 choices.sort(key=lambda v:-len(v));maxn=len(choices[0]);choices=[q for q in choices if len(q)==maxn][:6];jobs=[]
 for k,keep in enumerate(choices):
  lab='prune362_'+str(k);b=O/'candidates'/pid/lab
  for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
  ts=solid(bn['teeth_v'],bn['teeth_f'])+union([rr[j][2]for j in keep]);nf=union([f for f in material_components(fin)if(f^ts).volume()>.005]);nn=dict(n);nn['fin_v'],nn['fin_f']=vf(nf);nn['teeth_v'],nn['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{pid}.npz',**nn);dd=json.loads(json.dumps(d));keepids={rr[j][0]for j in keep};dd['local_route_repairs']=[r for j,r in enumerate(d['local_route_repairs'])if r.get('kind')!='extractable_void_contact_341'or j in keepids];dd.update(trial=lab,new_tooth_count=d['new_tooth_count']-len(rr)+len(keep),support_count=len(material_components(nf)),support_volume_mm3=float((nf+ts).volume()),pruned_new_contact_indices=[i for i in range(len(rr))if i not in keep]);put(b/'design'/f'{pid}.json',dd)
  for name in ['guards.npz','strict_magnet_guards.npz']:shutil.copy2(a/'verification'/name,b/'verification'/name)
  jobs.append((pid,lab));print('PRUNE362_BUILT',pid,lab,keep,flush=True)
 return jobs

def run(job):
 p,l=job;q=audit(p,l)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p)
 return p,l,q['native_review_resolved']
if __name__=='__main__':
 jobs=sum([create(p)for p in sys.argv[1:]],[])
 with concurrent.futures.ProcessPoolExecutor(max_workers=4)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('PRUNE362_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('PRUNE362_ERROR',fs[f],flush=True)
