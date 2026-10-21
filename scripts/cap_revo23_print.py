from bambu_revo23_print import *
from audit_revo23_print import read_project,manual_caps

def exact_box_offset(s,d):
    if s.is_empty():return s
    v,f=vf(s);corners=np.array([[x,y,z] for x in (-d[0],d[0]) for y in (-d[1],d[1]) for z in (-d[2],d[2])])
    # Continuous triangle sweeps, not disconnected samples of translated skins.
    # This closes the small gaps left by a finite translation approximation.
    expanded=[md.Manifold.hull_points((tri[:,None,:]+corners).reshape(-1,3)) for tri in v[f]]
    return union([s]+expanded)

def build(job):
    rid,name,requested=job
    file=OUT/'candidates'/(rid+'.json');s=read(file);rr=[read(p) for p in (OUT/'bambu'/rid).glob('*/checked_result.json')]
    if any(r['passed'] for r in rr):return
    # Keep confirmed clear holes; the caps address only detached model starts.
    eligible=[r for r in rr if r['clearance']['passed']]
    r=next(r for r in eligible if r['name']==requested) if requested else min(eligible,key=lambda r:len(r['islands']['external_new_islands'])*15+r['support_g']);c=copy.deepcopy(read((B/r['source_project']).parent/'input.json')['candidate'])
    M=np.array(c['matrix']);body=solid(*read_project(B/r['project'])[0][rid]);n=np.load(OUT/'guards_v5'/(rid+'.npz'));guard=move(solid(n['v'],n['f']),M)
    oldcaps=manual_caps(B/r['project']);caps=[] if oldcaps.is_empty() else list(oldcaps.decompose());records=[];layer=float(c.get('settings',{}).get('layer_height','.16'))
    for issue in r['islands']['external_new_islands']:
        x0,y0,x1,y1=issue['bounds_mm'];top=issue['z_mm']-layer-.24
        patch=box([x0-.65,y0-.65,top-.32],[x1+.65,y1+.65,top]);bb=np.array(patch.bounding_box());crop=box(bb[:3]-.6,bb[3:]+.6)
        expanded=exact_box_offset(body^crop,[.23,.23,.23])
        ban=exact_box_offset(guard^crop,[.35,.35,.16])
        patch=patch-expanded-ban
        good=[p for p in patch.decompose() if p.volume()>.08 and p.min_gap(body,.18)>=.179]
        caps.extend(good);records.append(dict(target=issue,patch_count=len(good),volume_mm3=sum(p.volume() for p in good)))
    assert caps,(rid,'No clear support cap locations')
    path=OUT/'candidates'/(rid+'_'+name+'.npz');v,f=vf(move(union(caps),np.linalg.inv(M)));np.savez_compressed(path,v=v,f=f)
    c.update(name=name,manual_caps=path.relative_to(B).as_posix(),guard_revision=5,shield_enforcers=True,cap_design=records)
    s=read(file);s['candidates']=[x for x in s['candidates'] if x['name']!=name]+[c];put(file,s)
    print('CAPS',rid,'from',r['name'],len(caps),flush=True)
    return run(dict(id=rid,key=s['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*',default=['O23G-S09','O23G-S10','O23G-S12','O23G-S14','O23G-S22']);ap.add_argument('--name',default='peel_caps');ap.add_argument('--source');a=ap.parse_args()
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:list(pool.map(build,[(rid,a.name,a.source) for rid in a.ids]))
