"""Search verified sparse F5 candidates; never select unresolved native results."""
import sys,json,time,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from audit_revo22_f5_native271 import run as audit
from route_revo22_f5_native272 import run as route
from trial_revo22_f5_process273 import trial as process
from relief_revo22_f5_native275 import run as relief

def candidates(pid):
 out=[]
 for f in(O/'candidates'/pid).glob('*/verification/native_final.json'):
  try:
   q=json.loads(f.read_text());d=json.loads((f.parents[1]/'design'/f'{pid}.json').read_text());score=5*q['external_island_count']+sum(x['length_mm']for x in q['critical_external_runs']);out.append((score,d['support_volume_mm3'],f.parents[1].name,q,d))
  except Exception:pass
 return sorted(out,key=lambda x:(x[0],x[1]))
def pick(pid):
 a=candidates(pid);ok=[]
 for q in a:
  folder=O/'candidates'/pid/q[2]/'verification';gf=folder/'f5_geometry.json'
  if not q[3]['native_review_resolved'] or not gf.exists():continue
  g=json.loads(gf.read_text())
  if not g.get('geometric_constraints_passed'):continue
  if q[4].get('connector_void_policy') and not g.get('whole_stem_extraction_verified'):continue
  if g.get('body_change_fit_and_pose_required'):
   ff=folder/'f5_fit_and_pose.json'
   if not ff.exists() or not json.loads(ff.read_text()).get('fit_and_pose_geometry_passed'):continue
  ok.append(q)
 if ok:
  q=min(ok,key=lambda x:(x[4].get('part_body_modified_from_F4',False),x[1]));put(O/'selections'/f'{pid}.json',dict(id=pid,label=q[2],native_pass=True,body_modified=q[4].get('part_body_modified_from_F4',False),teeth=q[4]['new_tooth_count'],fins=q[4]['support_count'],support_volume_mm3=q[1],fit_pending=q[4].get('fit_and_pose_pending',False)));return True
 return False

def run(pid):
 if pick(pid):return pid,True
 # Initial native audits run separately. Wait only for the relevant known candidate.
 for tries in range(300):
  if(O/'candidates'/pid/'oldpose_c/verification/native_final.json').exists():break
  time.sleep(2)
 choices=candidates(pid)[:2]
 for j,(_,_,src,rep,des)in enumerate(choices):
  current=src
  for step in range(3):
   label=f'opt{j}_route{step}';dd=route(pid,current,label);q=audit(pid,label)
   if pick(pid):return pid,True
   before=json.loads((O/'candidates'/pid/current/'design'/f'{pid}.json').read_text())
   current=label
   if dd['new_tooth_count']==before['new_tooth_count']:break
  # Short fin and body tips smaller than a nozzle are evaluated as an explicit slicer policy.
  label=f'opt{j}_micro';q=process(pid,current,label,{'min_feature_size':'100%'})
  if pick(pid):return pid,True
  label=f'opt{j}_width';q=process(pid,current,label,{'outer_wall_line_width':'0.6','inner_wall_line_width':'0.6','is_infill_first':'1'})
  if pick(pid):return pid,True
 # Only after both sparse layouts and localized routes fail, try a bounded underside relief.
 current=candidates(pid)[0][2]
 for step in range(3):
  label=f'opt_relief{step}';d=relief(pid,current,label)
  if d is None:break
  audit(pid,label)
  if pick(pid):return pid,True
  current=label
 q=candidates(pid)[0];put(O/'pending'/f'{pid}.json',dict(id=pid,best_label=q[2],islands=q[3]['external_island_count'],critical=q[3]['critical_external_count'],score=q[0]));print('F5_OPT_PENDING',pid,q[2],q[0],flush=True);return pid,False
if __name__=='__main__':
 inv=json.loads((O/'inventory.json').read_text());ids=sys.argv[1:]or[g[0]for g in inv['groups']if next(x for x in inv['rows']if x['id']==g[0])['has_fins']and g[0]!='X062'];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  ff={pool.submit(run,pid):pid for pid in ids}
  for f in concurrent.futures.as_completed(ff):
   try:out.append(f.result());put(O/'optimization_progress.json',out);print('OPT_RESULT',out[-1],flush=True)
   except Exception:traceback.print_exc();print('OPT_ERROR',ff[f],flush=True)
