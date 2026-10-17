from pathlib import Path
import sys,json,traceback,concurrent.futures,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from slice_revo22_f4_candidate import run
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(task):
 pid,label=task
 try:
  path=O/'candidates'/pid/label/'verification/local_extrusion.json'
  r=json.loads(path.read_text(encoding='utf8')) if path.exists() else run(pid,label)
  return {'id':pid,'label':label,'detached':len(r['detached_bead_regions']),'unresolved':r['unresolved_count'],'max_span_mm':r['max_unresolved_span_mm'],'native_slicing_complete':True}
 except Exception:return {'id':pid,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 tasks=[];choices=[]
 for f in (O/'candidates').glob('*/coverage_comparison.json'):
  rows=[r for r in json.loads(f.read_text(encoding='utf8')) if 'audit' in r]
  def score(r):
   a=r['audit'];return a['max_local_excess_area_mm2']*25+a['sum_layer_excess_area_mm2']+r['support_count']*.1
  r=min(rows,key=score);label=f"cov_{r['index']:02}";tasks.append((r['id'],label));choices.append({'id':r['id'],'label':label,'reason':'Lowest weighted maximum and total uncovered section area among four candidates, for native review only. Not accepted for printing.'})
 tasks.sort(key=lambda t:(t[0]!='X046',t[0]));(O/'native_review_choices.json').write_text(json.dumps(choices,ensure_ascii=False,indent=2),encoding='utf8');done=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  futures={pool.submit(one,t):t for t in tasks}
  for f in concurrent.futures.as_completed(futures):
   r=f.result();done.append(r);(O/'native_candidate_progress.json').write_text(json.dumps({'completed':len(done),'total':len(tasks),'results':done},ensure_ascii=False,indent=2),encoding='utf8');print('NATIVE_CANDIDATE_RESULT',r,flush=True)
 print('NATIVE_CANDIDATES_COMPLETE',len(done),flush=True)
