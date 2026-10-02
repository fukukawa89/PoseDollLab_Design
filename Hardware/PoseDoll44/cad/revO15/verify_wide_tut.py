from common import *
from layout_fullbody import libraries
import wide_tut
p,o,_=libraries()['wide_tut'];rng=np.random.default_rng(20260929);cases=[list(v) for v in itertools.product((-170,0,170),(-25,25),(-120,0),(-170,170))]+[[rng.uniform(-170,170),rng.uniform(-25,25),rng.uniform(-120,0),rng.uniform(-170,170)] for _ in range(52)];rr=[]
for i,q in enumerate(cases):
 fs=wide_tut.frames(q);hh=hits({k:pose(v,fs[o[k]]) for k,v in p.items()});rr.append({'angles_deg':q,'findings':hh})
 if i%10==0:print('wide full samples',i,'fail',sum(bool(r['findings']) for r in rr),flush=True)
save('wide_tut_validation.json',{'cases':rr,'inputs_sha256':{n:sha(OUT/n) for n in ('wide_tut_parts.npz','wide_tut_build.json')},'physical_tested':False,'continuous_proof':False});print('DONE',len(rr),[(x['angles_deg'],len(x['findings'])) for x in rr if x['findings']],flush=True)
