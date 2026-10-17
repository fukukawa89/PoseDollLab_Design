from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_recessed_portal76 import trial,O
from refine_revo22_f4_full_bead import refine

def one(spec):
 pid,parent=spec.split(':');label='recessed76'
 try:
  trial(pid,parent,label);p=O/'candidates'/pid/label/'verification/local_extrusion.json'
  if p.exists():
   d=refine(pid,label);return {k:d[k]for k in['id','label','external_island_count','critical_external_count','native_review_resolved']}
  return {'id':pid,'no_portals_added':True}
 except Exception:return {'id':pid,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());(O/'recessed76_progress.json').write_text(json.dumps(out,indent=2));print('RECESSED76_RESULT',out[-1],flush=True)
