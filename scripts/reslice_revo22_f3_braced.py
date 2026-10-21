"""Reslice only plates whose physical geometry changed after the first pass."""
import json
from package_revo22_fins_v3 import *
from prepare_revo22_f3 import slicer
m=json.loads((O/'manifest.json').read_text())
for pid in ['F01','F05']:
    idx=next(i for i,p in enumerate(m['plates']) if p['id']==pid);p=m['plates'][idx]
    updated=arrange(p['items'],'F',p['title'],p['optional'],int(pid[1:]));assert len(updated)==1,(pid,len(updated))
    p=updated[0];m['plates'][idx]=p;source,work=build(p);dest=O/'projects'/f'{pid}_O22F3_PLA_fins.3mf'
    result=slicer(source,dest,work/'orca_braced');assert result['complete'],result
    (O/'verification'/f'{pid}_slice.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('RESLICED',pid,len(p['items']),flush=True)
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
