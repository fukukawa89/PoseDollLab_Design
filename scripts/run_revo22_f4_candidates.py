"""Consume completed direction scans, with separate processes and isolated folders."""
from pathlib import Path
import sys,json,time,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_f4_coverage_candidates import one,O
if __name__=='__main__':
 baseline=json.loads((O/'audit/baseline/all_parts.json').read_text(encoding='utf8'));ids={q['id'] for q in baseline['parts'] if q['needs_support_coverage_review']};submitted=set();done=[];started=time.time()
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  active={}
  while len(done)<len(ids):
   ready=sorted(pid for pid in ids-submitted if (O/'orientation_v2'/f'{pid}.json').exists())
   for pid in ready[:max(0,2-len(active))]:
    active[pool.submit(one,pid)]=pid;submitted.add(pid)
   for future in list(active):
    if not future.done():continue
    pid=active.pop(future)
    try:result=future.result();done.append({'id':pid,'result':result})
    except Exception:done.append({'id':pid,'error':traceback.format_exc()})
    (O/'candidate_build_progress.json').write_text(json.dumps({'completed':len(done),'total':len(ids),'active':list(active.values()),'parts':done},ensure_ascii=False,indent=2),encoding='utf8')
   if time.time()-started>7200:raise TimeoutError('Two-hour bounded candidate run ended; resume after inspecting progress.')
   if len(done)<len(ids):time.sleep(2)
 print('COVERAGE_CANDIDATES_DONE',len(done),flush=True)
