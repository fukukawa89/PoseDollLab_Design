"""Generate, repair, and compare rotated F3 candidates without overwriting F2."""
import json,concurrent.futures,traceback,shutil
import numpy as np
from pathlib import Path
from explore_revo22_f3 import O,OLD,B,audit
import build_revo22_fins_v3 as builder
import check_revo22_f3_layers as layer
import repair_revo22_f3_contacts as repair
import repair_revo22_f3_side_contacts as side
ITEMS={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']}
VOLS={i['part']:i['volumes'] for i in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects']}
def score(r):
    return sum(q['area_mm2'] for q in r['layer_islands'])*50+len(r['layer_islands'])*5+sum(q['area_mm2'] for q in r['long_overhang_layers'])+r['max_long_overhang_area_mm2']*15+r['max_fin_height_mm']*.02
def one(row):
    pid=row['id'];dest=O/'rotated_candidates'/pid
    try:
        for d in ['parts','design','verification']:(dest/d).mkdir(parents=True,exist_ok=True)
        builder.O=dest;builder.choose=lambda _:row['best']['orientation'];builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=None;builder.THICKNESS_OVERRIDE=None
        layer.O=dest;repair.O=dest;side.O=dest
        r=builder.make(pid,ITEMS[pid],VOLS.get(ITEMS[pid]['part'],[]));layer.check(pid);repair.repair(pid);side.repair_side(pid)
        after=audit(pid,dest)
        before=json.loads((O/'verification'/f'{pid}_coverage.json').read_text())
        result={'id':pid,'old_score':score(before),'new_score':score(after),'candidate':str(dest),'selected':score(after)<score(before)-.05,'before':before,'after':after}
        (dest/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print('COMPARE',pid,result['selected'],round(result['old_score'],2),round(result['new_score'],2),flush=True)
        return result
    except Exception:return {'id':pid,'error':traceback.format_exc(),'selected':False}
if __name__=='__main__':
    a=json.loads((O/'verification/plain_orientation_search.json').read_text())
    candidates=[x for x in a if x['best']['label']!='F2' and x['best']['metrics']['score']<x['original']['metrics']['score']*.85]
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:rows=list(pool.map(one,candidates))
    for r in rows:
        if not r['selected']:continue
        folder=Path(r['candidate'])
        for d,e in [('parts','npz'),('design','json')]:shutil.copy2(folder/d/f"{r['id']}.{e}",O/d/f"{r['id']}.{e}")
        shutil.copy2(folder/'verification'/f"{r['id']}_coverage.json",O/'verification'/f"{r['id']}_coverage.json")
    (O/'verification/rotation_changes.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    print('ROTATED_DONE',len(rows),'selected',sum(r['selected'] for r in rows),'errors',sum('error' in r for r in rows),flush=True)

