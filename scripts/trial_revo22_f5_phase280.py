"""Shift elevated rigid parts within the layer pitch; keep every fin foot on the bed."""
import sys,json,shutil,numpy as np,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid
from audit_revo22_f5_native271 import run as audit

def run(pid,src,delta):
 label=src+'_phase'+str(round(delta*1000));a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if not(b/'parts'/f'{pid}.npz').exists():
  n=dict(np.load(a/'parts'/f'{pid}.npz'));assert n['v'][:,2].min()>1.;d=json.loads((a/'design'/f'{pid}.json').read_text());n['v'][:,2]+=delta;n['teeth_v'][:,2]+=delta;n['fin_v'][:,2]+=delta*np.clip(n['fin_v'][:,2]/.4,0,1)
  s=solid(n['v'],n['f']);f=solid(n['fin_v'],n['fin_f']);assert(s^f).volume()<1e-6
  for sub in['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
  np.savez_compressed(b/'parts'/f'{pid}.npz',**n);gn=dict(np.load(a/'verification/guards.npz'));gn['v'][:,2]+=delta;np.savez_compressed(b/'verification/guards.npz',**gn)
  d['orientation']['source_translation_mm'][2]+=delta;d['f4_to_current_translation_mm'][2]+=delta;d['lift_mm']+=delta;d['trial']=label;d['layer_phase_shift_mm']=d.get('layer_phase_shift_mm',0)+delta
  for row in d.get('teeth',[])+d.get('local_route_repairs',[]):
   for k in['root','tip','target']:
    if k in row:row[k][2]+=delta
  for row in d.get('segments',[]):row['bounds_mm'][5]+=delta
  for q in d.get('required_layer_ranges',[]):q[0]+=delta;q[1]+=delta
  put(b/'design'/f'{pid}.json',d)
 q=audit(pid,label);return pid,label,q['native_review_resolved'],q['external_island_count'],q['critical_external_count']
if __name__=='__main__':
 jobs=[('P003','oldpose_c'),('X037','oldpose_m100'),('X001','onset_low_a'),('H008','opt0_route0'),('H010','opt0_micro')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as ex:
  ff=[ex.submit(run,pid,src,delta)for pid,src in jobs for delta in[.05,.1,.15]]
  for f in concurrent.futures.as_completed(ff):print('F5_PHASE',f.result(),flush=True)
