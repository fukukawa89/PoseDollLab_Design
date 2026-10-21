import sys,json,shutil,traceback,concurrent.futures,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,box,union
from o22_material_components import material_components
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def create(pid,src,drop):
 label='phase369_'+str(round(drop*1000));a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if(b/'parts'/f'{pid}.npz').exists():return label
 n=dict(np.load(a/'parts'/f'{pid}.npz'));d=json.loads((a/'design'/f'{pid}.json').read_text());delta=np.array([0.,0.,-drop]);assert n['v'][:,2].min()>=drop-1e-6
 for k in ['v','fin_v','teeth_v','f5_pre_relief_v']:
  if k in n:n[k]=n[k]+delta
 body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f'])^box([-1000,-1000,0],[1000,1000,1000]);ts=solid(n['teeth_v'],n['teeth_f'])^box([-1000,-1000,0],[1000,1000,1000]);ts=union([t for t in material_components(ts)if(t^body).volume()>.005 and(t^fin).volume()>.005]);fin=union([f for f in material_components(fin)if(f^ts).volume()>.005]);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(ts)
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 np.savez_compressed(b/'parts'/f'{pid}.npz',**n)
 for name in ['guards.npz','strict_magnet_guards.npz']:
  fp=a/'verification'/name
  if fp.exists():
   gn=dict(np.load(fp));gn['v']+=delta;np.savez_compressed(b/'verification'/name,**gn)
 for key in ['f4_to_current_translation_mm']:
  d[key]=(np.array(d[key])+delta).tolist()
 d['orientation']['source_translation_mm']=(np.array(d['orientation']['source_translation_mm'])+delta).tolist()
 for key in ['teeth','local_route_repairs','f5_reliefs','f5_additions','temporary_fin_gussets']:
  for r in d.get(key,[]):
   for k in ['root','tip','target','point']:
    if k in r:r[k]=(np.array(r[k])+delta).tolist()
   for k in ['local_bounds_mm','bounds_mm']:
    if k in r:r[k]=(np.array(r[k])+np.r_[delta,delta]).tolist()
 d.update(trial=label,teeth_clipped_at_bed=True,bed_drop_mm=drop,support_count=len(material_components(fin)),support_volume_mm3=float((fin+ts).volume()),phase_adjustment_source=src);put(b/'design'/f'{pid}.json',d);return label

def run(job):
 p,src,drop=job;l=create(*job);q=audit(p,l)
 if q['native_review_resolved']:
  g=geo(p,l)
  if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
  assert pick(p)
 return p,l,q['native_review_resolved']
if __name__=='__main__':
 jobs=[('X054','bedroute364_3',6.)]+[(p,l,d)for p,l in [('P130','ends366_0'),('X038','ends366_0'),('X066','ends366_0'),('X046','stem356_1')]for d in [.10,.05,.15]]
 with concurrent.futures.ProcessPoolExecutor(max_workers=4)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('PHASE369_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('PHASE369_ERROR',fs[f],flush=True)
