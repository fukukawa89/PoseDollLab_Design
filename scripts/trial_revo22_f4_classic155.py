from pathlib import Path
import sys,json,shutil,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
from verify_revo22_f4_repaired_geometry import check as geom
from verify_revo22_f4_body_change import check as fit
from o22_mesh_identity import body_sha
import numpy as np
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(spec):
 pid,parent,feature=spec.split(':');label='classic155_'+parent;src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 try:
  for sub,ext in [('parts','npz'),('design','json')]:
   (dst/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(src/sub/f'{pid}.{ext}',dst/sub/f'{pid}.{ext}')
  (dst/'verification').mkdir(exist_ok=True);dp=dst/'design'/f'{pid}.json';d=json.loads(dp.read_text());d['required_wall_generator']='classic';d.setdefault('required_process_overrides',{})['detect_thin_wall']='0';d['slicing_trial_parent']=parent;d['micro_feature_policy']={'thin_wall_detection':False,'nozzle_mm':.4,'no_change_to_CAD_body_or_support_mesh':True,'full_native_recheck_required':True};dp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');fp=src/'verification/body_change_fit_and_pose.json'
  if fp.exists():
   f=json.loads(fp.read_text());assert f['body_mesh_sha256']==body_sha(np.load(dst/'parts'/f'{pid}.npz'))
   shutil.copy2(fp,dst/'verification/body_change_fit_and_pose.json')
  run(pid,label);check(pid,label);q=refine(pid,label)
  if q['native_review_resolved']:
   if ('body_change'in d or'nominal_reference'in d)and not fp.exists():fit(pid,label)
   geom(pid,label)
  print('FEATURE139',pid,label,q['external_island_count'],q['critical_external_count'],flush=True);return {'id':pid,'label':label,'islands':q['external_island_count'],'critical':q['critical_external_count']}
 except Exception:return {'spec':spec,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(trial,s)for s in sys.argv[1:]]):out.append(f.result());(O/'classic155_progress.json').write_text(json.dumps(out,indent=2))
