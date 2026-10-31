"""Stage exact E candidates and check the complete moving assembly."""
from build_revo23_wire_seats import *
from verify_revo23_daily import check_daily
import itertools


def stage():
    parts,p,cfg=load_e();data=np.load(DHISTORY/'assembly.npz');out={k:data[k] for k in data.files};changed=[]
    for key,item in parts.items():
        path=EROOT/(key.replace('/','__')+'.npz')
        if not path.exists():continue
        z=np.load(path);i=str(item['index']);out[i+'v']=z['v'];out[i+'f']=z['f'];changed.append(key)
    np.savez_compressed(EROOT/'assembly.npz',**out)
    put(EROOT/'assembly.json',dict(revision='O23E-fingers-structure-harness-20261021',
        items=[{k:v for k,v in r.items() if k!='s'} for r in parts.values()]))
    put(EROOT/'staging.json',dict(input_geometry_sha256=DHASH,geometry_sha256=sha(EROOT/'assembly.npz'),
        changed_parts=changed,candidate_files={k:sha(EROOT/(k.replace('/','__')+'.npz')) for k in changed}))
    return parts,p,cfg


def fixed(parts,p):
    base,_,_=load_d();F=frames(p,p['neutral_raw_deg'])
    groups=rigid_groups(p,{r['token'] for r in parts.values()});rows=[];hits=[];cache={}
    for k,a in parts.items():
        if not (EROOT/(k.replace('/','__')+'.npz')).exists():continue
        for other,b in parts.items():
            if k==other or groups[a['token']]!=groups[b['token']]:continue
            pair=tuple(sorted((k,other)))
            if pair in cache:continue
            cache[pair]=True
            M=np.linalg.inv(F[a['token']])@F[b['token']];s=move(b['s'],M)
            bb=np.array(s.bounding_box());aa=np.array(a['s'].bounding_box())
            if np.any(np.minimum(bb[3:],aa[3:])-np.maximum(bb[:3],aa[:3])<=0):continue
            vol=max(0.,(a['s']^s).volume())
            if vol<.03:continue
            old=max(0.,(base[k]['s']^move(base[other]['s'],M)).volume())
            row=dict(pair=list(pair),overlap_mm3=vol,accepted_D_overlap_mm3=old,increased=vol>old+.05)
            rows.append(row)
            if row['increased']:hits.append(row)
    return dict(geometry_sha256=sha(EROOT/'assembly.npz'),passed=not hits,rows=rows,new_contacts=hits)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--only',nargs='*');ap.add_argument('--edge',action='store_true')
    ap.add_argument('--stage-only',action='store_true');args=ap.parse_args()
    parts,p,cfg=stage()
    if args.stage_only:raise SystemExit
    f=fixed(parts,p);put(EROOT/'fixed_interfaces.json',f);print('FIXED',f['passed'],f['new_contacts'],flush=True)
    spec=read(DHISTORY/'profiles'/('edge_path_poses.json' if args.edge else 'daily_poses.json'))
    poses=spec['poses']
    if args.only:poses={k:v for k,v in poses.items() if any(k==s or k.startswith(s) for s in args.only)}
    definitions=spec.get('policy',{}).get('poses',[])
    path=EROOT/('edge_motion.json' if args.edge else 'daily_motion.json')
    path.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
    result=check_daily(parts,p,poses,definitions,sha(EROOT/'assembly.npz'),output=path)
    result.update(complete_policy=not args.only,trial=False,
        profile_sha256=hashlib.sha256(json.dumps(p,sort_keys=True,default=plain).encode()).hexdigest())
    put(path,result)
    print('MOTION RESULT',result['passed'],len(result['blocking_contacts']),flush=True)
