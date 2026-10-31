from pathlib import Path
import json, numpy as np, manifold3d as md
from pack_revo22_a1mini import read_mesh
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins'
O.mkdir(exist_ok=True)
out=[]
for pid in ['P033','P034','P035','H004','X005','X006','X045','X046','X038','X050']:
 v,f=read_mesh(B/f'print_batch/{pid}.3mf')
 s=md.Manifold(md.Mesh64(v,f.astype(np.uint64)))
 print(pid,s.status(),len(v),len(f),flush=True)
 out.append(dict(id=pid,v=np.round(v,5).tolist(),f=f.tolist()))
(O/'probe.json').write_text(json.dumps(out,separators=(',',':')))
