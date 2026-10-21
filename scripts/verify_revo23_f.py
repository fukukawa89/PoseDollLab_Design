"""Checks bound to the staged clean O23F candidate, without publishing it."""
from revo23_clean import *
from verify_revo23_daily import check_daily
from audit_revo23_load_paths import screen


def stage():
    parts,p,cfg=load_f();data=np.load(EHISTORY/'assembly.npz');out={k:data[k] for k in data.files}
    changed=[]
    for key,item in parts.items():
        path=FROOT/(key.replace('/','__')+'.npz')
        if item['role']=='structure':assert path.exists(),key
        if not path.exists():continue
        z=np.load(path);i=str(item['index']);out[i+'v']=z['v'];out[i+'f']=z['f'];changed.append(key)
    np.savez_compressed(FROOT/'assembly.npz',**out)
    put(FROOT/'assembly.json',dict(revision=FREV,items=[{k:v for k,v in r.items() if k!='s'} for r in parts.values()]))
    put(FROOT/'staging.json',dict(input_geometry_sha256=EHASH,geometry_sha256=sha(FROOT/'assembly.npz'),
        changed_parts=changed,candidate_files={k:sha(FROOT/(k.replace('/','__')+'.npz')) for k in changed}))
    return parts,p,cfg


def exterior(parts,p):
    F=frames(p,p['neutral_raw_deg']);rows=[];done=set();rodrows=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        path=FROOT/(key.replace('/','__')+'.npz')
        report=read(path.with_suffix('.json'))
        bymount={}
        for r in report['rods']:bymount[r['mount']]=bymount.get(r['mount'],0)+1
        rodrows.append(dict(key=key,rod_count=len(report['rods']),rods_by_mount=bymount,
            passed=all(n<=3 for n in bymount.values()),candidate_sha256=sha(path)))
        if key in done:continue
        skinpath=path.with_name(path.stem+'_skin.npz')
        z=np.load(skinpath);v=z['v'];m=F[item['token']]
        if not len(v):
            rows.append(dict(key=key,exterior='No decorative skin',passed=True));continue
        world=v@m[:3,:3].T+m[:3,3]
        if key.endswith(('_l','_r')):
            other=key[:-1]+('r' if key[-1]=='l' else 'l')
            op=FROOT/(other.replace('/','__')+'_skin.npz');oz=np.load(op);om=F[parts[other]['token']]
            target=oz['v']@om[:3,:3].T+om[:3,3];done.add(other)
        else:other=key;target=world
        mirrored=world*np.array([1,-1,1])
        error=max(cKDTree(target).query(mirrored)[0].max(),cKDTree(mirrored).query(target)[0].max())
        # Approved fingers have different triangulation, so compare surfaces
        # rather than just vertex locations.
        if error>=.02:
            target_mesh=trimesh.Trimesh(target,oz['f'] if other!=key else z['f'],process=False)
            source_mesh=trimesh.Trimesh(mirrored,z['f'],process=False)
            _,da,_=trimesh.proximity.closest_point(target_mesh,mirrored)
            _,db,_=trimesh.proximity.closest_point(source_mesh,target)
            error=max(da.max(),db.max())
        rows.append(dict(key=key,mirror_key=other,max_mirrored_distance_mm=error,passed=error<.02))
    report=dict(geometry_sha256=sha(FROOT/'assembly.npz'),symmetry=rows,connections=rodrows,
        passed=all(r['passed'] for r in rows+rodrows),total_rods=sum(r['rod_count'] for r in rodrows),
        scope='External anatomical skins mirror across neutral world Y=0. Functional lands retain actual hardware geometry. Each explicit nonbranching rod is assigned to its mounting land; physical-interface grouping is audited separately.')
    put(FROOT/'clean_design.json',report);print('EXTERIOR',report['passed'],'rods',report['total_rods'],flush=True)


def loads(parts,p,cfg,keys=None):
    from build_revo23_clean_connections import source_keep
    F=frames(p,p['neutral_raw_deg']);kz=np.load(EHISTORY/'source/retained_interfaces.npz')
    out=FROOT/'load_paths';out.mkdir(exist_ok=True)
    for key,item in parts.items():
        if item['role']!='structure' or keys and key not in keys:continue
        path=FROOT/(key.replace('/','__')+'.npz')
        z=np.load(path.with_name(path.stem+'_skin.npz'));skin=solid(z['v'],z['f'])
        keep=source_keep(key,kz,load_e_snapshot()[0][key],p,F) if key=='frame/chest' else solid(kz[key+'|v'],kz[key+'|f'])
        r=screen(key,item['s'],keep,skin,1.)
        r['candidate_sha256']=sha(path);put(out/(path.stem+'.json'),r)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--only',nargs='*');ap.add_argument('--edge',action='store_true')
    ap.add_argument('--stage-only',action='store_true');ap.add_argument('--loads',action='store_true')
    ap.add_argument('--exterior',action='store_true');ap.add_argument('--use-staged',action='store_true');args=ap.parse_args()
    if args.use_staged:
        st=read(FROOT/'staging.json')
        assert st['geometry_sha256']==sha(FROOT/'assembly.npz')
        for key,h in st['candidate_files'].items():
            assert sha(FROOT/(key.replace('/','__')+'.npz'))==h,('Changed candidate',key)
        parts,p,cfg=load_f()
    else:parts,p,cfg=stage()
    if args.stage_only:raise SystemExit
    if args.loads:loads(parts,p,cfg,args.only);raise SystemExit
    if args.exterior:exterior(parts,p);raise SystemExit
    spec=read(EHISTORY/'profiles'/('edge_path_poses.json' if args.edge else 'daily_poses.json'))
    poses=spec['poses']
    if args.only:poses={k:v for k,v in poses.items() if any(k==s or k.startswith(s) for s in args.only)}
    path=FROOT/('edge_motion.json' if args.edge else 'daily_motion.json')
    path.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
    result=check_daily(parts,p,poses,spec.get('policy',{}).get('poses',[]),sha(FROOT/'assembly.npz'),output=path)
    result.update(complete_policy=not args.only,trial=False,profile_sha256=profile_signature(p))
    put(path,result);print('MOTION',result['passed'],len(result['blocking_contacts']),flush=True)
