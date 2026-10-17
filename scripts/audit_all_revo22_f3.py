"""Baseline F3 diagnostics of all real part types, preserve source F2."""
from pathlib import Path
import json,shutil,hashlib,concurrent.futures
from explore_revo22_f3 import audit,O,OLD,B
def one(pid):
    try:
        previous=O/'verification'/f'{pid}_coverage.json'
        return json.loads(previous.read_text()) if previous.exists() else audit(pid,O)
    except Exception as e:return {'id':pid,'error':repr(e)}
if __name__=='__main__':
    items={i['id']:i for p in json.loads((OLD/'manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']}
    records=[]
    for pid in items:
        for d,ext in [('parts','npz'),('design','json'),('orientation','json')]:
            src=OLD/d/f'{pid}.{ext}';dst=O/d/src.name
            if not dst.exists():shutil.copy2(src,dst)
        records.append({'id':pid,'F2_npz_sha256':hashlib.sha256((OLD/'parts'/f'{pid}.npz').read_bytes()).hexdigest()})
    (O/'verification/baseline_sources.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(one,[pid for pid in items if pid!='X046']))
    (O/'verification/all_baseline_coverage.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('BASELINE_DONE',len(results),'ERRORS',sum('error' in r for r in results),flush=True)

