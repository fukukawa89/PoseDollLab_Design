import json,shutil,traceback,concurrent.futures,numpy as np
from scipy.spatial.transform import Rotation
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,union,box
from o22_material_components import material_components
from prune_revo22_f5_contacts402 import rods
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from optimize_revo22_f5_276 import pick

def run(job):
 axis,deg=job;p='P130';l='tilt421_'+axis+str(deg).replace('-','m').replace('.','p');a=O/'candidates'/p/'reroute417_r4_2';b=O/'candidates'/p/l
 if not(b/'parts'/f'{p}.npz').exists():
  n=dict(np.load(a/'parts'/f'{p}.npz'));d=json.loads((a/'design'/f'{p}.json').read_text());U=Rotation.from_euler(axis,deg,degrees=True).as_matrix();vv=np.r_[n['v'],n['fin_v'],n['teeth_v']]@U.T;off=-vv.min(0);oldfin=solid(n['fin_v'],n['fin_f']);oldteeth=solid(n['teeth_v'],n['teeth_f']);rr=rods(d,oldteeth)
  for vk in ['v','fin_v','teeth_v']:n[vk]=n[vk]@U.T+off
  body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);feet=[]
  for f in material_components(oldfin):
   foot=f^box([-1000,-1000,-.01],[1000,1000,.45]);foot=foot.transform(np.c_[U,off]);feet.append(foot.project().extrude(max(.45,foot.bounding_box()[5]+.15)))
  fin+=union(feet);assert(fin^body).volume()<1e-6;n['fin_v'],n['fin_f']=vf(fin)
  for i,r,s in rr:
   key=f'rot421_stem{i}';n[key+'_v'],n[key+'_f']=vf(s.transform(np.c_[U,off]));d['local_route_repairs'][i]['mesh_key']=key
  for coll in ['teeth','local_route_repairs']:
   for r in d.get(coll,[]):
    for k in ['root','tip','target']:
     if k in r:r[k]=(U@np.array(r[k])+off).tolist()
    for k in ['normal','removal_vector','stem_removal_vector']:
     if k in r:r[k]=(U@np.array(r[k])).tolist()
  d['orientation']['matrix']=(U@np.array(d['orientation']['matrix'])).tolist();d['orientation']['source_translation_mm']=(U@np.array(d['orientation']['source_translation_mm'])+off).tolist();d['orientation']['size_mm']=np.ptp(n['v'],axis=0).tolist();d['f4_to_current_matrix']=(U@np.array(d['f4_to_current_matrix'])).tolist();d['f4_to_current_translation_mm']=(U@np.array(d['f4_to_current_translation_mm'])+off).tolist();d.update(trial=l,tilt_refinement_deg={axis:deg},temporary_base_extensions=True,support_count=len(material_components(fin)),support_volume_mm3=float((fin+solid(n['teeth_v'],n['teeth_f'])).volume()))
  for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
  np.savez_compressed(b/'parts'/f'{p}.npz',**n);put(b/'design'/f'{p}.json',d)
  for fn in ['guards.npz','strict_magnet_guards.npz']:
   gn=np.load(a/'verification'/fn);gv,gf=vf(solid(gn['v'],gn['f']).transform(np.c_[U,off]));np.savez_compressed(b/'verification'/fn,v=gv,f=gf)
  print('TILT421_BUILT',l,flush=True)
 q=audit(p,l)
 if q['native_review_resolved']:geo(p,l);assert pick(p)
 return l,q['native_review_resolved']
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,j):j for j in [('x',-1.),('x',1.),('y',-1.),('y',1.)]}
  for f in concurrent.futures.as_completed(fs):
   try:print('TILT421_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('TILT421_ERROR',fs[f],flush=True)
