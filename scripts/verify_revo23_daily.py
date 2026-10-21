"""Check the user's revised adjacency/ordinary-motion policy on actual solids.

All moving adjacent pairs are checked in absolute volume, including inherited
hardware. A rigid attachment is not a moving interference. Nonadjacent contacts
are retained as advisory in named task poses. Nothing is hidden in the viewer.
"""
from revo23_daily import *
from present_revo23 import load_current
import itertools,time


def check_daily(parts,p,poses,definitions,digest,focus=None,output=None):
    tokens={v['token'] for v in parts.values()};groups=rigid_groups(p,tokens);edges=anatomical_edges(p)
    keys=list(parts);n=len(keys);local={}
    for k,item in parts.items():
        bb=item['s'].bounding_box();local[k]=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))))
    adjacent_matrix=np.array([[adjacent(parts[a],parts[b],p,edges) for b in keys] for a in keys])
    rigid_matrix=np.array([[groups[parts[a]['token']]==groups[parts[b]['token']] for b in keys] for a in keys])
    cache={};hits=[];warnings=[];rows=[];started=time.time()
    ordinary_tasks={r['name'] for r in definitions if r['group'] in ('basic','combined')}
    for num,(name,q) in enumerate(poses.items()):
        F=frames(p,q);inv={t:np.linalg.inv(F[t]) for t in tokens};bounds=[]
        for k in keys:
            M=F[parts[k]['token']];v=local[k]@M[:3,:3].T+M[:3,3];bounds.append(np.r_[v.min(0),v.max(0)])
        bounds=np.asarray(bounds);blocking=[];advisory=[]
        for i,k in enumerate(keys):
            mask=np.all(np.minimum(bounds[i,3:],bounds[:,3:])-np.maximum(bounds[i,:3],bounds[:,:3])>1e-5,axis=1)
            mask[:i+1]=False;mask&=~rigid_matrix[i]
            if name not in ordinary_tasks:mask&=adjacent_matrix[i]
            for j in np.flatnonzero(mask):
                other=keys[j]
                if focus and k not in focus and other not in focus:continue
                rel=inv[parts[k]['token']]@F[parts[other]['token']]
                ck=(k,other,tuple(np.round(rel,7).ravel()))
                if ck not in cache:cache[ck]=max(0.,float((parts[k]['s']^move(parts[other]['s'],rel)).volume()))
                volume=cache[ck]
                if volume<=.05:continue
                rec=dict(pair=[k,other],overlap_mm3=volume,bodies=[anatomical_body(parts[k]),anatomical_body(parts[other])])
                if adjacent_matrix[i,j]:blocking.append(rec);hits.append(dict(pose=name,**rec))
                else:advisory.append(rec);warnings.append(dict(pose=name,**rec))
        rows.append(dict(pose=name,blocking_contacts=blocking,nonadjacent_advisory=advisory))
        if output:
            with output.with_suffix('.rows.jsonl').open('a',encoding='utf8') as stream:
                stream.write(json.dumps(dict(geometry_sha256=digest,**rows[-1]),default=plain)+'\n')
        print('DAILY',num+1,'/',len(poses),name,'required',len(blocking),'advisory',len(advisory),'sec',round(time.time()-started),flush=True)
        if output:
            put(output.with_suffix('.progress.json'),dict(completed=num+1,total=len(poses),blocking=len(hits),unique_solid_checks=len(cache)))
            if num%10==0:
                put(output.with_suffix('.partial.json'),dict(geometry_sha256=digest,rows=rows,blocking_contacts=hits,nonadjacent_advisory=warnings,complete=False))
    return dict(geometry_sha256=digest,policy_id='O23D-ordinary-adjacent-v1',pose_count=len(rows),
        rows=rows,blocking_contacts=hits,nonadjacent_advisory=warnings,passed=not hits,
        blocking_pose_count=len({h['pose'] for h in hits}),advisory_pose_count=len({h['pose'] for h in warnings}),
        unique_solid_checks=len(cache),overlap_tolerance_mm3=.05,rigid_groups=groups,
        scope='All actual moving adjacent-part pairs, including inherited hardware. Fixed attachments are excluded only after five random configurations establish identical rigid motion.',
        nonadjacent_scope='Named basic and combined ordinary-use tasks; these contacts are advisory at the user request.',
        continuous_motion_proven=False,manufacturing_release=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='daily_motion.json');ap.add_argument('--only',nargs='*');ap.add_argument('--focus',nargs='*');ap.add_argument('--trial',action='store_true');ap.add_argument('--hardware-only',action='store_true');args=ap.parse_args()
    if args.trial:
        from build_revo23_continuous import DROOT,load_c,profile_signature
        parts=load_c();p=read(DROOT/'source/device_profile.json')
        hashes={}
        for key,item in parts.items():
            path=DROOT/(key.replace('/','__')+'.npz')
            if item['role']=='structure' and path.exists() and not args.hardware_only:
                report=read(path.with_suffix('.json'))
                assert report.get('validated_profile_sha256',report['construction_profile_sha256'])==profile_signature(p),('stale trial',key)
                z=np.load(path);item['s']=solid(z['v'],z['f']);hashes[key]=sha(path)
        digest=hashlib.sha256(json.dumps(dict(profile=profile_signature(p),parts=hashes,
            hardware_overrides=sha(DROOT/'source/part_overrides.npz')),sort_keys=True).encode()).hexdigest()
    else:
        digest=sha(B/'assembly.npz');parts=load_current();p=read(B/'profiles/device_profile.json')
    if args.hardware_only:parts={k:v for k,v in parts.items() if v['role']!='structure'}
    spec=read(B/'profiles/daily_poses.json');poses=spec['poses']
    if args.only:poses={k:v for k,v in poses.items() if any(k==s or k.startswith(s) for s in args.only)}
    out=B/'verification'/args.output
    out.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
    result=check_daily(parts,p,poses,spec['policy']['poses'],digest,set(args.focus) if args.focus else None,out)
    result.update(trial=args.trial,hardware_only=args.hardware_only,
                  complete_policy=not args.only and not args.focus and not args.hardware_only,
                  profile_sha256=hashlib.sha256(json.dumps(p,sort_keys=True,default=plain).encode()).hexdigest())
    put(out,result);print('DAILY RESULT',result['passed'],len(result['blocking_contacts']),flush=True)
