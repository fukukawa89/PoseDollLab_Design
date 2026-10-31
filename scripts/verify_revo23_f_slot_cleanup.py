"""Recheck every pair involving the only changed part at all 522 poses.

Unchanged pair results are inherited only after exact candidate-file hashes
and the baseline assembly digest are checked. This is an explicit incremental
check, not an unqualified relabeling of an older collision report.
"""
from verify_revo23_f import *
from revo23_daily import rigid_groups,anatomical_edges,adjacent,anatomical_body
import copy,itertools,time

backup=FROOT/'before_slot_cleanup';changed={'frame/waist'}
oldstage=read(backup/'staging.json');oldhash=sha(backup/'assembly.npz')
assert oldhash==oldstage['geometry_sha256']
for key,h in oldstage['candidate_files'].items():
    if key not in changed:assert sha(FROOT/(key.replace('/','__')+'.npz'))==h
for name in ('daily_motion.json','edge_motion.json'):
    r=read(FROOT/name);assert r['passed'] and r['complete_policy'] and r['geometry_sha256']==oldhash
    shutil.copy2(FROOT/name,backup/name)
parts,p,cfg=stage();digest=sha(FROOT/'assembly.npz')
groups=rigid_groups(p,{r['token'] for r in parts.values()});edges=anatomical_edges(p)
local={k:np.array(list(itertools.product(*zip(r['s'].bounding_box()[:3],r['s'].bounding_box()[3:]))))
       for k,r in parts.items()}
cache={};checked=0;started=time.time()
for specname,reportname in [('daily_poses.json','daily_motion.json'),('edge_path_poses.json','edge_motion.json')]:
    spec=read(EHISTORY/'profiles'/specname)
    tasks={r['name'] for r in spec.get('policy',{}).get('poses',[]) if r['group'] in ('basic','combined')}
    report=read(backup/reportname)
    for i,row in enumerate(report['rows']):
        name=row['pose'];F=frames(p,spec['poses'][name]);bounds={}
        for key,item in parts.items():
            M=F[item['token']];v=local[key]@M[:3,:3].T+M[:3,3]
            bounds[key]=np.r_[v.min(0),v.max(0)]
        row['blocking_contacts']=[r for r in row['blocking_contacts'] if not changed.intersection(r['pair'])]
        row['nonadjacent_advisory']=[r for r in row['nonadjacent_advisory'] if not changed.intersection(r['pair'])]
        for key in changed:
            a=parts[key];I=np.linalg.inv(F[a['token']]);aa=bounds[key]
            for other,b in parts.items():
                if other==key or groups[a['token']]==groups[b['token']]:continue
                is_adjacent=adjacent(a,b,p,edges)
                if not is_adjacent and name not in tasks:continue
                bb=bounds[other]
                if np.any(np.minimum(aa[3:],bb[3:])-np.maximum(aa[:3],bb[:3])<=1e-5):continue
                M=I@F[b['token']];signature=(key,other,tuple(np.round(M,7).ravel()))
                if signature not in cache:
                    cache[signature]=max(0.,(a['s']^move(b['s'],M)).volume());checked+=1
                volume=cache[signature]
                if volume<=.05:continue
                rec=dict(pair=[key,other],overlap_mm3=volume,
                         bodies=[anatomical_body(a),anatomical_body(b)])
                row['blocking_contacts' if is_adjacent else 'nonadjacent_advisory'].append(rec)
        if i%50==0:print('INCREMENTAL',specname,i+1,'/',len(report['rows']),flush=True)
    report['blocking_contacts']=[dict(pose=r['pose'],**x) for r in report['rows'] for x in r['blocking_contacts']]
    report['nonadjacent_advisory']=[dict(pose=r['pose'],**x) for r in report['rows'] for x in r['nonadjacent_advisory']]
    report.update(geometry_sha256=digest,passed=not report['blocking_contacts'],
        blocking_pose_count=len({r['pose'] for r in report['blocking_contacts']}),
        advisory_pose_count=len({r['pose'] for r in report['nonadjacent_advisory']}),
        incremental_recheck=dict(base_geometry_sha256=oldhash,
            unchanged_candidate_hashes_verified=True,changed_parts=sorted(changed),
            rechecked_every_changed_part_pair_at_every_reported_pose=True,
            slot_cleanup=read(FROOT/'slot_cleanup.json'),new_unique_solid_checks=checked),
        scope='Full assembly baseline check plus exact checks of every moving pair involving the changed waist at every reported pose; other meshes are byte-identical.')
    put(FROOT/reportname,report)
    print('FINAL',reportname,report['passed'],len(report['blocking_contacts']),flush=True)
print('SECONDS',round(time.time()-started),flush=True)
