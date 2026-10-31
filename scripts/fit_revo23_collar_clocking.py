"""Try physical collar-carrier clocking while preserving every body transform."""
from build_revo23_continuous import *
from verify_revo23_daily import check_daily

def collar_clock(p,angle,right_angle=None):
    p=copy.deepcopy(p)
    for side in ('l','r'):
        j=next(j for j in p['joints'] if j['id']=='clavicle_'+side+'.protract')
        assert j['kind']=='hinge'
        C=np.eye(4);C[:3,:3]=kin.b.b.rot(2,angle if side=='l' or right_angle is None else right_angle)
        j['parent_to_mount_mm']=(np.array(j['parent_to_mount_mm'])@C).tolist()
        j['rotor_to_child_mm']=(np.linalg.inv(C)@np.array(j['rotor_to_child_mm'])).tolist()
    return p

def static_packing(p,parts):
    F=frames(p,p['neutral_raw_deg'])
    S={k:move(v['s'],F[v['token']]) for k,v in parts.items()}
    BB={k:np.array(s.bounding_box()) for k,s in S.items()}
    changed=[k for k in parts if k.startswith(('clavicle_l.protract/','clavicle_r.protract/'))]
    hits=[];seen=set()
    for a in changed:
        for b in parts:
            if a.split('/')[0]==b.split('/')[0]:continue
            pair=tuple(sorted((a,b)))
            if pair in seen:continue
            seen.add(pair)
            if np.any(np.minimum(BB[a][3:],BB[b][3:])-np.maximum(BB[a][:3],BB[b][:3])<=0):continue
            volume=max(0.,(S[a]^S[b]).volume())
            if volume>.05:hits.append(dict(pair=pair,overlap_mm3=volume))
    return hits

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--angle',type=float,default=180.)
    ap.add_argument('--right-angle',type=float);args=ap.parse_args()
    p=read(B/'profiles/device_profile.json');pp=collar_clock(p,args.angle,args.right_angle)
    parts={k:v for k,v in load_current().items() if v['role']!='structure'}
    spec=read(B/'profiles/daily_poses.json')
    poses={k:v for k,v in spec['poses'].items()
           if k.startswith(('upperarm_','clavicle_','daily_')) or k in ('A_STAND_35','N_NEUTRAL','asymmetric','left_elbow','right_forearm')}
    poses.update(read(B/'profiles/edge_path_poses.json')['poses'])
    error=0.
    for q in poses.values():
        a=frames(p,q);b=frames(pp,q)
        error=max(error,max(np.max(abs(a[k]-b[k])) for k in a if k.startswith('f:')))
    assert error<1e-8,error
    focus={k for k in parts if k.startswith(('clavicle_l.protract/','clavicle_r.protract/'))}
    label=f'{args.angle:g}_{args.right_angle:g}' if args.right_angle is not None else f'{args.angle:g}'
    out=B/'verification'/f'collar_clock_{label}.json'
    static=static_packing(pp,parts)
    if static:
        put(out,dict(clocking_deg=[args.angle,args.right_angle],static_contacts=static,passed=False))
        print('STATIC FAIL',label,len(static),flush=True);sys.exit(0)
    result=check_daily(parts,pp,poses,spec['policy']['poses'],profile_signature(pp),focus,out)
    result.update(clocking_deg=[args.angle,args.right_angle],maximum_body_transform_error=error,static_contacts=static)
    put(out,result)
    print('COLLAR CLOCK',args.angle,result['passed'],len(result['blocking_contacts']),error,flush=True)
