from pathlib import Path
import sys,concurrent.futures,json,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from trial_revo22_f4_process45 import trial
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 p,l,tag,settings=spec
 try:
  r=trial(p,l,tag,settings);return {k:r[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']}
 except Exception:return {'id':p,'label':tag,'error':traceback.format_exc()}
if __name__=='__main__':
 specs=[('P001','rot14_00_full_lower','retain_short48',{'min_length_factor':'0'}),('P001','rot14_00_full_lower','retain_micro48',{'min_length_factor':'0','min_feature_size':'5%'}),('P001','solid_gusset46','retain_gusset48',{'min_length_factor':'0'})];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,q) for q in specs]):
   out.append(f.result());(O/'retain48_progress.json').write_text(json.dumps(out,indent=2))
