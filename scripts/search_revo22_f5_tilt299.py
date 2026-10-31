"""Small rigid tilts around the most promising unmodified native candidate."""
import sys,json,math,traceback,concurrent.futures,numpy as np
from search_revo22_f5_orientation268 import O,put
from build_revo22_f5_open270 import run as build
from build_revo22_f5_precise_guards283 import run as guards
from audit_revo22_f5_native271 import run as audit
from route_revo22_f5_native272 import run as route
from trial_revo22_f5_process273 import trial as process
from trial_revo22_f5_phase280 import run as phase
from optimize_revo22_f5_276 import pick,candidates

def run(pid):
 if pick(pid):return(pid,True)
 guards(pid);base=next(q for q in candidates(pid)if not q[4].get('part_body_modified_from_F4',False));src=base[2]
 if base[4].get('lift_mm',0)>1:
  for delta in [.05,.1,.15]:
   phase(pid,src,delta)
   if pick(pid):return(pid,True)
 ori=json.loads((O/'orientation'/f'{pid}.json').read_text());Q=np.array(base[4]['f4_to_current_matrix']);jobs=[]
 for axis,deg in [(a,d)for d in [2,-2,5,-5,10,-10]for a in[0,1]]:
  token=f'tilt299_{src}_{axis}_{deg}';old=next((i for i,q in enumerate(ori['ranked'])if q.get('token')==token),None)
  if old is None:
   an=math.radians(deg);c=math.cos(an);s=math.sin(an);A=np.array([[1,0,0],[0,c,-s],[0,s,c]])if axis==0 else np.array([[c,0,s],[0,1,0],[-s,0,c]]);old=len(ori['ranked']);ori['ranked'].append(dict(token=token,matrix_from_F4=(A@Q).tolist(),bed_face_mm2=0,xy_hull_area_mm2=1))
  jobs.append((old,token))
 put(O/'orientation'/f'{pid}.json',ori)
 for rank,token in jobs:
  label=f'tilt299_r{rank}';build(pid,label,rank,precise_guard=True);q=audit(pid,label)
  if pick(pid):return(pid,True)
  if 5*q['external_island_count']+sum(x['length_mm']for x in q['critical_external_runs'])<45:
   current=label
   for j in range(2):
    nxt=label+f'_route{j}';dd=route(pid,current,nxt,allow_removable_core=True,target_native_height=True);q=audit(pid,nxt)
    if pick(pid):return(pid,True)
    before=json.loads((O/'candidates'/pid/current/'design'/f'{pid}.json').read_text());current=nxt
    if dd['new_tooth_count']==before['new_tooth_count']:break
   process(pid,current,label+'_micro',{'min_feature_size':'100%'})
   if pick(pid):return(pid,True)
  print('TILT299_RANK',pid,rank,q['external_island_count'],q['critical_external_count'],flush=True)
 return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  fs={ex.submit(run,p):p for p in(sys.argv[1:]or['P034','X037','P001','P033','P049','P130'])}
  for f in concurrent.futures.as_completed(fs):
   try:print('TILT299_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('TILT299_ERROR',fs[f],flush=True)
