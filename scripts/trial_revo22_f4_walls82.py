from pathlib import Path
import sys,json,shutil,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,parent,variant=spec.split(':');label='walls82_'+variant;src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 try:
  for sub,ext in [('parts','npz'),('design','json')]:
   (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
  (dst/'verification').mkdir(exist_ok=True);p=dst/'design'/f'{pid}.json';d=json.loads(p.read_text());d['slicing_trial_parent']=parent;over=d.get('required_process_overrides',{}).copy()
  if variant=='classic':d['required_wall_generator']='classic';over.update(detect_thin_wall='0')
  elif variant=='length':d['required_wall_generator']='arachne';over.update(min_length_factor='2')
  elif variant=='feature':d['required_wall_generator']='arachne';over.update(min_feature_size='50%')
  else:raise ValueError(variant)
  d['required_process_overrides']=over;p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);check(pid,label);q=refine(pid,label)
  if q['native_review_resolved']:
   if 'body_change'in d:fit(pid,label)
   geom(pid,label)
  return {k:q[k]for k in['id','label','external_island_count','critical_external_count','native_review_resolved']}
 except Exception:return {'spec':spec,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());print('WALL82_RESULT',out[-1],flush=True);(O/'walls82_progress.json').write_text(json.dumps(out,indent=2))
