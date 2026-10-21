"""Attempt external-only supports on the best rigid-tilt candidate; isolated from release."""
import json,sys,copy,os,shutil,types,numpy as np
import o22f6_holeclear as h
pid='P130';base=h.WORK/'tilt_trials/P130_xm20_v3';work=base/'external_route';stage=work/'batch';src='tilted';label='guarded_fine';folder=work/f'candidates/{pid}/{src}'
for sub in ['parts','design','verification','projects']:(folder/sub).mkdir(parents=True,exist_ok=True)
shutil.copy2(base/f'batch/parts/{pid}.npz',folder/f'parts/{pid}.npz');d=json.loads((base/f'batch/design/{pid}.json').read_text());U=np.array(d['f6_tilt_trial']['rotation_matrix']);off=np.array(d['f6_tilt_trial']['translation_mm'])
for group in ['teeth','local_route_repairs']:
 for q in d.get(group,[]):
  for key in ['root','tip','target']:
   if key in q and len(q[key])==3:q[key]=(U@np.array(q[key])+off).tolist()
  if 'removal_vector'in q:q['removal_vector']=(U@np.array(q['removal_vector'])).tolist()
d['segments']=[];h.put(folder/f'design/{pid}.json',d);shutil.copy2(base/f'guards/{pid}.npz',folder/'verification/guards.npz');p=json.loads((base/'plate.json').read_text());r=json.loads((base/f"audit/plates/{p['id']}/support_paths.json").read_text());h.put(folder/'verification/native_final.json',r);h.put(folder/'verification/plate_manifest.json',dict(items=p['items']))
code=(h.R/'scripts/route_revo22_f5_native272.py').read_text().replace("for q in rootrecs+records}","for q in rootrecs+records if 'root'in q}")
m=types.ModuleType('tilt_external_router');exec(compile(code,'tilt_external_router','exec'),m.__dict__);m.O=work;oldsolid=m.solid;m.solid=lambda v,f:oldsolid(v,f).set_tolerance(1e-5)
result=m.run(pid,src,label,max_targets=60,tip_width=.45);print('TILT_ROUTED',len(result['unrouted_native_targets']),flush=True)
for sub in ['parts','design']:
 (stage/sub).mkdir(parents=True,exist_ok=True)
 for fp in (base/'batch'/sub).glob('*'):
  dest=stage/sub/fp.name
  if not dest.exists():os.link(fp,dest)
 dest=stage/sub/f'{pid}'+'' if False else stage/sub/f'{pid}.npz' if sub=='parts' else stage/sub/f'{pid}.json'
 dest.unlink();shutil.copy2(work/f'candidates/{pid}/{label}/{sub}/{dest.name}',dest)
h.OUT=stage;h.WORK=work/'audit';h.put(h.WORK/'profile_overrides.json',json.loads((base/'audit/profile_overrides.json').read_text()));h.build_plate(p);r=h.screen_plate(p);h.put(work/'result.json',dict(islands=r['external_island_count'],critical=r['critical_external_count']));print('TILT_ROUTE_RESULT',r['external_island_count'],r['critical_external_count'],flush=True)