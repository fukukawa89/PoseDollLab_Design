from pathlib import Path
import sys,json,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_complete_corner import trial,O
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom

def one(spec):
 pid,parent=spec.split(':');out=[]
 try:
  for j in range(1,7):
   label='corner70_'+str(j).zfill(2);trial(pid,parent,label);d=refine(pid,label);q={k:d[k]for k in['id','label','external_island_count','critical_external_count','native_review_resolved']};out.append(q);print('CORNER70',q,flush=True)
   if d['native_review_resolved']:q['fit']=fit(pid,label)['fit_and_pose_geometry_passed'];q['geometry']=geom(pid,label)['geometric_constraints_passed'];break
   bd=json.loads((O/'candidates'/pid/parent/'design'/f'{pid}.json').read_text());nd=json.loads((O/'candidates'/pid/label/'design'/f'{pid}.json').read_text());delta=nd['body_change']['removed_volume_mm3']-bd.get('body_change',{}).get('removed_volume_mm3',0)
   if delta<1e-6:break
   parent=label
  return {'id':pid,'results':out}
 except Exception:return {'id':pid,'results':out,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());(O/'corner70_progress.json').write_text(json.dumps(out,indent=2))
