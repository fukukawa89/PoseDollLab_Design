from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from select_revo22_f4_repairs import select,O
from verify_revo22_f4_repaired_geometry import check

def one(q):
 try:
  d=check(q['id'],q['label']);return {k:d[k] for k in ['id','label','failures','geometric_constraints_passed']}
 except Exception:return {'id':q['id'],'label':q['label'],'error':traceback.format_exc()}
if __name__=='__main__':
 jobs=[q for q in select() if q['eligible_before_fin_geometry_check']];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,q) for q in jobs]):
   out.append(f.result());(O/'selected_geometry_progress.json').write_text(json.dumps({'complete':len(out),'total':len(jobs),'results':out},indent=2))
 print('SELECTED_GEOMETRY_DONE',len(out),flush=True)
