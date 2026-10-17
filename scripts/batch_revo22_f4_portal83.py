from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_portal_short83 import trial
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,parent=spec.split(':');label='portal83'
 try:
  trial(pid,parent,label);p=O/'candidates'/pid/label
  if not(p/'verification/full_bead_contacts.json').exists():return {'id':pid,'added':0}
  q=refine(pid,label)
  if q['native_review_resolved']:
   d=json.loads((p/'design'/f'{pid}.json').read_text())
   if 'body_change'in d:fit(pid,label)
   geom(pid,label)
  return {k:q[k]for k in['id','label','external_island_count','critical_external_count','native_review_resolved']}
 except Exception:return {'spec':spec,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());print('PORTAL83_RESULT',out[-1],flush=True);(O/'portal83_progress.json').write_text(json.dumps(out,indent=2))
