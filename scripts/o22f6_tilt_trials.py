"""Single-part rigid tilt trials, preserving permanent dimensions and screw exclusions."""
import json,sys,os,copy,concurrent.futures,numpy as np
from scipy.spatial.transform import Rotation
import o22f6_holeclear as h
BASE=h.WORK;SOURCE=h.OUT

def trial(spec):
 pid,axis,angle=spec;label=f'{pid}_{axis}{angle}_v3'.replace('-','m');root=BASE/'tilt_trials'/label;stage=root/'batch';work=root/'audit';print('TILT_START',label,flush=True)
 for sub in ['parts','design']:
  (stage/sub).mkdir(parents=True,exist_ok=True)
  for fp in (SOURCE/sub).glob('*'):
   dest=stage/sub/fp.name
   if not dest.exists():os.link(fp,dest)
 n=dict(np.load(SOURCE/f'parts/{pid}.npz'));U=Rotation.from_euler(axis,angle,degrees=True).as_matrix();orig=np.r_[n['v'],n['fin_v'],n['teeth_v']];vv=orig@U.T;off=-vv.min(0);oldfin=h.solid(n['fin_v'],n['fin_f'])
 for k in [x for x in n if x=='v'or x.endswith('_v')]:
  if n[k].ndim==2 and n[k].shape[1]==3:n[k]=n[k]@U.T+off
 body=h.solid(n['v'],n['f']).set_tolerance(1e-5);fin=h.solid(n['fin_v'],n['fin_f']).set_tolerance(1e-5);teeth=h.solid(n['teeth_v'],n['teeth_f']).set_tolerance(1e-5);n['v'],n['f']=h.vf(body);gn=np.load(BASE/f'guards/{pid}.npz');guard=h.solid(gn['v'],gn['f']).transform(np.c_[U,off]).set_tolerance(1e-5);feet=[]
 for c in h.material_components(oldfin):
  foot=(c^h.box([-1000,-1000,-.01],[1000,1000,.4])).transform(np.c_[U,off]);v=h.vf(foot)[0];down=v.copy();down[:,2]=0;ft=h.md.Manifold.hull_points(np.r_[v,down]);feet.append(ft)
 print('TILT_FEET',label,len(feet),flush=True);feet=h.union(feet).set_tolerance(1e-5);feet=(feet-guard.set_tolerance(1e-5))-body.set_tolerance(1e-5);fin=(fin.set_tolerance(1e-5)+feet);print('TILT_CLEAN',label,flush=True)
 for k in range(1):
  print('TILT_ITER',label,k,flush=True)
  fin=h.union([c for c in h.material_components(fin)if c.bounding_box()[2]<1e-5]);teeth=h.union([c for c in h.material_components(teeth)if(c^body).volume()>.001 and(c^fin).volume()>.001]);fin=h.union([c for c in h.material_components(fin)if(c^teeth).volume()>.001])
 chk=dict(guard_overlap_mm3=float(((fin+teeth)^guard).volume()),body_components=len(h.material_components(body)),whole_components=len(h.material_components(body+fin+teeth)),body_volume_mm3=float(body.volume()),new_fin_mm3=float(fin.volume()))
 h.put(root/'geometry.json',chk);assert chk['guard_overlap_mm3']<1e-6 and chk['body_components']==chk['whole_components'],chk
 for v,f,s in [('fin_v','fin_f',fin),('teeth_v','teeth_f',teeth)]:n[v],n[f]=h.vf(s)
 dest=stage/f'parts/{pid}.npz';dest.unlink();np.savez_compressed(dest,**n);d=json.loads((SOURCE/f'design/{pid}.json').read_text());d['orientation']['matrix']=(U@np.array(d['orientation']['matrix'])).tolist();d['orientation']['source_translation_mm']=(U@np.array(d['orientation']['source_translation_mm'])+off).tolist();d['f6_tilt_trial']=dict(rotation_matrix=U.tolist(),translation_mm=off.tolist(),permanent_body_rigid_transform_only=False,numeric_simplification_tolerance_mm=1e-5)
 dest=stage/f'design/{pid}.json';dest.unlink();h.put(dest,d);h.save_mesh(root/f'guards/{pid}.npz',guard);h.put(work/'profile_overrides.json',json.loads((BASE/'profile_overrides.json').read_text()))
 p=copy.deepcopy(next(p for p in json.loads((h.SRC/'manifest.json').read_text())['plates']if any(it['id']==pid for it in p['items'])));it=copy.deepcopy(next(it for it in p['items']if it['id']==pid));v=np.r_[n['v'],n['fin_v'],n['teeth_v']];bb=np.r_[v.min(0),v.max(0)];shift=np.array([90,90,0])-np.r_[(bb[:2]+bb[3:5])/2,bb[2]];it['rotation_matrix']=np.eye(3).tolist();it['translation_mm']=shift.tolist();it['bounds_mm']=(bb+np.r_[shift,shift]).tolist();p['items']=[it];p['title']='O22F6 单件摆放验证';h.put(root/'plate.json',p)
 h.OUT=stage;h.WORK=work;h.TARGET_PART_IDS=[pid];h.build_plate(p);r=h.screen_plate(p);res=dict(id=pid,label=label,islands=r['external_island_count'],critical=r['critical_external_count'],body_rigid_only=True);h.put(root/'result.json',res);print('TILT_RESULT',res,flush=True)
if __name__=='__main__':
 jobs=[('P130','x',20),('P130','x',-20),('P130','y',20),('P095','x',20)]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for r in pool.map(trial,jobs):pass