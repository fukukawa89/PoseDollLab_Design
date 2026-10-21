import sys,json,concurrent.futures,traceback
from search_revo22_f5_orientation268 import O
from route_revo22_f5_native272 import run as route
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick

def run(pid,src):
 current=src
 for step in range(3):
  label=f'accessible{step}';d=route(pid,current,label,allow_removable_core=True);q=audit(pid,label)
  if pick(pid):return(pid,True)
  old=json.loads((O/'candidates'/pid/current/'design'/f'{pid}.json').read_text());current=label
  if old['new_tooth_count']==d['new_tooth_count']:break
 return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs=[ex.submit(run,*q)for q in [('H010','precise_route0'),('P003','precise_route2'),('X037','precise_route0')]]
  for f in concurrent.futures.as_completed(fs):
   try:print('ACCESSIBLE285',f.result(),flush=True)
   except Exception:traceback.print_exc()
