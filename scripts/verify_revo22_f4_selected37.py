from pathlib import Path
import sys,json,concurrent.futures,traceback,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from select_revo22_f4_repairs import select
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from o22_mesh_identity import body_sha
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(q):
 p,l=q['id'],q['label'];f=O/'candidates'/p/l
 try:
  if q['body_changed']:
   report=f/'verification/body_change_fit_and_pose.json';d=json.loads(report.read_text()) if report.exists() else {}
   if d.get('body_mesh_sha256')!=body_sha(np.load(f/'parts'/f'{p}.npz')):fit(p,l)
  g=geom(p,l);return {'id':p,'label':l,'passed':g['geometric_constraints_passed'],'failures':g['failures']}
 except Exception:return {'id':p,'label':l,'passed':False,'error':traceback.format_exc()}
if __name__=='__main__':
 jobs=[q for q in select() if q['eligible_before_fin_geometry_check']];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,q) for q in jobs]):
   out.append(f.result());(O/'selected_geometry_progress.json').write_text(json.dumps({'total':len(jobs),'completed':len(out),'passed':sum(q['passed'] for q in out),'results':out},indent=2))
 print('GEOMETRY_BATCH_DONE',len(out),sum(q['passed'] for q in out),flush=True)
