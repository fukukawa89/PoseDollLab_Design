import sys,json,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from build_revo22_f5_open270 import run as build
from build_revo22_f5_precise_guards283 import run as guards
from audit_revo22_f5_native271 import run as audit
from route_revo22_f5_native272 import run as route
from trial_revo22_f5_process273 import trial as process
from trial_revo22_f5_phase280 import run as phase
from optimize_revo22_f5_276 import pick,candidates

def good(pid):
 pick(pid);f=O/'selections'/f'{pid}.json'
 return f.exists() and not json.loads(f.read_text()).get('body_modified',False)
def run(pid):
 if good(pid):return(pid,True)
 guards(pid)
 choices=[q for q in candidates(pid)if not q[4].get('part_body_modified_from_F4',False)and q[4].get('lift_mm',0)>1 and list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))]
 if choices:
  src=choices[0][2]
  for delta in [.05,.1,.15]:
   phase(pid,src,delta)
   if good(pid):return(pid,True)
 for rank in [2,3,4,5,6,7,8,9,10,11,1]:
  label=f'search295_r{rank}';build(pid,label,rank,precise_guard=True);q=audit(pid,label)
  if good(pid):return(pid,True)
  current=label
  for i in range(2):
   nxt=label+f'_route{i}';d=route(pid,current,nxt,allow_removable_core=True,target_native_height=True);q=audit(pid,nxt)
   if good(pid):return(pid,True)
   old=json.loads((O/'candidates'/pid/current/'design'/f'{pid}.json').read_text());current=nxt
   if d['new_tooth_count']==old['new_tooth_count']:break
  score=5*q['external_island_count']+sum(x['length_mm']for x in q['critical_external_runs'])
  if score<35:
   process(pid,current,label+'_micro',{'min_feature_size':'100%'})
   if good(pid):return(pid,True)
  print('SEARCH295_RANK',pid,rank,score,flush=True)
 return(pid,False)
if __name__=='__main__':
 ids=sys.argv[1:]or['P001','P002','P033','P034','P035','P049','P051','P073','P130','X037','X061'];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in ids}
  for f in concurrent.futures.as_completed(fs):
   try:out.append(f.result());put(O/'search295_progress.json',out);print('SEARCH295_RESULT',out[-1],flush=True)
   except Exception:traceback.print_exc();print('SEARCH295_ERROR',fs[f],flush=True)
