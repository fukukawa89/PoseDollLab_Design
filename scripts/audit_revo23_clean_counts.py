"""Count named rods by the adjacent physical joint module/controller case."""
from build_revo23_clean_connections import *

parts,p,cfg=load_f();base,_,_=load_e_snapshot();F=frames(p,p['neutral_raw_deg'])
kz=np.load(EHISTORY/'source/retained_interfaces.npz');rows=[]
for key,item in parts.items():
    if item['role']!='structure':continue
    path=FROOT/(key.replace('/','__')+'.npz');r=read(path.with_suffix('.json'))
    keep=source_keep(key,kz,base[key],p,F)
    lands=sorted([c for c in keep.decompose() if c.volume()>.05],key=lambda c:-c.volume())
    anchors=interface_anchors(item['body'],p,F)
    groups=[]
    for land in lands:
        v,_=vf(land);N=F[item['token']];world=v@N[:3,:3].T+N[:3,3]
        mid=(world.min(0)+world.max(0))/2
        if key=='frame/chest' and mid[0]<-38 and 510<mid[2]<555 and abs(mid[1])>25:
            group='controller_housing'
        else:
            group=min(anchors,key=lambda a:np.linalg.norm(world-np.array(a['point']),axis=1).min())['joint']
        groups.append(group)
    counts={};connections=[]
    for rod in r['rods']:
        touched={groups[rod['mount']]}
        points=np.array(rod['centerline_body_mm'])
        # Count both ends when a rod directly joins two mounting lands.
        probe=ball(points[-1],1.6)
        for li,land in enumerate(lands):
            if (probe^land).volume()>.05:touched.add(groups[li])
        if rod.get('target_mount') is not None:touched.add(groups[rod['target_mount']])
        for g in touched:counts.setdefault(g,[]).append(rod['id'])
        connections.append(dict(id=rod['id'],adjacent_components=sorted(touched)))
    rows.append(dict(part=key,rods=len(r['rods']),connections=connections,
        counts={g:len(ids) for g,ids in counts.items()},rod_ids=counts,
        passed=all(len(ids)<=3 for ids in counts.values())))
report=dict(geometry_sha256=sha(FROOT/'assembly.npz') if (FROOT/'assembly.npz').exists() else None,
    rows=rows,passed=all(r['passed'] for r in rows),
    maximum_rods_per_adjacent_component=max([n for r in rows for n in r['counts'].values()],default=0),
    physical_scope='Conservative grouping by whole adjacent joint module, plus one group for the complete controller housing. A rod touching both interface ends counts for both. Integral wire saddles fuse directly and have no supporting rods.')
put(FROOT/'physical_rod_count.json',report)
print('PHYSICAL ROD COUNT',report['passed'],report['maximum_rods_per_adjacent_component'],flush=True)
for r in rows:
    if not r['passed']:print(r,flush=True)
