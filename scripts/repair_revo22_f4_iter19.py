from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_clean_chamfer import trial
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,label=spec.split(':');result=[]
 try:
  for j in range(1,5):
   new='iter19_'+str(j).zfill(2);d=trial(pid,label,new);result.append({k:d[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']});print('ITER19_RESULT',result[-1],flush=True)
   if d['native_review_resolved']:fit(pid,new);geom(pid,new);break
   before=json.loads((O/'candidates'/pid/label/'design'/f'{pid}.json').read_text()).get('body_change',{}).get('removed_volume_mm3',0);after=json.loads((O/'candidates'/pid/new/'design'/f'{pid}.json').read_text()).get('body_change',{}).get('removed_volume_mm3',0)
   if after-before<1e-5:break
   label=new
  return result
 except Exception:return {'id':pid,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s) for s in sys.argv[1:]]):
   out.append(f.result());(O/'iter19_progress.json').write_text(json.dumps(out,indent=2))
