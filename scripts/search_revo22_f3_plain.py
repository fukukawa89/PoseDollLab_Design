"""Compare rigid print orientations on real source geometry, before creating support."""
from pathlib import Path
import json, numpy as np, concurrent.futures
from build_revo22_fins import solid
from pack_revo22_a1mini import read_mesh
from explore_revo22_f3 import R,B,O,OLD

def metrics(v,f,M,off):
    s=solid(v@np.array(M).T+off,f);bb=s.bounding_box()
    prev=s.slice(.1);island_area=0.;island_count=0;longsum=0.;maxlong=0.
    for z in np.arange(.3,bb[5],.2):
        cs=s.slice(float(z))
        for c in cs.decompose():
            if c.area()>.03 and (c^prev.offset(.025)).area()<.001:island_area+=c.area();island_count+=1
        a=(cs-prev.offset(2.)).area()
        longsum+=a;maxlong=max(maxlong,a);prev=cs
    return {'island_area_mm2':island_area,'island_count':island_count,'long_area_sum_mm2':longsum,'max_long_area_mm2':maxlong,
            'height_mm':bb[5],'score':island_area*8+longsum+maxlong*2}
def one(pid):
    old=json.loads((OLD/'design'/f'{pid}.json').read_text());v,f=read_mesh(B/f'print_batch/{pid}.3mf')
    rank=json.loads((OLD/'orientation'/f'{pid}.json').read_text())['ranked_candidates']
    candidates=[('F2',old['orientation'])]+[(f'axis_{j}',q) for j,q in enumerate(rank) if max(map(abs,q['gravity_in_source']))>.999999]
    candidates += [(f'rank_{j}',q) for j,q in enumerate(rank[:3])]
    seen=set();out=[]
    for label,c in candidates:
        key=tuple(np.round(c['gravity_in_source'],5))
        if key in seen:continue
        seen.add(key)
        r=metrics(v,f,c['matrix'],c['source_translation_mm'])
        out.append({'label':label,'orientation':c,'metrics':r})
    out.sort(key=lambda q:q['metrics']['score'])
    folder=O/'orientation_plain';folder.mkdir(exist_ok=True)
    (folder/f'{pid}.json').write_text(json.dumps(out,indent=2),encoding='utf8')
    print(pid,'best',out[0]['label'],round(out[0]['metrics']['score'],2),'F2',round(next(q['metrics']['score'] for q in out if q['label']=='F2'),2),flush=True)
    return {'id':pid,'best':out[0],'original':next(q for q in out if q['label']=='F2')}
if __name__=='__main__':
    raw=json.loads((O/'verification/all_baseline_coverage.json').read_text())
    risky={q['id'] for q in raw if q['max_long_overhang_area_mm2']>5 or len(q['layer_islands'])>0}
    risk=json.loads((OLD/'verification/remaining_regions.json').read_text())
    risky |= {r['object_name'].split()[1] for p in risk['plates'] for r in p['regions']}
    risky.discard('X046')
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:res=list(pool.map(one,sorted(risky)))
    (O/'verification/plain_orientation_search.json').write_text(json.dumps(res,indent=2),encoding='utf8')
    print('ORIENTATION_SCAN_DONE',len(res),flush=True)

