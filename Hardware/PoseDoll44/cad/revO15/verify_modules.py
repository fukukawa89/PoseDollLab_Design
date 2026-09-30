"""Read sealed inputs immediately before validation and lock their hashes.
Deliberate out-of-range collisions demonstrate that the checker is not vacuous.
"""
from common import *
import tut

def main():
 reports=[];rng=np.random.default_rng(150929)
 for kind in ('core','tut'):
  source=OUT/(kind+'_parts.npz');digest=sha(source);data=read(OUT/(kind+'_build.json'));parts={k:from_tri(t) for k,t in np.load(source).items()};owners=data['owners'];records=[]
  if kind=='core':cases=[(a,b) for a,b in itertools.product(range(-25,26,5),range(-95,1,5))]
  else:cases=[[0,0,0,0]]+[[float(rng.uniform(-170,170)),float(rng.uniform(-25,25)),float(rng.uniform(-95,0)),float(rng.uniform(-170,170))] for _ in range(180)]+[[p,a,b,s] for p,a,b,s in itertools.product((-170,0,170),(-25,25),(-95,0),(-170,0,170))]
  for i,q in enumerate(cases):
   fs=tut.frames(q) if kind=='tut' else {'C01':rot(0,q[0]),'ring':np.eye(3),'C02':rot(1,q[1])};p={k:pose(s,fs[owners[k]]) for k,s in parts.items()};hh=[h for h in hits(p) if owners[h['pair'][0]]!=owners[h['pair'][1]]];records.append({'angles_deg':list(q),'findings':hh})
   if (i+1)%50==0:print(kind,i+1,'failures',sum(bool(x['findings']) for x in records),flush=True)
  assert sha(source)==digest
  badq=[35,0] if kind=='core' else [0,0,70,0];fs=tut.frames(badq) if kind=='tut' else {'C01':rot(0,badq[0]),'ring':np.eye(3),'C02':rot(1,badq[1])};bad=hits({k:pose(s,fs[owners[k]]) for k,s in parts.items()})
  r={'module':kind,'input_sha256':digest,'samples':records,'fail_samples':sum(bool(x['findings']) for x in records),'out_of_range_counterexample':{'angles_deg':badq,'findings':bad},'counterexample_detected':bool(bad),'continuous_motion_proved':False,'physical_tested':False};reports.append(r);save('module_validation.json',{'reports':reports,'generator_sha256':sha(__file__)})
  print('FINISH',kind,len(records),r['fail_samples'],'positive_control',bool(bad),flush=True)
if __name__=='__main__':main()
