import concurrent.futures,traceback
from trial_revo22_f5_process273 import trial
from optimize_revo22_f5_276 import pick

def one(pid,src,label,settings):
 q=trial(pid,src,label,settings);pick(pid);return(pid,label,q['native_review_resolved'],q['external_island_count'],q['critical_external_count'])
if __name__=='__main__':
 jobs=[('P003','open_a','flat_bridge'+str(a),{'bridge_angle':str(a)})for a in[30,45,60,90,120,150]]
 jobs +=[(pid,src,'classic_a',{'wall_generator':'classic','detect_thin_wall':'1'})for pid,src in [('P003','open_a'),('X037','oldpose_m100'),('X001','onset_low_a')]]
 jobs +=[(pid,src,'outer_first_a',{'wall_sequence':'outer wall/inner wall'})for pid,src in [('P003','open_a'),('X037','oldpose_m100'),('X001','onset_low_a')]]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs=[ex.submit(one,*q)for q in jobs]
  for f in concurrent.futures.as_completed(fs):
   try:print('SWEEP281',f.result(),flush=True)
   except Exception:traceback.print_exc()
