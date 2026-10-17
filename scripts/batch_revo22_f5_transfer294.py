import json,sys,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from transfer_revo22_f5_family289 import build
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit

def run(pair):
 pid,ref=pair
 label=build(pid,ref);q=audit(pid,label)
 if q['native_review_resolved']:
  g=geo(pid,label)
  if g['body_change_fit_and_pose_required']:assert fit(pid,label)['fit_and_pose_geometry_passed']
  assert pick(pid)
 print('TRANSFER294',pid,ref,q['native_review_resolved'],flush=True)
 return(pid,ref,q['native_review_resolved'])
if __name__=='__main__':
 groups=json.loads((O/'rigid_families286.json').read_text())['groups'];sels={p.stem:json.loads(p.read_text()) for p in(O/'selections').glob('*.json')};pairs=[]
 for g in groups:
  good=[]
  for p in g:
   if p not in sels:continue
   if not sels[p].get('body_modified',False):good.append(p);continue
   fp=O/'candidates'/p/sels[p]['label']/'verification/f5_fit_and_pose.json'
   if fp.exists()and json.loads(fp.read_text()).get('fit_and_pose_geometry_passed'):good.append(p)
  if not good:continue
  ref=min(good,key=lambda p:(sels[p].get('body_modified',False),sels[p]['support_volume_mm3']))
  for pid in g:
   if pid!=ref and (pid not in sels or (sels[pid].get('body_modified',False)and not sels[ref].get('body_modified',False))):pairs.append((pid,ref))
 print('TRANSFER_PLAN',pairs,flush=True)
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in pairs}
  for f in concurrent.futures.as_completed(fs):
   try:f.result()
   except Exception:traceback.print_exc();print('TRANSFER_ERROR',fs[f],flush=True)
