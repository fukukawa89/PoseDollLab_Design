from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from select_revo22_f4_repairs import select
from repair_revo22_f4_lower_root_targets import repair
from verify_revo22_f4_repaired_geometry import check as geom
from verify_revo22_f4_body_change import check as fit
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(q):
 p=q['id'];old=q['label'];label='lower_root_12';dst=O/'candidates'/p/label
 try:
  if (dst/'verification/full_bead_contacts.json').exists():r=json.loads((dst/'verification/full_bead_contacts.json').read_text())
  else:r=repair(p,old,label)
  d=json.loads((dst/'design'/f'{p}.json').read_text())
  if 'body_change' in d and r['native_review_resolved']:fit(p,label)
  if r['native_review_resolved']:geom(p,label)
  z={k:r[k] for k in ['id','label','critical_external_count','external_island_count','native_review_resolved']};print('LOWER_ROOT_RESULT',z,flush=True);return z
 except Exception:return {'id':p,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 qs=[q for q in select() if not q['eligible_before_fin_geometry_check']];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,q) for q in qs]):
   out.append(f.result());(O/'lower_root_12_progress.json').write_text(json.dumps({'completed':len(out),'total':len(qs),'results':out},indent=2))
 print('LOWER_ROOT_BATCH_DONE',len(out),flush=True)
