from bambu_revo23_print import *

def finish(rid):
    file=OUT/'candidates'/(rid+'.json');s=read(file)
    rr=[read(p) for p in (OUT/'bambu'/rid).glob('*/checked_result.json')]
    if any(r.get('passed') for r in rr):return
    rr.sort(key=lambda r:len(r['clearance']['wire_void_hits'])*100+len(r['clearance']['functional_void_hits'])*3+len(r['islands']['external_new_islands'])*20+r['support_g'])
    source=rr[0];original=copy.deepcopy(next(c for c in s['candidates'] if c['name']==source['name']))
    if original.get('enforce_source'):original['enforce_sources']=original.get('enforce_sources',[])+[original['enforce_source']]
    original['enforce_source']=(OUT/'bambu'/rid/source['name']/'checked_result.json').relative_to(B).as_posix()
    for name,gap,angle,style in [('contact32','0.32','45','snug'),('contact36','0.36','90','snug'),('contact_tree','0.28','0','tree')]:
        c=copy.deepcopy(original);c.update(name=name,guard_revision=5,blocker_margin_mm=2.2,shield_enforcers=True,support=style)
        c.setdefault('settings',{}).update(bridge_no_support='0',support_threshold_angle='55',support_top_z_distance=gap,support_bottom_z_distance=gap,support_object_xy_distance='0.6',support_angle=angle)
        s['candidates']=[x for x in s['candidates'] if x['name']!=name]+[c];put(file,s)
        print('CONTACT',rid,name,'from',source['name'],flush=True)
        r=run(dict(id=rid,key=s['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))
        if r['passed']:return r
    return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    ids=a.ids or [p.stem for p in sorted((OUT/'candidates').glob('*.json'))]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:list(pool.map(finish,ids))
