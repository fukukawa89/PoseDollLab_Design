"""Recheck every changed part; reuse only byte-identical canonical mesh pairs."""
from deepen_revo23_backpack import *

def mesh_digest(s):
    v,f=vf(s)
    return hashlib.sha256(v.tobytes()+f.tobytes()).hexdigest()

def tools_check(parts,p):
    config=read(B/'verification/backpack_mount.json');rows=[]
    N=frames(p,p['neutral_raw_deg'])['f:chest'];I=np.linalg.inv(N)
    for name,q in cases(p,'quick').items():
        F=frames(p,q)
        for t in config['rear_access_screws']:
            # Radius is the specified shaft diameter / 2. Start at the top
            # of the real screw head, excluding intended bit/head contact.
            local=move(move(kin.b.b.cyl(3,3.05,83.05),screw_frame(t['head_neutral_mm'])),I)
            tool=move(local,F['f:chest']);bb=np.array(tool.bounding_box());hits=[]
            for k,part in parts.items():
                s=move(part['s'],F[part['token']]);b=np.array(s.bounding_box())
                if np.any(np.minimum(bb[3:],b[3:])-np.maximum(bb[:3],b[:3])<=0):continue
                volume=float((tool^s).volume())
                if volume>.001:hits.append(dict(key=k,overlap_mm3=volume))
            rows.append(dict(pose=name,screw=t['id'],hits=hits))
    return dict(rows=rows,passed=not any(r['hits']for r in rows),scope='8 rear screw axes, diameter 6 mm, straight 80 mm shaft, five service poses; handle/grip and human hand not modeled.')

def main():
    parts=load_current();old=source_parts();p=read(B/'profiles/device_profile.json');op=read(HISTORY/'profiles/device_profile.json')
    assert p==op,'Cannot reuse motion checks after a profile change.'
    oldmotion=read(HISTORY/'verification/motion_full.json');assert oldmotion['geometry_sha256']==INPUT_HASH
    changed=set();same=[];removed=set(old)-set(parts)
    for k,x in parts.items():
        if k not in old or x['token']!=old[k]['token']or mesh_digest(x['s'])!=mesh_digest(old[k]['s']):changed.add(k)
        else:same.append(k)
    digest=sha(B/'assembly.npz')
    put(B/'verification/backpack_change_scope.json',dict(geometry_sha256=digest,input_sha256=INPUT_HASH,
        unchanged_canonical_mesh_and_owner_keys=same,changed_keys=sorted(changed),removed_keys=sorted(removed),
        profile_identical=True,unchanged_count=len(same)))
    print('CHANGED',len(changed),'IDENTICAL',len(same),'REMOVED',len(removed),flush=True)
    geo=dict(revision=REV,geometry_sha256=digest,configuration_sha256=sha(CFG),kinematics=kinematics(p),
        geometry=geometric(parts,p),physical_tested=False,manufacturing_release=False)
    put(B/'verification/geometry.json',geo)
    print('GEOMETRY',geo['geometry']['invalid_parts'],geo['geometry']['oversize_parts'],flush=True)
    base,_,_=load_baseline();checks=motion(parts,base,p,'full',changed)
    oldrows={r['pose']:r for r in oldmotion['rows']};hits=[]
    for row in checks['rows']:
        prior=[r for r in oldrows[row['pose']]['contacts'] if all(k in same for k in r['pair'])]
        row['contacts']+=prior
        hits +=[dict(pose=row['pose'],**r)for r in row['contacts']if r['increased']]
    checks.update(new_or_increased_contacts=hits,passed=not hits,
        scope='All changed parts versus every current part. Unchanged-pair results reused only after identical canonical vertex/index bytes, identical rigid owner, and identical profile checks.',
        reuse_source_sha256=INPUT_HASH,reuse_audit='backpack_change_scope.json')
    put(B/'verification/motion_full.json',checks)
    names=set(cases(p,'quick'));quick=dict(checks)
    quick.update(suite='quick',derived_from='motion_full.json',rows=[r for r in checks['rows']if r['pose']in names],
        new_or_increased_contacts=[r for r in hits if r['pose']in names],pose_count=len(names),unique_solid_checks=None)
    quick['passed']=not quick['new_or_increased_contacts'];put(B/'verification/motion_quick.json',quick)
    tool_report=tools_check(parts,p);tool_report['geometry_sha256']=digest;put(B/'verification/backpack_tool_access.json',tool_report)
    print('FINAL CONTACTS',len(hits),'QUICK',len(quick['new_or_increased_contacts']),'TOOL',tool_report['passed'],flush=True)

if __name__=='__main__':main()
