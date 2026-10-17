"""Finite print-phase trials preserve the permanent part by rigid transforms only."""
import sys,json,shutil,os,concurrent.futures,numpy as np
from scipy.spatial.transform import Rotation
import o22f6_holeclear as h
BASE=h.WORK;SOURCE=h.OUT

def candidate(spec):
 pid,deg,phase,minimum=spec;label=f'{pid}_rx{deg}_z{phase}_min{minimum}'.replace('.','p').replace('-','m');root=BASE/'phase_trials'/label;stage=root/'batch';work=root/'audit'
 for sub in ['parts','design']:
  (stage/sub).mkdir(parents=True,exist_ok=True)
  for fp in (SOURCE/sub).glob('*'):
   dest=stage/sub/fp.name
   if not dest.exists():os.link(fp,dest)
 U=Rotation.from_euler('x',deg,degrees=True).as_matrix();n=dict(np.load(SOURCE/f'parts/{pid}.npz'));orig=np.r_[n['v'],n['fin_v'],n['teeth_v']];v=orig@U.T;off=np.r_[(orig[:,:2].min(0)+orig[:,:2].max(0)-v[:,:2].min(0)-v[:,:2].max(0))/2,phase-v[:,2].min()];oldfin=h.solid(n['fin_v'],n['fin_f'])
 for k in [x for x in n if x=='v' or x.endswith('_v')]:
  if n[k].ndim==2 and n[k].shape[1]==3:n[k]=n[k]@U.T+off
 body=h.solid(n['v'],n['f']);fin=h.solid(n['fin_v'],n['fin_f']);feet=[]
 for c in h.material_components(oldfin):
  foot=(c^h.box([-1000,-1000,-.01],[1000,1000,.45])).transform(np.c_[U,off]);feet.append(foot.project().extrude(max(.45,foot.bounding_box()[5]+.05)))
 fin+=h.union(feet);gn=np.load(BASE/f'guards/{pid}.npz');guard=h.solid(gn['v'],gn['f']).transform(np.c_[U,off]);assert(fin^body).volume()<1e-6;assert(fin^guard).volume()<1e-6
 n['fin_v'],n['fin_f']=h.vf(fin);dest=stage/f'parts/{pid}.npz';dest.unlink();np.savez_compressed(dest,**n);d=json.loads((SOURCE/f'design/{pid}.json').read_text());d['orientation']['matrix']=(U@np.array(d['orientation']['matrix'])).tolist();d['orientation']['source_translation_mm']=(U@np.array(d['orientation']['source_translation_mm'])+off).tolist();d['f6_print_phase_trial']=dict(rotation_matrix=U.tolist(),translation_mm=off.tolist(),permanent_body_rigid_transform_only=True)
 dest=stage/f'design/{pid}.json';dest.unlink();h.put(dest,d);h.save_mesh(root/f'guards/{pid}.npz',guard)
 overrides=json.loads((BASE/'profile_overrides.json').read_text());overrides.setdefault(pid,{})['min_feature_size']=minimum+'%';h.put(work/'profile_overrides.json',overrides)
 p=next(p for p in json.loads((h.SRC/'manifest.json').read_text())['plates']if any(it['id']==pid for it in p['items']));h.OUT=stage;h.WORK=work;h.TARGET_PART_IDS=[pid];h.build_plate(p);r=h.screen_plate(p);result=dict(id=pid,label=label,plate=p['id'],islands=r['external_island_count'],critical=r['critical_external_count'],scope_part_ids=[pid]);h.put(root/'result.json',result);print('PHASE_RESULT',result,flush=True);return result
if __name__=='__main__':
 jobs=[('P095',0,.08,'100'),('P130',-1.,0.,'100'),('X046',0,.1,'100')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for result in pool.map(candidate,jobs):pass