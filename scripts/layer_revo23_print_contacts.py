from bambu_revo23_print import *

def refine(rid):
    file=OUT/'candidates'/(rid+'.json');s=read(file)
    rr=[read(p) for p in (OUT/'bambu'/rid).glob('*/checked_result.json')]
    if any(r.get('passed') for r in rr):return
    rr.sort(key=lambda r:len(r['clearance']['wire_void_hits'])*100+len(r['clearance']['functional_void_hits'])*30+len(r['islands']['external_new_islands'])*10+r['support_g'])
    source=rr[0];original=copy.deepcopy(next(c for c in s['candidates'] if c['name']==source['name']))
    for name,layer,first in [('layer24','0.16','0.24'),('layer12','0.12','0.2')]:
        c=copy.deepcopy(original);c.update(name=name)
        c.setdefault('settings',{}).update(layer_height=layer,initial_layer_print_height=first)
        s['candidates']=[x for x in s['candidates'] if x['name']!=name]+[c];put(file,s)
        print('LAYER',rid,name,'from',source['name'],flush=True)
        r=run(dict(id=rid,key=s['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))
        if r['passed']:return r
    return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    ids=a.ids or [p.stem for p in sorted((OUT/'candidates').glob('*.json'))]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:list(pool.map(refine,ids))
