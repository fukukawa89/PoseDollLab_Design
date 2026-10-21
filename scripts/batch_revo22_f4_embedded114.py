from pathlib import Path
import sys,concurrent.futures,traceback,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_portal_embedded114 import trial
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from refine_revo22_f4_lateral104 import check as refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 try:
  pid,parent=spec.split(':');label='embedded114';trial(pid,parent,label);p=O/'candidates'/pid/label
  if(p/'verification/local_extrusion.json').exists():
   q=refine(pid,label)
   if q['native_review_resolved']:
    d=json.loads((p/'design'/f'{pid}.json').read_text())
    if 'body_change'in d:fit(pid,label)
    geom(pid,label)
 except Exception:traceback.print_exc()
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as p:
  for f in concurrent.futures.as_completed([p.submit(one,s)for s in sys.argv[1:]]):f.result()
