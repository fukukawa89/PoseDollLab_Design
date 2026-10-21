import traceback,concurrent.futures
from build_revo22_f5_open270 import run as build
from route_revo22_f5_ends366 import run as route
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from optimize_revo22_f5_276 import pick

def run(rank):
 p='P130';l=f'orient398_r{rank}_base';build(p,l,rank=rank,precise_guard=True)
 for i in range(5):
  q=audit(p,l)
  if q['native_review_resolved']:geo(p,l);assert pick(p);return rank,True
  dest=f'orient398_r{rank}_route{i}';route(p,l,dest,allow_removable_core=True);l=dest
 return rank,False
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  for f in concurrent.futures.as_completed([ex.submit(run,r)for r in [1,2]]):
   try:print('ORIENT398_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc()
