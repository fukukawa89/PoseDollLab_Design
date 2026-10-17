import json,os,sys,concurrent.futures
import o22f6_holeclear as h
BASE=h.WORK;SOURCE=h.OUT

def trial(spec):
 pid,profile=spec;label=pid+'_'+profile;root=BASE/'wall_trials'/label;stage=root/'batch';work=root/'audit'
 for sub in ['parts','design']:
  (stage/sub).mkdir(parents=True,exist_ok=True)
  for fp in(SOURCE/sub).glob('*'):
   dest=stage/sub/fp.name
   if not dest.exists():os.link(fp,dest)
 overrides=json.loads((BASE/'profile_overrides.json').read_text());overrides.setdefault(pid,{})['wall_generator']='classic'
 if profile=='classic_none':overrides[pid]['counterbore_hole_bridging']='none'
 h.put(work/'profile_overrides.json',overrides);p=next(p for p in json.loads((h.SRC/'manifest.json').read_text())['plates']if any(it['id']==pid for it in p['items']));h.OUT=stage;h.WORK=work;h.TARGET_PART_IDS=[pid]
 h.build_plate(p);r=h.screen_plate(p);res=dict(id=pid,label=label,islands=r['external_island_count'],critical=r['critical_external_count']);h.put(root/'result.json',res);print('WALL_RESULT',res,flush=True)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for r in pool.map(trial,[('P130','classic'),('X046','classic'),('P095','classic'),('P095','classic_none')]):pass