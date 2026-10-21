"""Foot/toe joint clocking search with both ankle rotations and toe flexion."""
from common import *
from layout_fullbody import config,build,module_hits

def classify(hh,meta):
 allhits=[r for g in hh for r in g['findings']];hard=[r for r in allhits if not r['same_rigid_body'] or all(meta[k]['sku'] is not None for k in r['parts'])];return hard,len(allhits)-len(hard)
def main():
 out=[]
 for side in ('l','r'):
  _,mm=config('quinn');name=f'ball_{side}.flex';m=next(m for m in mm if m['id']==name);F=np.array(m['F']);rank=[]
  for phase in range(0,360,30):
   op={name:{'F':(F@rot(2,phase)).tolist()}};samples=[]
   p,meta,_,fail,_=build('quinn',overrides=op,only=(f'foot_{side}',name));hard,integ=classify(module_hits(p,meta),meta)
   if hard:continue
   for dors,inv,toe in itertools.product((-45,0,30),(-25,0,25),(-20,0,60)):
    angles={f'foot_{side}.dorsiflex':dors,f'foot_{side}.invert':inv,name:toe};p,meta,_,fail,_=build('quinn',angles,op,only=(f'foot_{side}',name));hh,nn=classify(module_hits(p,meta),meta);samples.append({'angles_deg':angles,'hard_findings':hh,'integration_count':nn,'mapping_failures':fail})
   rank.append({'phase_deg':phase,'overrides':op,'samples':samples,'fail_samples':sum(bool(r['hard_findings'] or r['mapping_failures']) for r in samples)})
  rank.sort(key=lambda r:r['fail_samples']);out.append({'side':side,'ranked':rank});save('foot_toe_clocking.json',{'results':out,'scope':'Discrete pair search; unmodelled carrier cannot be inferred clear'});print('foot',side,[(r['phase_deg'],r['fail_samples']) for r in rank],flush=True)
if __name__=='__main__':main()
