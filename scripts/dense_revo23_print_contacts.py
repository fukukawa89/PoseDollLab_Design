from bambu_revo23_print import *

def dense(rid):
    file=OUT/'candidates'/(rid+'.json');s=read(file)
    rr=[read(p) for p in (OUT/'bambu'/rid).glob('*/checked_result.json')]
    if any(r.get('passed') for r in rr):return
    rr.sort(key=lambda r:len(r['clearance']['wire_void_hits'])*100+len(r['clearance']['functional_void_hits'])*25+len(r['islands']['external_new_islands'])*15+r['support_g'])
    r=rr[0];c=copy.deepcopy(next(c for c in s['candidates'] if c['name']==r['name']))
    if c.get('enforce_source'):c['enforce_sources']=c.get('enforce_sources',[])+[c['enforce_source']]
    c.update(name='dense_contact',guard_revision=5,blocker_margin_mm=2.2,shield_enforcers=True,
        enforce_source=(OUT/'bambu'/rid/r['name']/'checked_result.json').relative_to(B).as_posix())
    c.setdefault('settings',{}).update(bridge_no_support='0',support_threshold_angle='55',support_top_z_distance='0.28',support_bottom_z_distance='0.28',support_object_xy_distance='0.4',
        support_interface_spacing='0',support_bottom_interface_spacing='0',support_expansion='0.5')
    s['candidates']=[x for x in s['candidates'] if x['name']!=c['name']]+[c];put(file,s)
    print('DENSE',rid,r['name'],flush=True)
    return run(dict(id=rid,key=s['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    ids=a.ids or [p.stem for p in sorted((OUT/'candidates').glob('*.json'))]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:list(pool.map(dense,ids))
