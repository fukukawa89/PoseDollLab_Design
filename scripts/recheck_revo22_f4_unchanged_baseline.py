from pathlib import Path
import sys,json,shutil,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(pid):
 try:
  label='baseline_recheck';d=O/'candidates'/pid/label
  for sub,ext in [('parts','npz'),('design','json')]:
   (d/sub).mkdir(parents=True,exist_ok=True);shutil.copy2(O/sub/f'{pid}.{ext}',d/sub/f'{pid}.{ext}')
  (d/'verification').mkdir(exist_ok=True)
  if not (d/'verification/local_extrusion.json').exists():run(pid,label)
  q=check(pid,label);r={k:q[k] for k in ['id','label','critical_external_count','external_island_count','max_external_free_run_mm','native_review_resolved']};print('BASELINE_RESULT',r,flush=True);return r
 except Exception:return {'id':pid,'error':traceback.format_exc()}
if __name__=='__main__':
 ids=[p.stem for p in (O/'parts').glob('*.npz')];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,pid) for pid in ids]):
   out.append(f.result());(O/'baseline_recheck_progress.json').write_text(json.dumps({'completed':len(out),'total':len(ids),'results':out},indent=2))
 print('BASELINE_RECHECK_DONE',len(out),flush=True)
