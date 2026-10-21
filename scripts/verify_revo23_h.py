"""O23H staged verification; baseline G remains published until every gate passes."""
from revo23_endfaces import *
import verify_revo23_g as check

def configure():
    check.GROOT=HROOT;check.GREV=HREV;check.FHASH=GHASH;check.FHISTORY=GHISTORY
    check.load_g=load_h;check.raw_keep=lambda key,parts,p,N:native_keep(key);check.skin_of=clean_skin
    original=rod_body
    check.expected_sweep_cleanup=[]
    def expected_body(r):
        s=original(r)+union([socket_solid(r[k]) for k in ('source_socket','target_socket') if k in r])
        pieces=s.decompose();removed=[abs(c.volume()) for c in pieces if abs(c.volume())<=1e-8]
        if removed:check.expected_sweep_cleanup.append(dict(removed_components=len(removed),absolute_volume_mm3=sum(removed)))
        return union([c for c in pieces if abs(c.volume())>1e-8])
    check.rod_body=expected_body
    def contact(key,rod,body,M):
        mounts={rod['mount'],rod.get('target_mount')};result=body
        paths=list((HROOT/'mount_reinforcement').glob(key.replace('/','__')+'*.json'))
        for path in paths:
            if read(path)['mount'] in mounts:
                z=np.load(path.with_suffix('.npz'));result+=solid(z['v'],z['f'])
        return result
    check.connection_contact_material=contact

def stage():
    parts,p,cfg=load_h();cleanup=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        path=HROOT/(key.replace('/','__')+'.npz');record=connection_records(key)
        cc=item['s'].decompose();main=[s for s in cc if s.volume()>.001]
        debris=[s.volume() for s in cc if s.volume()<=.001]
        assert len(main)==1,(key,'disconnected material',sorted([s.volume() for s in cc],reverse=True)[:8])
        save_s(path,main[0]);record['candidate_sha256']=sha(path);record['components']=1;put(path.with_suffix('.json'),record)
        cleanup.append(dict(part=key,removed_components=len(debris),absolute_removed_volume_mm3=sum(abs(v)for v in debris)))
    put(HROOT/'zero_volume_cleanup.json',dict(rows=cleanup,maximum_absolute_removed_volume_mm3=max(r['absolute_removed_volume_mm3']for r in cleanup)))
    return check.stage()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['stage','ends','materials','loads','geometry','fixed','daily','edge'],required=True);ap.add_argument('--keys',nargs='*');a=ap.parse_args()
    configure()
    if a.mode=='stage':stage();raise SystemExit
    parts,p,cfg=load_h()
    if a.mode=='ends':audit(parts,p);raise SystemExit
    if a.mode=='materials':
        check.materials(parts,p)
        put(HROOT/'expected_sweep_cleanup.json',dict(rows=check.expected_sweep_cleanup,maximum_discarded_component_volume_mm3=1e-8,
            note='Analytic reference sweeps only: remove numerically zero-volume tetrahedra before topology tests. Actual staged parts are tested separately.'))
    elif a.mode=='loads':check.loads(parts,p,a.keys)
    elif a.mode in ('geometry','fixed'):
        import verify_revo23 as v
        v.B=HROOT
        if a.mode=='geometry':
            r=dict(revision=HREV,geometry_sha256=sha(HROOT/'assembly.npz'),kinematics=v.kinematics(p),geometry=v.geometric(parts,p),physical_tested=False,manufacturing_release=False)
            put(HROOT/'geometry.json',r);print('GEOMETRY',r['geometry']['invalid_parts'],r['geometry']['height_mm'],flush=True)
        else:
            from revo23_daily import rigid_groups
            v.cases=lambda profile,suite:{'A_STAND_35':read(HROOT/'profiles/default_pose.json')['raw_deg']}
            base,_,_=v.load_baseline();result=v.motion(parts,base,p,'fixed_reference')
            groups=rigid_groups(p,{x['token'] for x in parts.values()})
            rows=[r for case in result['rows'] for r in case['contacts'] if groups[parts[r['pair'][0]]['token']]==groups[parts[r['pair'][1]]['token']]]
            hits=[r for r in rows if r['increased']]
            put(HROOT/'fixed_interfaces.json',dict(geometry_sha256=sha(HROOT/'assembly.npz'),rows=rows,new_contacts=hits,passed=not hits));print('FIXED',not hits,hits,flush=True)
    else:
        spec=read(GHISTORY/'profiles'/('daily_poses.json' if a.mode=='daily' else 'edge_path_poses.json'))
        path=HROOT/(a.mode+'_motion.json');path.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
        r=check.check_daily(parts,p,spec['poses'],spec.get('policy',{}).get('poses',[]),sha(HROOT/'assembly.npz'),output=path)
        r.update(complete_policy=True,trial=False,profile_sha256=profile_signature(p));put(path,r);print('MOTION',r['passed'],len(r['blocking_contacts']),flush=True)
