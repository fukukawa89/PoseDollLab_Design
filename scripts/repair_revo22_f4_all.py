from pathlib import Path
import sys,json,concurrent.futures,time,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_fast_paths import repair
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(q):
 st=time.time();pid=q['id'];label='contact_full_02'
 try:
  repair(pid,q['label'],label);d=json.loads((O/'candidates'/pid/label/'verification/local_extrusion.json').read_text());r={'id':pid,'label':label,'islands':len(d['detached_bead_regions']),'unresolved':d['unresolved_count'],'max_span':d['max_unresolved_span_mm'],'seconds':time.time()-st};print('REPAIR_DONE',r,flush=True);return r
 except Exception:return {'id':pid,'error':traceback.format_exc()}
if __name__=='__main__':
 choices=json.loads((O/'native_review_choices.json').read_text());choices=[q for q in choices if q['id'] not in ['N003','X001','X079','H006','X038']];choices.sort(key=lambda q:(q['id'] not in ['X046','X038'],q['id']));out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  jobs={pool.submit(one,q):q['id'] for q in choices}
  for f in concurrent.futures.as_completed(jobs):
   r=f.result();out.append(r);print('PROGRESS',len(out),len(choices),r['id'],'ERROR' if 'error' in r else '',flush=True);(O/'repair_pass1_progress.json').write_text(json.dumps({'complete':len(out),'total':len(choices),'results':out},indent=2))
 print('ALL_DONE',len(out),'errors',sum('error' in r for r in out),flush=True)
