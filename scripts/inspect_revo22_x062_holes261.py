from pathlib import Path
import json,sys,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,box,md
import repair_revo22_f4_guarded_chamfer as ctx
B=R/'Hardware/PoseDoll44/bench/revO22';D=B/'X062_SupportTrial_R1';W=B/'a1mini_fins_v4/x062_trial_r2';W.mkdir(exist_ok=True)
d=json.loads((D/'design/X062.json').read_text());n=np.load(D/'parts/X062.npz');body=solid(n['v'],n['f']);parts,key,T=ctx.context(d,'X062');records=[];arr={}
for k,s in parts.items():
 if 'magnet_nut' not in k:continue
 ss=s.transform(T[:3,:]);gap=body.min_gap(ss,1)
 if gap>=1:continue
 meta=ctx.CACHE[1][k];A=np.array(meta['transform']);v,f=vf(ss);arr[k+'_v']=v;arr[k+'_f']=f
 rec=dict(name=k,bounds=list(ss.bounding_box()),gap=gap,volume=ss.volume(),meta=meta,world_to_print=T.tolist(),hardware_to_print=(T@A).tolist())
 records.append(rec)
np.savez_compressed(W/'nearby_magnet_nuts.npz',**arr);(W/'nearby_magnet_nuts.json').write_text(json.dumps(records,indent=2))
print(json.dumps([{k:v for k,v in r.items() if k not in ['meta','world_to_print']}for r in records],indent=2),flush=True)
