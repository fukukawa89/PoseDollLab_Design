from pathlib import Path
import sys,json,traceback,concurrent.futures
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_low_compact_targets import repair
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 p,l=spec.split(':');label='low_compact51'
 try:
  repair(p,l,label);d=refine(p,label);out={k:d[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']};print('LOW_COMPACT51_RESULT',out,flush=True)
  if d['native_review_resolved']:
   r=json.loads((O/'candidates'/p/label/'design'/f'{p}.json').read_text())
   if 'body_change' in r:out['fit']=fit(p,label)['fit_and_pose_geometry_passed']
   out['geometry']=geom(p,label)['geometric_constraints_passed']
  return out
 except Exception:return {'id':p,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s) for s in sys.argv[1:]]):
   out.append(f.result());(O/'low_compact51_progress.json').write_text(json.dumps(out,indent=2))
