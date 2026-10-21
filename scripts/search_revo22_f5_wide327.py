import sys,json,traceback,concurrent.futures,numpy as np
from search_revo22_f5_orientation268 import O
from build_revo22_f5_open270 import run as build
from audit_revo22_f5_native271 import run as audit
from route_revo22_f5_taper316 import run as route
from optimize_revo22_f5_276 import candidates,pick
from verify_revo22_f5_geometry292 import run as geometry

def run(pid):
 if pick(pid):return(pid,True)
 tried={x[4].get('orientation_rank')for x in candidates(pid)}
 for rank in [1,3,6,9,2,4,5,7,8,10,11]:
  if rank in tried:continue
  label=f'orient327_r{rank}'
  try:
   build(pid,label,rank,pitch=7.2,spacing=3.,precise_guard=True);n=np.load(O/'candidates'/pid/label/'parts'/f'{pid}.npz');v=np.r_[n['v'],n['fin_v'],n['teeth_v']]
   if max(np.ptp(v,axis=0)[:2])>172:print('ORIENT327_BED_SKIP',pid,rank,flush=True);continue
   q=audit(pid,label)
   if q['native_review_resolved']:pick(pid);geometry(pid);return(pid,True)
   score=q['external_island_count']*5+sum(x['length_mm']for x in q['critical_external_runs'])
   if score<70:
    src=label
    for step in range(2):
     label=f'orient327_r{rank}_route{step}';d=route(pid,src,label,allow_removable_core=True,target_native_height=True,tip_width=.6);q=audit(pid,label)
     if q['native_review_resolved']:pick(pid);geometry(pid);return(pid,True)
     before=json.loads((O/'candidates'/pid/src/'design'/f'{pid}.json').read_text());src=label
     if d['new_tooth_count']==before['new_tooth_count']:break
  except Exception:traceback.print_exc();print('ORIENT327_TRIAL_ERROR',pid,rank,flush=True)
 return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=4)as ex:
  fs={ex.submit(run,p):p for p in sys.argv[1:]}
  for f in concurrent.futures.as_completed(fs):
   try:print('ORIENT327_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('ORIENT327_ERROR',fs[f],flush=True)
