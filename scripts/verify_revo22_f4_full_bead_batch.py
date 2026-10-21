from pathlib import Path
import sys,json,traceback,concurrent.futures
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,label=spec
 try:
  d=check(pid,label);r={k:d[k] for k in ['id','label','critical_external_count','external_island_count','max_external_free_run_mm','native_review_resolved']};print('BEAD_RESULT',r,flush=True);return r
 except Exception:return {'id':pid,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 specs=[]
 for p in (O/'candidates').glob('*/contact_full_02/verification/local_extrusion.json'):specs.append((p.parents[2].name,p.parents[1].name))
 if sys.argv[1:]:specs=[tuple(v.split(':')) for v in sys.argv[1:]]
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s) for s in specs]):
   out.append(f.result());(O/'full_bead_batch_progress.json').write_text(json.dumps({'completed':len(out),'total':len(specs),'results':out},indent=2))
 print('BEAD_BATCH_DONE',len(out),flush=True)
