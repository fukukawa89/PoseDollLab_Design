import json,numpy as np
import build_revo22_fins_v2 as f2
from check_revo22_f2_layers import check
from repair_revo22_f2_contacts import repair
B=f2.B;O=f2.O;u={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']};vols={i['part']:i['volumes'] for i in json.loads((f2.D/'all_protected_volumes.json').read_text())['objects']}
for pid,ref in [('P115','P049'),('P093','P071')]:
 gravity=json.loads((O/'design'/f'{ref}.json').read_text())['orientation']['gravity_in_source'];rank=json.loads((O/'orientation'/f'{pid}.json').read_text())['ranked_candidates'];ori=min(rank,key=lambda c:np.linalg.norm(np.array(c['gravity_in_source'])-gravity));assert np.linalg.norm(np.array(ori['gravity_in_source'])-gravity)<.001;f2.choose=lambda _:ori;f2.make(pid,u[pid],vols[u[pid]['part']]);check(pid);repair(pid)