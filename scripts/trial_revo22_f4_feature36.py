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
 pid,source,feature=spec.split(':');label='feature36_'+source+'_'+feature;src=O/'candidates'/pid/source;dst=O/'candidates'/pid/label
 try:
  for sub,ext in [('parts','npz'),('design','json')]:
   (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
  (dst/'verification').mkdir(exist_ok=True);p=dst/'design'/f'{pid}.json';d=json.loads(p.read_text());d.setdefault('required_process_overrides',{}).update(min_feature_size=feature+'%');d['slicing_trial_parent']=source;p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);check(pid,label);r=refine(pid,label);out={'id':pid,'label':label,'islands':r['external_island_count'],'critical':r['critical_external_count']};print('FEATURE36_RESULT',out,flush=True)
  if r['native_review_resolved']:
   if 'body_change' in d:out['fit']=fit(pid,label)['fit_and_pose_geometry_passed']
   out['geometry']=geom(pid,label)['geometric_constraints_passed']
  return out
 except Exception:return {'id':pid,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s) for s in sys.argv[1:]]):
   out.append(f.result());(O/'feature36_progress.json').write_text(json.dumps(out,indent=2))
