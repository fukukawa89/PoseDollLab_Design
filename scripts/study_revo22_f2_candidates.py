import sys,json,shutil,time
from pathlib import Path
import numpy as np
import build_revo22_fins_v2 as f2
from check_revo22_f2_layers import check
B=f2.B;O=f2.O
u={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']}
vols={i['part']:i['volumes'] for i in json.loads((f2.D/'all_protected_volumes.json').read_text())['objects']}
pid=sys.argv[1];d=json.loads((O/'orientation'/f'{pid}.json').read_text());rank=d['ranked_candidates'];card=[c for c in rank if max(abs(np.array(c['gravity_in_source'])))>.999999];candidates=card+rank[:4]+sorted(rank,key=lambda c:c['size_mm'][2])[:2];seen=set();results=[]
for i,ori in enumerate(candidates):
 key=tuple(np.round(ori['gravity_in_source'],5))
 if key in seen:continue
 seen.add(key);f2.choose=lambda pid:ori
 r=f2.make(pid,u[pid],vols.get(u[pid]['part'],[]));check(pid)
 name=f'{pid}_orientation_{i:02}';dest=O/'candidates'/name;dest.mkdir(parents=True,exist_ok=True)
 for path in [O/'parts'/f'{pid}.npz',O/'design'/f'{pid}.json',O/'verification'/f'{pid}_layers.json']:shutil.copy2(path,dest/path.name)
 layers=json.loads((dest/f'{pid}_layers.json').read_text());islands=sum(x['area_mm2'] for x in layers['combined_floating_islands']);mx=max([x['unbacked_beyond_2mm_area'] for x in layers['long_overhang_layers']],default=0);mh=max([s['height_mm'] for s in r['segments']],default=0)
 z={'name':name,'orientation':key,'height':r['new_height_mm'],'fins':r['support_count'],'teeth':len(r['teeth']),'max_fin_height':mh,'island_area':islands,'max_unbacked_area':mx,'volume':r['support_volume_mm3']};results.append(z);print(json.dumps(z),flush=True)
(O/'candidates'/f'{pid}_comparison.json').write_text(json.dumps(results,indent=2))