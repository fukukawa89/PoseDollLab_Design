"""Independent I checks, preserving H as the published baseline until completion."""
from revo23_unified import *
import verify_revo23_g as check
import revo23_endfaces as ends

def configure():
    check.GROOT=IROOT;check.GREV=IREV;check.FHASH=HHASH;check.FHISTORY=IHISTORY
    check.load_g=load_i;check.raw_keep=lambda key,parts,p,N:native_keep(key);check.skin_of=clean_skin
    original=rod_body
    def expected(r):
        s=original(r)+union([socket_solid(r[k])for k in ('source_socket','target_socket')if k in r])
        return union([c for c in s.decompose()if abs(c.volume())>1e-8])
    check.rod_body=expected
    def contact(key,rod,body,M):
        mounts={rod['mount'],rod.get('target_mount')};out=body
        for path in (IROOT/'mount_reinforcement').glob(key.replace('/','__')+'*.json'):
            if read(path).get('mount')in mounts:
                z=np.load(path.with_suffix('.npz'));out+=solid(z['v'],z['f'])
        return out
    check.connection_contact_material=contact

def preservation(parts):
    rows=[]
    for key,x in parts.items():
        if x['role']!='structure':continue
        old=h_part(key);new=x['s'];delta=new-old
        missing=max(0.,(old-new).volume());void_hit=max(0.,(delta^functional_voids(key)).volume())
        rows.append(dict(part=key,removed_H_material_mm3=missing,added_mm3=max(0.,delta.volume()),original_functional_void_intrusion_mm3=void_hit,passed=missing<.03 and void_hit<.03))
        print('PRESERVATION PART',key,rows[-1]['passed'],round(missing,6),round(void_hit,6),flush=True)
    out=dict(revision=IREV,geometry_sha256=sha(IROOT/'assembly.npz'),baseline_geometry_sha256=HHASH,rows=rows,passed=all(r['passed']for r in rows),scope='H material and all frozen H/G wire and small-aperture voids; large service openings verified separately.')
    put(IROOT/'functional_voids.json',out);print('PRESERVATION',out['passed'],sum(r['added_mm3']for r in rows),flush=True)

def end_faces(parts,p,label='candidate'):
    ends.HROOT=IROOT;ends.HREV=IREV;ends.GHASH=HHASH
    ends.connection_records=i_records
    return ends.audit(parts,p,label)

def contours(parts,p):
    N=frames(p,p['neutral_raw_deg']);rows=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        path=IROOT/'contour_guards'/(key.replace('/','__')+'.npz');z=np.load(path);guard=solid(z['v'],z['f']);delta=item['s']-h_part(key)
        residual=max(0.,(delta^guard).volume());r=dict(part=key,guard_sha256=sha(path),remaining_beyond_approved_wall_mm3=residual,passed=residual<.03)
        if key.startswith('frame/hand_'):
            A=np.array(next(x for x in read(FROOT/'skins.json')['skins']if x['key']==key)['canonical_frame_mm'])
            region=move(box([-150,-150,-150],[150,150,-21.501]),np.linalg.inv(N[item['token']])@A)
            r['added_material_in_finger_region_mm3']=max(0.,(delta^region).volume());r['passed']&=r['added_material_in_finger_region_mm3']<.03
        rows.append(r);print('FINAL CONTOUR',key,r['passed'],flush=True)
    put(IROOT/'external_contours.json',dict(geometry_sha256=sha(IROOT/'assembly.npz'),rows=rows,passed=all(r['passed']for r in rows)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['stage','ends','materials','loads','geometry','fixed','daily','edge','voids','contours']);ap.add_argument('--keys',nargs='*');ap.add_argument('--inherit');a=ap.parse_args();configure()
    if a.mode=='stage':stage_i();raise SystemExit
    parts,p,cfg=load_i()
    if a.mode=='ends':end_faces(parts,p)
    elif a.mode=='voids':preservation(parts)
    elif a.mode=='contours':contours(parts,p)
    elif a.mode=='materials':check.materials(parts,p)
    elif a.mode=='loads':check.loads(parts,p,a.keys)
    elif a.mode in ('geometry','fixed'):
        import verify_revo23 as v
        v.B=IROOT
        if a.mode=='geometry':
            r=dict(revision=IREV,geometry_sha256=sha(IROOT/'assembly.npz'),kinematics=v.kinematics(p),geometry=v.geometric(parts,p),physical_tested=False,manufacturing_release=False)
            put(IROOT/'geometry.json',r);print('GEOMETRY',r['geometry']['invalid_parts'],r['geometry']['height_mm'],flush=True)
        else:
            from revo23_daily import rigid_groups
            v.cases=lambda profile,suite:{'A_STAND_35':read(IROOT/'profiles/default_pose.json')['raw_deg']}
            base,_,_=v.load_baseline();result=v.motion(parts,base,p,'fixed_reference');groups=rigid_groups(p,{x['token']for x in parts.values()})
            rows=[r for case in result['rows']for r in case['contacts']if groups[parts[r['pair'][0]]['token']]==groups[parts[r['pair'][1]]['token']]]
            hits=[r for r in rows if r['increased']]
            put(IROOT/'fixed_interfaces.json',dict(geometry_sha256=sha(IROOT/'assembly.npz'),rows=rows,new_contacts=hits,passed=not hits));print('FIXED',not hits,hits,flush=True)
    else:
        spec=read(IHISTORY/'profiles'/('daily_poses.json'if a.mode=='daily'else 'edge_path_poses.json'))
        path=IROOT/(a.mode+'_motion.json');path.with_suffix('.rows.jsonl').write_text('',encoding='utf8')
        inherited=None
        if a.inherit:
            assert a.keys
            baseline=IROOT/a.inherit;old=read(baseline/(a.mode+'_motion.json'));before=read(baseline/'staging.json');current=read(IROOT/'staging.json')
            assert old['passed']and old['geometry_sha256']==sha(baseline/'assembly.npz')
            assert all(current['candidate_files'][k]==h for k,h in before['candidate_files'].items()if k not in a.keys)
            assert old['profile_sha256']==profile_signature(p)
            inherited=dict(report_sha256=sha(baseline/(a.mode+'_motion.json')),geometry_sha256=old['geometry_sha256'],focus_parts=a.keys,scope='Every pair involving the changed chest is rechecked at every pose; other pairs inherit byte-identical parts and identical kinematics from the frozen passing assembly.')
        r=check.check_daily(parts,p,spec['poses'],spec.get('policy',{}).get('poses',[]),sha(IROOT/'assembly.npz'),focus=set(a.keys)if a.inherit else None,output=path)
        if inherited:r['unchanged_pairs_proof']=inherited
        r.update(complete_policy=True,trial=False,profile_sha256=profile_signature(p));put(path,r);print('MOTION',r['passed'],len(r['blocking_contacts']),flush=True)
