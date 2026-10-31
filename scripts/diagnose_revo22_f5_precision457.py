import json,numpy as np
from search_revo22_f5_orientation268 import O,OLD
from build_revo22_fins import solid,union,box
p='P071';sel=json.loads((O/'selections'/f'{p}.json').read_text());a=O/'candidates'/p/sel['label'];d=json.loads((a/'design'/f'{p}.json').read_text());n=np.load(a/'parts'/f'{p}.npz');old=np.load(OLD/'parts'/f'{p}.npz');ref=solid(old['v']@np.array(d['f4_to_current_matrix']).T+np.array(d['f4_to_current_translation_mm']),old['f']);s=solid(n['v'],n['f']);roi=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:])for q in d.get('f5_reliefs',[])+d.get('f5_additions',[])])
for tol in [1e-9,1e-8,1e-7]:
 r=ref.set_tolerance(tol);b=s.set_tolerance(tol);raw=r-b;added=b-r;print('TOL457',tol,'added',added.volume(),'removed',raw.volume(),'outside',abs((raw-roi).volume())+abs((added-roi).volume()),'triangles',b.num_tri(),flush=True)
