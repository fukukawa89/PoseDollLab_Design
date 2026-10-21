from pathlib import Path
import sys,json,concurrent.futures,time,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import trial as repair
from verify_revo22_f4_body_change import check as check_fit
from verify_revo22_f4_full_bead import check
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,label,newlabel=spec
 try:
  folder=O/'candidates'/pid/newlabel
  if not (folder/'verification/local_extrusion.json').exists():d=repair(pid,label,newlabel)
  else:d=check(pid,newlabel)
  fit=check_fit(pid,newlabel);d['fit_and_pose_geometry_passed']=fit['fit_and_pose_geometry_passed'];r={k:d[k] for k in ['id','label','critical_external_count','external_island_count','max_external_free_run_mm','native_review_resolved','fit_and_pose_geometry_passed']};print('FINISH_RESULT',r,flush=True);return r
 except Exception:return {'id':pid,'label':newlabel,'error':traceback.format_exc()}
if __name__=='__main__':
 source=sys.argv[1] if len(sys.argv)>1 else 'contact_finish_03';label=sys.argv[2] if len(sys.argv)>2 else 'chamfer_guarded_03';specs=[]
 for p in (O/'candidates').glob('*/'+source+'/verification/full_bead_contacts.json'):
  d=json.loads(p.read_text())
  if not d['native_review_resolved']:specs.append((d['id'],source,label))
 specs.sort();out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s) for s in specs]):
   out.append(f.result());(O/(label+'_progress.json')).write_text(json.dumps({'completed':len(out),'total':len(specs),'results':out},indent=2))
 print('FINISH_BATCH_DONE',len(out),flush=True)
