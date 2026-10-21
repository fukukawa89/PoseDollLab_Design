import sys,json,concurrent.futures
import numpy as np
from build_revo22_fins_v2 import O,B
from package_revo22_fins_v2 import build
from build_revo22_supports import slice_project
from verify_revo22_f2_native_mesh import check as native
from verify_revo22_f2_extrusions import check_project

def audit(p):return check_project(O/'projects'/f"{p['id']}_O22F2_PLA_fins.3mf",p)
if __name__=='__main__':
 plates=[p for p in json.loads((O/'manifest.json').read_text())['plates'] if p['id'] in sys.argv[1:]]
 for p in plates:
  for it in p['items']:
   n=np.load(O/'parts'/f"{it['id']}.npz");vv=np.concatenate([n[k] for k in ['v','fin_v','teeth_v'] if len(n[k])]);vv=vv@np.array(it['rotation_matrix']).T+it['translation_mm'];bb=it['fins_bounds_mm'];assert np.all(vv.min(0)>=np.array(bb[:3])-.0001) and np.all(vv.max(0)<=np.array(bb[3:])+.0001),(p['id'],it['id'],'new layout required')
  src,work=build(p);dest=O/'projects'/f"{p['id']}_O22F2_PLA_fins.3mf";r=slice_project(src,dest,work);(O/'verification'/f"{p['id']}_slice.json").write_text(json.dumps({'result':r},ensure_ascii=False,indent=2),encoding='utf-8');native(p)
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  for r in pool.map(audit,plates):print('REFRESH',r['project'],r['teeth_missing_printed_layer'],flush=True)