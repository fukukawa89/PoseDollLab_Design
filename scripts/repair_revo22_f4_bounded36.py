from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_clean_chamfer import trial
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,label=spec.split(':');out=[]
 try:
  for j in range(1,3):
   new='bounded36_'+str(j).zfill(2);d=trial(pid,label,new);d=refine(pid,new);z={k:d[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']};out.append(z);print('BOUNDED36_RESULT',z,flush=True)
   if d['native_review_resolved']:
    z['fit']=fit(pid,new)['fit_and_pose_geometry_passed'];z['geometry']=geom(pid,new)['geometric_constraints_passed'];break
   before=json.loads((O/'candidates'/pid/label/'design'/f'{pid}.json').read_text()).get('body_change',{}).get('removed_volume_mm3',0);after=json.loads((O/'candidates'/pid/new/'design'/f'{pid}.json').read_text()).get('body_change',{}).get('removed_volume_mm3',0)
   if after-before<1e-5:break
   label=new
  return {'id':pid,'results':out}
 except Exception:return {'id':pid,'results':out,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s) for s in sys.argv[1:]]):
   out.append(f.result());(O/'bounded36_progress.json').write_text(json.dumps(out,indent=2))
