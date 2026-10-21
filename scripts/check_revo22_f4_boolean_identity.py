from pathlib import Path
import sys,json,numpy as np,concurrent.futures
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid
from select_revo22_f4_repairs import select,O
B=O.parent

def one(q):
 pid=q['id'];p=O/'candidates'/pid/q['label'];n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());base=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');v=base['source_v']@np.array(d['orientation']['matrix']).T+np.array(d['orientation']['source_translation_mm']);s=solid(v,base['f']);z=float((s-s).volume());return {'id':pid,'label':q['label'],'source_self_difference_mm3':z,'source_status':str(s.status()),'source_boolean_identity_pass':abs(z)<1e-6}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for d in pool.map(one,select()):
   out.append(d)
   if not d['source_boolean_identity_pass']:print('SOURCE_IDENTITY_FAILURE',d,flush=True)
 (O/'source_boolean_identity_controls.json').write_text(json.dumps(out,indent=2));print('SOURCE_IDENTITY_DONE',len(out),sum(q['source_boolean_identity_pass'] for q in out),flush=True)
