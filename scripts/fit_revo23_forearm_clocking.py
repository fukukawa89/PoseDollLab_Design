"""Clock a single-axis carrier without changing its axis or body kinematics."""
from build_revo23_continuous import *
from verify_revo23_daily import check_daily


def clock_profile(p,angle):
    p=copy.deepcopy(p);j=next(j for j in p['joints'] if j['id']=='forearm_r.twist')
    assert j['kind']=='hinge'
    R=np.eye(4);R[:3,:3]=kin.b.b.rot(2,angle)
    j['parent_to_mount_mm']=(np.array(j['parent_to_mount_mm'])@R).tolist()
    j['rotor_to_child_mm']=(np.linalg.inv(R)@np.array(j['rotor_to_child_mm'])).tolist()
    return p


def shift_forearms(p,distance):
    p=copy.deepcopy(p)
    for j in p['joints']:
        if j['id'] not in ('forearm_l.twist','forearm_r.twist'):continue
        Z=np.eye(4);Z[2,3]=-distance
        j['parent_to_mount_mm']=(np.array(j['parent_to_mount_mm'])@Z).tolist()
        j['rotor_to_child_mm']=(np.linalg.inv(Z)@np.array(j['rotor_to_child_mm'])).tolist()
    return p


def main():
    p=read(DROOT/'source/device_profile.json');parts=load_c()
    parts={k:v for k,v in parts.items() if v['role']!='structure'}
    focus={k for k in parts if k.startswith('forearm_r.twist/')}
    spec=read(B/'profiles/daily_poses.json')
    poses={n:q for n,q in spec['poses'].items()
           if n in ('A_STAND_35','N_NEUTRAL','left_elbow','asymmetric','right_forearm')
           or n.startswith(('elbow_r.','forearm_r.','wrist_r.','daily_'))}
    results=[]
    for angle in (180.,90.,-90.,45.,-45.):
        pp=clock_profile(p,angle);error=0.
        for q in poses.values():
            a=frames(p,q);b=frames(pp,q)
            error=max(error,max(np.max(abs(a[k]-b[k])) for k in a if k.startswith('f:')))
        assert error<1e-8,error
        result=check_daily(parts,pp,poses,spec['policy']['poses'],profile_signature(pp),focus)
        result.update(clocking_deg=angle,maximum_body_transform_error=error)
        results.append(result)
        put(B/'verification/forearm_clocking_search.json',results)
        print('CLOCK',angle,'required',len(result['blocking_contacts']),flush=True)
        if result['passed']:break


if __name__=='__main__':main()
