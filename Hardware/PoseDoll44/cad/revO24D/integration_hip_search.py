from fullbody import *
import fullbody,closures
from validate import Collision
from itertools import product
old=closures.remove_isolated_cutoffs
closures.remove_isolated_cutoffs=lambda d:None
for back in [44,48,52,56]:
    fullbody.HIP_BACK=closures.HIP_BACK=back
    D=fullbody.build();pp=D.parts; engine=Collision(pp,[p['s'] for p in pp]);fails=[]
    for side in ['l','r']:
        for aa,bb,cc in product([-20,0,45],[-20,50,120],[-35,0,45]):
            q={**NEUTRAL_ANGLES,side+'_hip_abduct':aa,side+'_hip_flex':bb,side+'_hip_roll':cc}
            hits=engine.check(q)
            if hits:fails.append(dict(q=q,hits=hits))
    put(OUT/f'history/integration_search/hip_{back}.json',dict(back=back,height=fullbody.HIP_BRIDGE,failures=fails))
    print('CANDIDATE',back,'FAIL',len(fails),'PAIRS',sorted({h['a']+' / '+h['b'] for r in fails for h in r['hits']}),flush=True)
